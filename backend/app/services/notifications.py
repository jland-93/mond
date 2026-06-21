"""
Notifications — Slack / Generic Webhook

엔드포인트가 비어 있으면 조용히 no-op. 운영자가 .env에 URL을 채우거나
Admin → Slack 페이지에서 등록하면 활성화된다.
"""

from __future__ import annotations

import httpx

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.asset import Asset
from app.models.slack import SlackPurpose
from app.models.user import User
from app.models.user_slack import UserSlackPreference
from app.services import notify_channels
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
    base_text = (
        f"{emoji} *Mond* — {finding.severity.value.upper()} finding\n"
        f"• *{finding.title}*\n"
        f"• rule: `{finding.rule_id}` · scanner: `{finding.scanner}`\n"
        f"• location: `{finding.location or '-'}`"
    )

    # asset owner의 Slack preference 찾기 — DM + mention.
    owner_dm_url: str | None = None
    owner_mention: str | None = None
    async with AsyncSessionLocal() as db:
        asset = (await db.execute(select(Asset).where(Asset.id == finding.asset_id))).scalar_one_or_none()
        owner_email = asset.owner if asset else None
        if owner_email:
            owner_user = (await db.execute(select(User).where(User.email == owner_email))).scalar_one_or_none()
            if owner_user:
                pref = (await db.execute(
                    select(UserSlackPreference).where(UserSlackPreference.user_id == owner_user.id)
                )).scalar_one_or_none()
                if pref and pref.notify_finding:
                    owner_dm_url = pref.slack_dm_webhook_url
                    owner_mention = pref.slack_user_id

        # DB의 FINDING purpose 채널 우선, 없으면 DEFAULT, 없으면 ENV.
        slack_url = await slack_service.resolve_webhook(db, SlackPurpose.FINDING)

    text = base_text
    if owner_mention:
        text = f"<@{owner_mention}> {base_text}"

    payloads: list[tuple[str, dict]] = []
    if slack_url:
        payloads.append((slack_url, {"text": text}))
    if owner_dm_url and owner_dm_url != slack_url:
        # 본인 DM은 mention 빼고 본문만.
        payloads.append((owner_dm_url, {"text": base_text}))
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

    if payloads:
        async with httpx.AsyncClient(timeout=10) as client:
            for url, body in payloads:
                try:
                    await client.post(url, json=body)
                except Exception as exc:  # 외부 채널 실패가 코어를 막지 않게
                    logger.warning("notification_failed", url=url, error=str(exc))

    # Discord/Teams — 포맷이 달라 별도 어댑터로. URL 미설정이면 silent skip.
    sev = finding.severity.value
    short_title = f"{emoji} Mond — {sev.upper()} finding · {finding.title}"
    await notify_channels.post_discord(base_text, title=short_title, severity=sev)
    await notify_channels.post_teams(base_text, title=short_title, severity=sev)
