"""
FastAPI 인증/인가 의존성 — current_user, require_role
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.mfa import mfa_required_for
from app.auth.session import resolve_session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import Role, User, UserSession


async def current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    """현재 cookie의 세션 반환. 1차 인증만 검증(MFA는 체크 X).

    MFA challenge 엔드포인트는 pre-MFA 세션도 접근해야 한다.
    일반 보호 리소스는 아래 `current_user`가 mfa_verified까지 자동 검증.
    """
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 필요",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return sess


async def current_user(
    sess: UserSession = Depends(current_session),
) -> User:
    """1차 인증 OK + MFA 강제 대상이면 mfa_verified까지 통과해야 통과."""
    user = sess.user
    if mfa_required_for(user) and not sess.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA 검증 필요",
            headers={"X-MFA-Required": "1"},
        )
    return user


async def current_user_pre_mfa(
    sess: UserSession = Depends(current_session),
) -> tuple[User, UserSession]:
    """MFA 검증 전이어도 통과. MFA 등록·challenge 엔드포인트 전용."""
    return sess.user, sess


async def current_user_or_none(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    return sess.user if sess else None


def require_role(*allowed: Role):
    """주어진 role 중 하나여야 통과. ADMIN은 모든 role을 포함 (계층)."""
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
