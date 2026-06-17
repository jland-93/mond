"""
🌙 FastAPI 인증/인가 의존성 — current_user, require_role
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import resolve_session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import Role, User


async def current_user(
    request: Request,
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
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    return sess.user if sess else None


def require_role(*allowed: Role):
    """주어진 role 중 하나여야 통과. ADMIN은 모든 role을 포함한다 (계층).

    예: require_role(Role.REVIEWER) → REVIEWER 또는 ADMIN만 통과.
    """
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
