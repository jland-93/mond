"""
MCP HTTP — health endpoint invariant.

마운트 자체는 외부 mcp 패키지 의존(현재 mcp 1.28의 streamable_http_app)이라
통합 테스트가 까다롭다. 여기선 비활성화 + 활성화 두 상태에서 health JSON
스키마가 안정적인지만 확인한다.
"""

import importlib
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings


@contextmanager
def _reload_app():
    """main.py를 다시 import해 새로운 settings로 app을 재구성."""
    import main as main_module

    importlib.reload(main_module)
    try:
        yield main_module.app
    finally:
        # 다음 테스트가 깨지지 않도록 기본 상태로 복귀
        importlib.reload(main_module)


@pytest.mark.asyncio
async def test_mcp_health_when_disabled(monkeypatch):
    """기본 상태: 토글 off → mounted=false, auth_required=false, url=null."""
    monkeypatch.setattr(settings, "MCP_HTTP_ENABLED", False)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", None)
    with _reload_app() as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get("/api/v1/integrations/mcp/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "enabled": False,
        "mounted": False,
        "transport": None,
        "auth_required": False,
        "reason": None,
        "url": None,
    }


@pytest.mark.asyncio
async def test_mcp_health_when_enabled_with_token(monkeypatch):
    """토글 on + 토큰: mounted=true, transport 결정, auth_required=true, url=/mcp."""
    monkeypatch.setattr(settings, "MCP_HTTP_ENABLED", True)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", "tok-xyz")
    with _reload_app() as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get("/api/v1/integrations/mcp/health")
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is True
    assert body["mounted"] is True
    assert body["auth_required"] is True
    assert body["url"] == "/mcp"
    assert body["transport"] in {"streamable_http_app", "sse_app"}


@pytest.mark.asyncio
async def test_mcp_anonymous_when_no_token(monkeypatch, caplog):
    """토글 on + 토큰 비어있음: mounted=true지만 auth_required=false, 경고 로그."""
    monkeypatch.setattr(settings, "MCP_HTTP_ENABLED", True)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", None)
    with _reload_app() as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get("/api/v1/integrations/mcp/health")
    body = r.json()
    assert body["mounted"] is True
    assert body["auth_required"] is False


@pytest.mark.asyncio
async def test_mcp_mount_failure_records_reason(monkeypatch):
    """mcp_server import가 깨졌을 때 reason이 노출되고 backend는 정상 부팅."""
    monkeypatch.setattr(settings, "MCP_HTTP_ENABLED", True)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", "tok")

    import sys
    # mcp_server 모듈을 의도적으로 잘못된 객체로 교체해 mount 실패 유도.
    bad = type("X", (), {})()
    with patch.dict(sys.modules, {"mcp_server": bad}):
        with _reload_app() as app:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
                r = await c.get("/api/v1/integrations/mcp/health")
    body = r.json()
    assert body["enabled"] is True
    assert body["mounted"] is False
    assert body["reason"] is not None  # 사유가 노출됨
