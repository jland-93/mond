"""
서버 세션 — opaque token + DB 영속화. JWT 미사용 (즉시 revoke 가능).

cookie에는 url-safe base64 raw token이, DB에는 SHA-256 해시만 저장된다.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserSession


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token() -> str:
    """raw token 1개를 생성한다. 길이는 url-safe 43자(32 byte)."""
    return secrets.token_urlsafe(32)


async def create_session(
    db: AsyncSession,
    user: User,
    *,
    user_agent: str | None = None,
    ip: str | None = None,
) -> tuple[UserSession, str]:
    raw = issue_token()
    session = UserSession(
        user_id=user.id,
        token_hash=_hash(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.SESSION_DAYS),
        user_agent=(user_agent or "")[:512],
        ip=(ip or "")[:64],
    )
    db.add(session)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session, raw


async def resolve_session(db: AsyncSession, raw: str | None) -> UserSession | None:
    if not raw:
        return None
    stmt = (
        select(UserSession)
        .where(UserSession.token_hash == _hash(raw))
        .where(UserSession.revoked_at.is_(None))
    )
    sess = (await db.execute(stmt)).scalar_one_or_none()
    if not sess:
        return None
    if sess.expires_at <= datetime.now(timezone.utc):
        return None
    return sess


async def revoke_session(db: AsyncSession, sess: UserSession) -> None:
    sess.revoked_at = datetime.now(timezone.utc)
    await db.commit()


def set_cookie(response: Response, raw: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE,
        value=raw,
        max_age=settings.SESSION_DAYS * 86400,
        httponly=True,
        secure=settings.SESSION_SECURE,
        samesite="lax",
        path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=settings.SESSION_SECURE,
        samesite="lax",
    )
