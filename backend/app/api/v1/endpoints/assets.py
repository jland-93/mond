"""
Asset 엔드포인트

권한 모델:
  - GET (조회)   : 모든 인증된 사용자 (VIEWER 이상)
  - POST/PATCH   : EMPLOYEE 이상 — 직원이 직접 자산 등록·갱신
  - DELETE       : REVIEWER 이상 — 자산 삭제는 보안 담당자
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.user import Role, User
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate
from app.schemas.common import Page
from app.services import asset as asset_service

router = APIRouter()


@router.get("", response_model=Page[AssetRead])
async def list_assets(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    asset_type: str | None = Query(None),
    q: str | None = Query(None, description="이름/URI 부분일치 검색"),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[AssetRead]:
    items, total = await asset_service.list_assets(
        db, limit=limit, offset=offset, asset_type=asset_type, q=q
    )
    return Page(items=[AssetRead.model_validate(i) for i in items], total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.EMPLOYEE))],
)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    asset = await asset_service.create_asset(db, payload)
    return AssetRead.model_validate(asset)


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(
    asset_id: int,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetRead.model_validate(asset)


@router.patch(
    "/{asset_id}",
    response_model=AssetRead,
    dependencies=[Depends(require_role(Role.EMPLOYEE))],
)
async def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    updated = await asset_service.update_asset(db, asset, payload)
    return AssetRead.model_validate(updated)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
async def delete_asset(asset_id: int, db: AsyncSession = Depends(get_db)) -> None:
    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await asset_service.delete_asset(db, asset)
