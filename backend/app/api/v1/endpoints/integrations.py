"""
🌙 Integrations 엔드포인트 — 사용 가능한 스캐너 어댑터 + AI 활성 상태
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import current_model_label, get_provider, is_enabled
from app.core.database import get_db
from app.scanners.registry import list_scanners

router = APIRouter()


@router.get("/scanners")
async def list_scanner_integrations() -> dict:
    return {"scanners": list_scanners()}


@router.get("/ai")
async def ai_integration_status(db: AsyncSession = Depends(get_db)) -> dict:
    return {
        "enabled": await is_enabled(db),
        "provider": await get_provider(db),
        "model": await current_model_label(db),
    }
