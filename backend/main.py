"""
🌙 Mond — AI-Powered Open-Source DevSecOps Platform

FastAPI 엔트리포인트.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.logging import configure_logging, get_logger
from app.db_seed import seed_if_empty
from app.models import Base

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("mond_startup", version=settings.VERSION, env=settings.ENVIRONMENT)

    # 개발/데모 편의: 스키마 자동 생성. 운영은 alembic을 권장.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.SEED_ON_STARTUP:
        async with AsyncSessionLocal() as session:
            await seed_if_empty(session)

    yield
    logger.info("mond_shutdown")


app = FastAPI(
    title="Mond API",
    description="🌙 AI-Powered Open-Source DevSecOps Platform",
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


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }
