"""
'내 페이지' 엔드포인트 — 본인 자산 / 자기 발견사항 / 권한 요청 / 만료 임박 집계.

권한: 인증된 사용자만. 본인 데이터만 노출 (다른 사용자 데이터 leak 금지).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.user import User
from app.services import me as me_service

router = APIRouter()


@router.get("/overview")
async def overview(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """본인 화면에 쓰일 데이터 묶음."""
    return await me_service.get_me_overview(db, user)
