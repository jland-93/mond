"""
🌙 Integrations 엔드포인트 — 사용 가능한 스캐너 어댑터 목록
"""

from fastapi import APIRouter

from app.ai.client import is_enabled as ai_enabled
from app.scanners.registry import list_scanners

router = APIRouter()


@router.get("/scanners")
async def list_scanner_integrations() -> dict:
    return {"scanners": list_scanners()}


@router.get("/ai")
async def ai_integration_status() -> dict:
    return {
        "enabled": ai_enabled(),
        "model_default": "claude-haiku-4-5-20251001",
        "model_deep": "claude-sonnet-4-6",
    }
