"""
조직 Slack 채널 — DB CRUD + purpose별 webhook URL 조회.

알림 발송 시 라우팅:
  resolve_webhook(purpose) → DB의 해당 purpose · enabled 채널 → DEFAULT 채널 → ENV fallback.
"""

from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.slack import SlackChannel, SlackPurpose

logger = get_logger(__name__)


async def list_channels(db: AsyncSession) -> list[SlackChannel]:
    rows = await db.execute(select(SlackChannel).order_by(SlackChannel.purpose))
    return list(rows.scalars().all())


async def get_channel(db: AsyncSession, purpose: SlackPurpose) -> SlackChannel | None:
    row = await db.execute(
        select(SlackChannel).where(SlackChannel.purpose == purpose, SlackChannel.enabled.is_(True))
    )
    return row.scalar_one_or_none()


async def upsert_channel(
    db: AsyncSession,
    purpose: SlackPurpose,
    webhook_url: str,
    label: str | None,
    enabled: bool,
) -> SlackChannel:
    row = await db.execute(select(SlackChannel).where(SlackChannel.purpose == purpose))
    existing = row.scalar_one_or_none()
    if existing is None:
        ch = SlackChannel(purpose=purpose, webhook_url=webhook_url, label=label, enabled=enabled)
        db.add(ch)
    else:
        existing.webhook_url = webhook_url
        existing.label = label
        existing.enabled = enabled
        ch = existing
    await db.commit()
    await db.refresh(ch)
    return ch


async def delete_channel(db: AsyncSession, purpose: SlackPurpose) -> bool:
    row = await db.execute(select(SlackChannel).where(SlackChannel.purpose == purpose))
    existing = row.scalar_one_or_none()
    if existing is None:
        return False
    await db.delete(existing)
    await db.commit()
    return True


async def resolve_webhook(db: AsyncSession, purpose: SlackPurpose) -> str | None:
    """purpose → 해당 채널 → DEFAULT 채널 → ENV fallback."""
    direct = await get_channel(db, purpose)
    if direct:
        return direct.webhook_url
    default = await get_channel(db, SlackPurpose.DEFAULT)
    if default:
        return default.webhook_url
    # ENV fallback — purpose에 따라 두 변수 분기
    if purpose == SlackPurpose.DIGEST and settings.DIGEST_SLACK_WEBHOOK_URL:
        return settings.DIGEST_SLACK_WEBHOOK_URL
    return settings.SLACK_WEBHOOK_URL


async def test_send(webhook_url: str, text: str) -> tuple[bool, str | None]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(webhook_url, json={"text": text})
            if r.status_code >= 400:
                return False, f"HTTP {r.status_code}: {r.text[:120]}"
            return True, None
    except Exception as exc:
        logger.warning("slack_test_failed", error=str(exc))
        return False, str(exc)
