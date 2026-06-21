"""
Workspace 서비스 — CRUD + slug 유효성 + default 회수.

v0.3 MVP는 단일 모델(Workspace) CRUD만. Asset 등 자원의 workspace_id 필터링은
호출부에서 직접 처리.
"""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace

_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")


def is_valid_slug(slug: str) -> bool:
    """소문자 + 숫자 + 하이픈, 시작/끝은 영숫자, 1~64자."""
    return bool(_SLUG_PATTERN.match(slug or ""))


async def list_workspaces(db: AsyncSession) -> list[Workspace]:
    return list((await db.execute(select(Workspace).order_by(Workspace.id))).scalars().all())


async def get_by_slug(db: AsyncSession, slug: str) -> Workspace | None:
    return (await db.execute(select(Workspace).where(Workspace.slug == slug))).scalar_one_or_none()


async def get_by_id(db: AsyncSession, ws_id: int) -> Workspace | None:
    return (await db.execute(select(Workspace).where(Workspace.id == ws_id))).scalar_one_or_none()


async def get_default(db: AsyncSession) -> Workspace | None:
    row = (
        await db.execute(select(Workspace).where(Workspace.is_default.is_(True)).limit(1))
    ).scalar_one_or_none()
    if row:
        return row
    # default 표식이 없으면 가장 오래된 workspace를 default로 간주
    return (
        await db.execute(select(Workspace).order_by(Workspace.id).limit(1))
    ).scalar_one_or_none()


async def create(db: AsyncSession, *, slug: str, name: str, description: str | None) -> Workspace:
    ws = Workspace(slug=slug, name=name, description=description, is_default=False)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ws


async def update(
    db: AsyncSession, *, ws_id: int, name: str | None, description: str | None
) -> Workspace | None:
    ws = await get_by_id(db, ws_id)
    if ws is None:
        return None
    if name is not None:
        ws.name = name
    if description is not None:
        ws.description = description
    await db.commit()
    await db.refresh(ws)
    return ws


async def delete(db: AsyncSession, *, ws_id: int) -> tuple[bool, str | None]:
    """삭제. default workspace는 삭제 불가. 마지막 1건도 삭제 불가."""
    ws = await get_by_id(db, ws_id)
    if ws is None:
        return False, "workspace_not_found"
    if ws.is_default:
        return False, "cannot_delete_default"
    total = (await db.execute(select(func.count(Workspace.id)))).scalar_one()
    if int(total or 0) <= 1:
        return False, "cannot_delete_last"
    await db.delete(ws)
    await db.commit()
    return True, None


async def set_default(db: AsyncSession, *, ws_id: int) -> Workspace | None:
    """대상을 default로, 나머지는 false로 일괄 토글."""
    target = await get_by_id(db, ws_id)
    if target is None:
        return None
    for ws in await list_workspaces(db):
        ws.is_default = ws.id == ws_id
    await db.commit()
    await db.refresh(target)
    return target
