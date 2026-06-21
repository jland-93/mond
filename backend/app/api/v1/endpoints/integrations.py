"""
Integrations 엔드포인트 — 사용 가능한 스캐너 어댑터 + AI 활성 상태 + MCP HTTP 상태
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import current_model_label, get_provider, is_enabled
from app.core.config import settings
from app.core.database import get_db
from app.scanners.registry import list_scanners
from app.services import opa as opa_service

router = APIRouter()


@router.get("/scanners")
async def list_scanner_integrations() -> dict:
    return {"scanners": list_scanners()}


@router.get("/opa")
async def opa_integration_status() -> dict:
    return {
        "available": opa_service.is_available(),
        "binary": opa_service.opa_binary(),
    }


@router.get("/ai")
async def ai_integration_status(db: AsyncSession = Depends(get_db)) -> dict:
    return {
        "enabled": await is_enabled(db),
        "provider": await get_provider(db),
        "model": await current_model_label(db),
    }


@router.get("/mcp/health")
async def mcp_health(request: Request) -> dict:
    """MCP HTTP 마운트 상태 — Claude Desktop/Code 설정 검증용. 인증 불필요.

    응답 필드:
      enabled       — MCP_HTTP_ENABLED 토글
      mounted       — 실제로 /mcp 경로에 sub-app이 붙었는지
      transport     — 'streamable_http_app' / 'sse_app' / null
      auth_required — Bearer 토큰 보호 여부 (운영에선 true 권장)
      reason        — 마운트 실패 시 사유 (성공 시 null)
      url           — 외부 클라이언트가 접속할 경로 (mounted=false면 null)
    """
    state = getattr(request.app.state, "mcp", {})
    return {
        "enabled": bool(state.get("enabled", settings.MCP_HTTP_ENABLED)),
        "mounted": bool(state.get("mounted")),
        "transport": state.get("transport"),
        "auth_required": bool(state.get("auth_required", bool(settings.MCP_HTTP_AUTH_TOKEN))),
        "reason": state.get("reason"),
        "url": "/mcp" if state.get("mounted") else None,
    }
