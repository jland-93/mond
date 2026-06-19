"""
Notifications — Slack / Generic Webhook

엔드포인트가 비어 있으면 조용히 no-op. 운영자가 .env에 URL을 채우거나
Admin → Slack 페이지에서 등록하면 활성화된다.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.slack import SlackPurpose
from app.services import slack as slack_service

logger = get_logger(__name__)

SEVERITY_EMOJI = {
    "critical": "🚨",
    "high": "⚠️",
    "medium": "🟡",
    "low": "ℹ️",
    "info": "✅",
}


async def notify_finding(finding) -> None:
    """발견사항 1건이 임계치 이상이면 알림 채널에 전송."""
    threshold = (settings.NOTIFY_MIN_SEVERITY or "high").lower()
    levels = ["info", "low", "medium", "high", "critical"]
    try:
        if levels.index(finding.severity.value) < levels.index(threshold):
            return
    except ValueError:
        return

    emoji = SEVERITY_EMOJI.get(finding.severity.value, "🔍")
    text = (
        f"{emoji} *Mond* — {finding.severity.value.upper()} finding\n"
        f"• *{finding.title}*\n"
        f"• rule: `{finding.rule_id}` · scanner: `{finding.scanner}`\n"
        f"• location: `{finding.location or '-'}`"
    )

    # DB의 FINDING purpose 채널 우선, 없으면 DEFAULT, 없으면 ENV.
    async with AsyncSessionLocal() as db:
        slack_url = await slack_service.resolve_webhook(db, SlackPurpose.FINDING)

    payloads: list[tuple[str, dict]] = []
    if slack_url:
        payloads.append((slack_url, {"text": text}))
    if settings.GENERIC_WEBHOOK_URL:
        payloads.append(
            (
                settings.GENERIC_WEBHOOK_URL,
                {
                    "source": "mond",
                    "kind": "finding",
                    "severity": finding.severity.value,
                    "title": finding.title,
                    "rule_id": finding.rule_id,
                    "scanner": finding.scanner,
                    "location": finding.location,
                    "fingerprint": finding.fingerprint,
                },
            )
        )

    if not payloads:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        for url, body in payloads:
            try:
                await client.post(url, json=body)
            except Exception as exc:  # 외부 채널 실패가 코어를 막지 않게
                logger.warning("notification_failed", url=url, error=str(exc))
