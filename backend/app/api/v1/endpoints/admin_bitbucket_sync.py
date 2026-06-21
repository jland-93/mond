"""Bitbucket workspace → Asset 자동 동기화 — Admin 전용."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.models.user import Role
from app.services import bitbucket_sync

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


@router.get("/status")
async def status() -> dict:
    return bitbucket_sync.status_payload()


@router.post("/run", dependencies=[Depends(RateLimiter("bitbucket_sync", 5, 60, "user"))])
async def run(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    workspace = (payload.get("workspace") or settings.BITBUCKET_WORKSPACE or "").strip()
    if not workspace:
        raise HTTPException(status_code=400, detail="workspace 이름이 필요합니다")

    dry_run = bool(payload.get("dry_run", False))

    result = await bitbucket_sync.sync_workspace(
        db,
        workspace,
        username=settings.BITBUCKET_USERNAME,
        app_password=settings.BITBUCKET_APP_PASSWORD,
        dry_run=dry_run,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    result["dry_run"] = dry_run
    result["workspace"] = workspace
    return result
