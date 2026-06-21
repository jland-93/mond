"""GitLab group → Asset 자동 동기화 — Admin 전용."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.models.user import Role
from app.services import gitlab_sync

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


@router.get("/status")
async def status() -> dict:
    return gitlab_sync.status_payload()


@router.post("/run", dependencies=[Depends(RateLimiter("gitlab_sync", 5, 60, "user"))])
async def run(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    group = (payload.get("group") or settings.GITLAB_GROUP or "").strip()
    if not group:
        raise HTTPException(status_code=400, detail="group 이름이 필요합니다")

    dry_run = bool(payload.get("dry_run", False))
    include_archived = bool(payload.get("include_archived", False))

    result = await gitlab_sync.sync_group(
        db,
        group,
        token=settings.GITLAB_TOKEN,
        dry_run=dry_run,
        include_archived=include_archived,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    result["dry_run"] = dry_run
    result["group"] = group
    return result
