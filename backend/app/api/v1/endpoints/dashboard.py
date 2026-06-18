"""
Dashboard 엔드포인트

권한 모델: 인증된 사용자만 (조직 전체 보안 통계는 외부 공개 금지)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.user import User
from app.services import dashboard as dashboard_service

router = APIRouter()


@router.get("/overview")
async def overview(
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """메인 대시보드 요약."""
    return await dashboard_service.overview(db)
