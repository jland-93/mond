"""GitHub org → Asset 자동 동기화 — Admin 전용."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.config import settings
from app.core.database import get_db
from app.models.user import Role
from app.services import github_sync

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


@router.get("/status")
async def status() -> dict:
    return github_sync.status_payload()


@router.post("/run")
async def run(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    org = (payload.get("org") or settings.GITHUB_ORG or "").strip()
    if not org:
        raise HTTPException(status_code=400, detail="org 이름이 필요합니다")

    dry_run = bool(payload.get("dry_run", False))
    include_archived = bool(payload.get("include_archived", False))

    result = await github_sync.sync_org(
        db,
        org,
        token=settings.GITHUB_TOKEN,
        dry_run=dry_run,
        include_archived=include_archived,
    )
    if result.get("error"):
        # 인증/404 등은 사용자에게 그대로 노출 — secret 마스킹은 service에서 끝남
        raise HTTPException(status_code=400, detail=result["error"])
    result["dry_run"] = dry_run
    result["org"] = org
    return result
