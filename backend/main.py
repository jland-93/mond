"""
Mond — AI-Powered Self-Service DevSecOps Platform

FastAPI 엔트리포인트.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.api import api_router
from app.auth import oidc
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.logging import configure_logging, get_logger
from app.db_seed import seed_if_empty
from app.models import Base
from app.services.iam import expiry_sweep_loop

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("mond_startup", version=settings.VERSION, env=settings.ENVIRONMENT)

    # 개발/데모 편의: 스키마 자동 생성. 운영은 alembic을 권장.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 기존 access_requests 테이블에 신규 컬럼이 없으면 추가 (alembic 대체)
        for ddl in (
            "ALTER TABLE access_requests ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE access_requests ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE access_requests ADD COLUMN IF NOT EXISTS revoke_result JSON DEFAULT '{}'::json NOT NULL",
            "ALTER TABLE policies ADD COLUMN IF NOT EXISTS engine VARCHAR(16) DEFAULT 'builtin' NOT NULL",
            "ALTER TABLE scans ADD COLUMN IF NOT EXISTS router_decision JSON",
        ):
            await conn.execute(text(ddl))

    if settings.SEED_ON_STARTUP:
        async with AsyncSessionLocal() as session:
            await seed_if_empty(session)

    # 만료 자동 회수 백그라운드 sweep (5분 주기)
    sweep_task = asyncio.create_task(expiry_sweep_loop(interval_seconds=300))

    try:
        yield
    finally:
        sweep_task.cancel()
        logger.info("mond_shutdown")


app = FastAPI(
    title="Mond API",
    description="AI-Powered Self-Service DevSecOps Platform",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Authlib OIDC가 state/nonce 보관에 starlette session을 사용한다.
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, same_site="lax")

# OIDC provider 등록 (settings.SSO_PROVIDERS + ENV 기준)
oidc.init_providers()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# MCP HTTP 마운트 — 원격 클라이언트용. stdio 모드는 mcp_server.py로 별도 진입.
# Streamable HTTP(MCP 신규 표준) > SSE 순으로 시도, 둘 다 실패해도 backend 정상 부팅.
# 상태는 app.state.mcp에 저장 — /integrations/mcp/health가 노출한다.
app.state.mcp = {
    "enabled": settings.MCP_HTTP_ENABLED,
    "mounted": False,
    "transport": None,
    "reason": None,
    "auth_required": bool(settings.MCP_HTTP_AUTH_TOKEN),
}

if settings.MCP_HTTP_ENABLED:
    try:
        from mcp_server import mcp as mond_mcp
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse

        class _BearerAuthMiddleware(BaseHTTPMiddleware):
            """/mcp 진입 전 Bearer 토큰 검증. 토큰 미설정이면 anonymous OK (개발 편의)."""

            def __init__(self, app, token: str | None):
                super().__init__(app)
                self.token = token

            async def dispatch(self, request, call_next):
                if self.token is None:
                    return await call_next(request)
                auth = request.headers.get("authorization", "")
                if not auth.lower().startswith("bearer "):
                    return JSONResponse(
                        {"error": "mcp_auth_required", "detail": "Bearer token required"},
                        status_code=401,
                    )
                supplied = auth.split(" ", 1)[1].strip()
                if supplied != self.token:
                    return JSONResponse(
                        {"error": "mcp_auth_invalid", "detail": "Bearer token mismatch"},
                        status_code=403,
                    )
                return await call_next(request)

        mcp_app = None
        chosen_transport: str | None = None
        last_error: str | None = None
        for attr in ("streamable_http_app", "sse_app"):
            factory = getattr(mond_mcp, attr, None)
            if factory is None:
                continue
            try:
                mcp_app = factory()
                chosen_transport = attr
                logger.info("mcp_transport_resolved", transport=attr)
                break
            except Exception as exc:
                last_error = f"{attr}: {exc}"
                logger.warning("mcp_transport_failed", transport=attr, error=str(exc))

        if mcp_app is not None:
            # mcp_app 자체에 Bearer middleware를 두른다 — mount된 sub-app은
            # 부모 FastAPI middleware 체인을 안 거쳐 별도로 보호 필요.
            mcp_app.add_middleware(_BearerAuthMiddleware, token=settings.MCP_HTTP_AUTH_TOKEN)
            app.mount("/mcp", mcp_app)
            app.state.mcp.update({"mounted": True, "transport": chosen_transport})
            logger.info(
                "mcp_mounted",
                path="/mcp",
                transport=chosen_transport,
                auth=bool(settings.MCP_HTTP_AUTH_TOKEN),
            )
            if not settings.MCP_HTTP_AUTH_TOKEN:
                logger.warning(
                    "mcp_anonymous_access",
                    detail="MCP_HTTP_AUTH_TOKEN is empty — /mcp is anonymous; set a token in production",
                )
        else:
            reason = last_error or "no compatible transport"
            app.state.mcp["reason"] = reason
            logger.warning("mcp_mount_skipped", reason=reason)
    except Exception as exc:
        app.state.mcp["reason"] = str(exc)
        logger.warning("mcp_mount_failed", error=str(exc))


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
        "mcp": "/mcp" if app.state.mcp.get("mounted") else None,
    }
