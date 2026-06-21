"""
Discord/Teams 어댑터 — payload 포맷 invariant.

실제 webhook 호출은 외부 의존이라 단위로 테스트하기 어려워, 두 가지로 검증:
  1) payload shape (color/title/필드)
  2) URL 미설정 시 silent skip (False 반환)
"""

import pytest

from app.core.config import settings
from app.services.notify_channels import (
    SEVERITY_COLOR_HEX,
    discord_payload,
    post_discord,
    post_teams,
    teams_payload,
)


def test_discord_payload_critical_color():
    p = discord_payload(title="t", body="b", severity="critical")
    assert p["content"] == "t"
    emb = p["embeds"][0]
    assert emb["title"] == "t"
    assert emb["description"] == "b"
    # 0xC0392B = 12597291
    assert emb["color"] == int(SEVERITY_COLOR_HEX["critical"], 16)


def test_discord_payload_unknown_severity_defaults_grey():
    p = discord_payload(title="t", body="b", severity="weird")
    assert p["embeds"][0]["color"] == int(SEVERITY_COLOR_HEX["info"], 16)


def test_teams_payload_message_card_shape():
    p = teams_payload(title="t", body="b", severity="high")
    assert p["@type"] == "MessageCard"
    assert p["@context"].endswith("/extensions")
    assert p["summary"] == "t"
    assert p["title"] == "t"
    assert p["text"] == "b"
    # themeColor는 hex 문자열(접두사 # 없이) — Teams 스펙
    assert p["themeColor"] == SEVERITY_COLOR_HEX["high"]


@pytest.mark.asyncio
async def test_post_discord_skips_when_url_missing(monkeypatch):
    monkeypatch.setattr(settings, "DISCORD_WEBHOOK_URL", None)
    ok = await post_discord("hello", title="t", severity="high")
    assert ok is False


@pytest.mark.asyncio
async def test_post_teams_skips_when_url_missing(monkeypatch):
    monkeypatch.setattr(settings, "TEAMS_WEBHOOK_URL", None)
    ok = await post_teams("hello", title="t", severity="high")
    assert ok is False
