"""
Asset 서비스
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus
from app.schemas.asset import AssetCreate, AssetUpdate


async def list_assets(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    asset_type: str | None = None,
    q: str | None = None,
) -> tuple[list[Asset], int]:
    stmt = select(Asset)
    count_stmt = select(func.count(Asset.id))

    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type)
        count_stmt = count_stmt.where(Asset.asset_type == asset_type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Asset.name.ilike(like) | Asset.uri.ilike(like))
        count_stmt = count_stmt.where(Asset.name.ilike(like) | Asset.uri.ilike(like))

    total = (await db.execute(count_stmt)).scalar_one()
    items = (await db.execute(stmt.order_by(Asset.id.desc()).limit(limit).offset(offset))).scalars().all()
    return list(items), int(total)


async def get_asset(db: AsyncSession, asset_id: int) -> Asset | None:
    return (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()


async def create_asset(db: AsyncSession, payload: AssetCreate) -> Asset:
    asset = Asset(**payload.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def update_asset(db: AsyncSession, asset: Asset, payload: AssetUpdate) -> Asset:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, asset: Asset) -> None:
    await db.delete(asset)
    await db.commit()


async def refresh_open_findings_count(db: AsyncSession, asset_id: int) -> None:
    """자산의 open_findings_count 캐시 갱신 (status가 NEW/TRIAGED/IN_PROGRESS인 것만 집계)."""
    stmt = (
        select(func.count(Finding.id))
        .where(Finding.asset_id == asset_id)
        .where(
            Finding.status.in_(
                [FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]
            )
        )
    )
    count = (await db.execute(stmt)).scalar_one()
    asset = await get_asset(db, asset_id)
    if asset:
        asset.open_findings_count = int(count)
        await db.commit()
