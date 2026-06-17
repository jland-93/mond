"""
🌙 Dashboard 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import dashboard as dashboard_service

router = APIRouter()


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)) -> dict:
    """메인 대시보드 요약."""
    return await dashboard_service.overview(db)
