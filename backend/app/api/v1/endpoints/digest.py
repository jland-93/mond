"""Daily Digest endpoint — 미리보기(Reviewer)와 발송(Admin) 두 개."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.models.user import Role
from app.services import digest as digest_service

router = APIRouter()


@router.get("/preview", dependencies=[Depends(require_role(Role.REVIEWER))])
async def preview(db: AsyncSession = Depends(get_db)) -> dict:
    d = await digest_service.build_daily_digest(db)
    return {"digest": d, "slack_message": digest_service.format_slack_message(d)}


@router.post("/send", dependencies=[Depends(require_role(Role.ADMIN))])
async def send(db: AsyncSession = Depends(get_db)) -> dict:
    return await digest_service.send_daily_digest(db)
