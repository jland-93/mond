"""
🌙 Anthropic Claude 클라이언트

API 키가 없을 때는 None을 반환해 호출부가 fallback(기본 규칙)으로 동작하도록 한다.
프롬프트 캐싱은 시스템 프롬프트가 1024 토큰을 넘을 때만 효과가 있으므로,
짧은 분석 작업에서는 사용하지 않는다.
"""

from __future__ import annotations

from functools import lru_cache

from anthropic import AsyncAnthropic

from app.core.config import settings


@lru_cache(maxsize=1)
def get_client() -> AsyncAnthropic | None:
    if not settings.ANTHROPIC_API_KEY:
        return None
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def is_enabled() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)
