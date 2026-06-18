"""
헬스체크 / 메타 정보
"""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.ai.client import is_enabled as ai_enabled
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """헬스체크. DB 연결까지 확인한다."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    ai_ok = await ai_enabled(db) if db_ok else False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "ai_enabled": ai_ok,
    }
