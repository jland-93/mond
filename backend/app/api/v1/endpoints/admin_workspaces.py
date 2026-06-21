"""
Workspace CRUD — Admin 전용.

v0.3 MVP: 모든 자원의 workspace 분리가 아니라 *워크스페이스 카탈로그 + Asset
연결* 만 다룬다. Policy/Finding/IAM 등 나머지 자원은 v0.4 후속.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.models.user import Role
from app.services import workspace as workspace_service

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


class WorkspaceRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    is_default: bool


class WorkspaceCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=512)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=512)


def _to_read(ws) -> WorkspaceRead:
    return WorkspaceRead(
        id=ws.id, slug=ws.slug, name=ws.name, description=ws.description, is_default=ws.is_default
    )


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    return [_to_read(ws) for ws in await workspace_service.list_workspaces(db)]


@router.post("", response_model=WorkspaceRead, status_code=201)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    slug = payload.slug.strip().lower()
    if not workspace_service.is_valid_slug(slug):
        raise HTTPException(400, "slug must be lowercase alphanumeric + hyphen, 1-64 chars")
    if await workspace_service.get_by_slug(db, slug):
        raise HTTPException(409, "slug already exists")
    ws = await workspace_service.create(db, slug=slug, name=payload.name.strip(), description=payload.description)
    return _to_read(ws)


@router.patch("/{ws_id}", response_model=WorkspaceRead)
async def update_workspace(ws_id: int, payload: WorkspaceUpdate, db: AsyncSession = Depends(get_db)):
    ws = await workspace_service.update(db, ws_id=ws_id, name=payload.name, description=payload.description)
    if ws is None:
        raise HTTPException(404, "workspace not found")
    return _to_read(ws)


@router.post("/{ws_id}/default", response_model=WorkspaceRead)
async def set_default(ws_id: int, db: AsyncSession = Depends(get_db)):
    ws = await workspace_service.set_default(db, ws_id=ws_id)
    if ws is None:
        raise HTTPException(404, "workspace not found")
    return _to_read(ws)


@router.delete("/{ws_id}", status_code=204)
async def delete_workspace(ws_id: int, db: AsyncSession = Depends(get_db)):
    ok, reason = await workspace_service.delete(db, ws_id=ws_id)
    if not ok:
        if reason == "workspace_not_found":
            raise HTTPException(404, "workspace not found")
        raise HTTPException(400, reason)
    return None
