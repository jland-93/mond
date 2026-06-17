"""
🌙 FastAPI 인증/인가 의존성 — current_user, require_role
"""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import resolve_session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import Role, User


async def current_user_optional(
    session_cookie: str | None = Cookie(default=None, alias=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """쿠키에서 세션 토큰을 꺼내 사용자를 조회한다. 미인증이면 None."""
    # 쿠키 이름은 settings 기반 — alias로 못 받으므로 동적 처리
    from fastapi import Request

    return None  # 실제 처리는 current_user에서 Request 받아 처리


async def current_user(
    request: __import__("fastapi").Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 필요",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return sess.user


async def current_user_or_none(
    request: __import__("fastapi").Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    return sess.user if sess else None


def require_role(*allowed: Role):
    """주어진 role 중 하나여야 통과. ADMIN은 모든 role을 포함한다 (계층)."""
    ranks = {Role.VIEWER: 1, Role.EMPLOYEE: 2, Role.REVIEWER: 3, Role.ADMIN: 4}
    min_required = min(ranks[r] for r in allowed)

    async def dep(user: User = Depends(current_user)) -> User:
        if ranks[user.role] < min_required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한 부족 — {user.role.value}는 이 작업을 수행할 수 없습니다.",
            )
        return user

    return dep
