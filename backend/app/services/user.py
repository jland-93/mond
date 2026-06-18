"""
User 서비스 — SSO callback / Dev login 처리, 첫 가입자 ADMIN 지정
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import Role, User


def _admin_emails() -> set[str]:
    return {e.strip().lower() for e in (settings.SSO_ADMIN_EMAILS or "").split(",") if e.strip()}


async def upsert_user(
    db: AsyncSession,
    *,
    email: str,
    name: str | None = None,
    picture_url: str | None = None,
    sso_provider: str | None = None,
    sso_subject: str | None = None,
) -> User:
    email = email.strip().lower()
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    is_first = (await db.execute(select(func.count(User.id)))).scalar_one() == 0
    target_role = (
        Role.ADMIN if (email in _admin_emails() or is_first) else Role.EMPLOYEE
    )

    if user is None:
        user = User(
            email=email,
            name=name,
            picture_url=picture_url,
            sso_provider=sso_provider,
            sso_subject=sso_subject,
            role=target_role,
        )
        db.add(user)
    else:
        if name and not user.name:
            user.name = name
        if picture_url and not user.picture_url:
            user.picture_url = picture_url
        if sso_provider and not user.sso_provider:
            user.sso_provider = sso_provider
            user.sso_subject = sso_subject
        # 명시적으로 admin 리스트에 들어 있으면 승급
        if email in _admin_emails() and user.role != Role.ADMIN:
            user.role = Role.ADMIN

    await db.commit()
    await db.refresh(user)
    return user
