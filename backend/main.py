"""
🌙 Mond — AI-Powered Self-Service DevSecOps Platform

FastAPI 엔트리포인트.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.api import api_router
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
    description="🌙 AI-Powered Self-Service DevSecOps Platform",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# MCP HTTP/SSE 마운트 — 원격 협업용. stdio 모드는 mcp_server.py로 별도 진입.
# import는 lazy: mcp 패키지가 없거나 호환되지 않아도 backend는 정상 부팅.
if settings.MCP_HTTP_ENABLED:
    try:
        from mcp_server import mcp as mond_mcp

        app.mount("/mcp", mond_mcp.sse_app())
        logger.info("mcp_mounted", path="/mcp")
    except Exception as exc:
        logger.warning("mcp_mount_failed", error=str(exc))


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
        "mcp": "/mcp" if settings.MCP_HTTP_ENABLED else None,
    }
