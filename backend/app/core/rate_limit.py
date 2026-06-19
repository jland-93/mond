"""
Rate limit — Redis 기반 fixed-window counter

운영용 abuse 보호. login brute-force · AI 호출 비용 · webhook flood 차단.

설계 메모:
  - sliding window log보다 메모리/CPU가 적은 fixed window 사용. 1분 윈도우면
    경계 효과는 무시 가능. abuse 보호 목적엔 충분.
  - Redis 실패 시 fail open. 보안보다 가용성을 택함 (자체 호스팅 OSS이므로
    의도된 결정). 실패는 structlog warn으로 남김.
  - RATE_LIMIT_ENABLED=false면 의존성 자체가 통과. test/CI 편의.

scope:
  - "ip"   원격 IP. 로그인 · webhook 등 익명 endpoint에 사용.
  - "user" 인증된 사용자 ID. AI · admin action 등 비용/책임이 사용자에 귀속.
  - "global" 단일 키. 전체 처리량 상한 (드물게 사용).
"""

from __future__ import annotations

import structlog
from fastapi import Depends, HTTPException, Request, Response, status
from redis import asyncio as aioredis

from app.auth.deps import current_user_or_none
from app.core.config import settings
from app.models.user import User

logger = structlog.get_logger(__name__)

_redis: aioredis.Redis | None = None


def _client() -> aioredis.Redis:
    """lazy singleton. Celery worker / web 둘 다 같은 URL 공유."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _client_ip(request: Request) -> str:
    # X-Forwarded-For 첫 항목 → fallback to socket. 신뢰 가능한 reverse proxy 가정.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimiter:
    """단일 버킷 의존성 팩토리.

    사용 예:
      router = APIRouter(dependencies=[Depends(RateLimiter("login", 10, 60, "ip"))])
    """

    def __init__(self, name: str, limit: int, window_s: int, scope: str = "ip") -> None:
        self.name = name
        self.limit = limit
        self.window_s = window_s
        self.scope = scope

    async def __call__(
        self,
        request: Request,
        response: Response,
        user: User | None = Depends(current_user_or_none),
    ) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        if self.scope == "user":
            ident = f"u:{user.id}" if user else f"ip:{_client_ip(request)}"
        elif self.scope == "global":
            ident = "global"
        else:
            ident = f"ip:{_client_ip(request)}"

        key = f"rl:{self.name}:{ident}"
        try:
            r = _client()
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, self.window_s)
                ttl = self.window_s
            else:
                ttl = await r.ttl(key)
        except Exception as e:
            logger.warning("rate_limit_redis_down", bucket=self.name, error=str(e))
            return

        remaining = max(0, self.limit - current)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(max(ttl, 0))

        if current > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"요청이 너무 많습니다 — {self.name} (한도 {self.limit}/{self.window_s}s)",
                headers={"Retry-After": str(max(ttl, 1))},
            )
