"""
알림 채널 — Discord / MS Teams 어댑터.

Slack과 Generic webhook은 기존 notifications.py가 직접 처리한다. 여기서는
*payload 포맷이 다른* Discord/Teams만 다룬다. 같은 finding이라도 채널마다
포맷이 다르므로 변환 책임을 한 곳에 모으는 게 목적.

설계 원칙
--------
- URL 미설정 채널은 silent skip — 운영 단계별 점진 활성화를 허용.
- payload는 텍스트 위주(공통). severity emoji는 그대로 인계.
- Slack 흐름과 분리되어 있어 한 채널 실패가 다른 채널을 막지 않는다.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 색상 코드 — Discord embed / Teams themeColor 양쪽에서 사용 (RGB hex)
SEVERITY_COLOR_HEX = {
    "critical": "C0392B",   # 진한 빨강
    "high": "E67E22",       # 주황
    "medium": "F1C40F",     # 노랑
    "low": "3498DB",        # 파랑
    "info": "95A5A6",       # 회색
}


def discord_payload(*, title: str, body: str, severity: str) -> dict:
    """Discord webhook 형식 — embed 1건.

    Discord는 `content`로 평문도 받지만 embed가 색상/필드 분리가 깔끔.
    color는 10진수 int로 줘야 한다 (RGB 0xRRGGBB).
    """
    color_int = int(SEVERITY_COLOR_HEX.get(severity, "95A5A6"), 16)
    return {
        "embeds": [
            {
                "title": title,
                "description": body,
                "color": color_int,
            }
        ],
        # embed가 막힌 환경(권한 부족)을 위한 평문 fallback.
        "content": title,
    }


def teams_payload(*, title: str, body: str, severity: str) -> dict:
    """MS Teams Incoming Webhook용 MessageCard.

    Teams의 Adaptive Card는 connector 종류에 따라 안 받는 환경이 많아
    legacy MessageCard 형식이 가장 호환성 높음.
    """
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": SEVERITY_COLOR_HEX.get(severity, "95A5A6"),
        "title": title,
        "text": body,
    }


async def post_discord(text: str, *, title: str, severity: str) -> bool:
    url = settings.DISCORD_WEBHOOK_URL
    if not url:
        return False
    return await _post(url, discord_payload(title=title, body=text, severity=severity), label="discord")


async def post_teams(text: str, *, title: str, severity: str) -> bool:
    url = settings.TEAMS_WEBHOOK_URL
    if not url:
        return False
    return await _post(url, teams_payload(title=title, body=text, severity=severity), label="teams")


async def _post(url: str, payload: dict, *, label: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload)
            if r.status_code >= 400:
                logger.warning("notify_channel_failed", channel=label, status=r.status_code)
                return False
            return True
    except Exception as exc:
        logger.warning("notify_channel_exception", channel=label, error=str(exc))
        return False
