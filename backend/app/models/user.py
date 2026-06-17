"""
🌙 User + UserSession — SSO/OIDC 또는 Dev Login으로 발급된 임직원 계정과 세션

세션은 stateless JWT 대신 DB에 opaque token으로 저장한다 (즉시 revoke + 로그아웃 확실성).
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class Role(str, enum.Enum):
    VIEWER = "viewer"      # 읽기 전용 (대시보드/규제/지식만)
    EMPLOYEE = "employee"  # 일반 직원 — 권한 요청 + 스캔 트리거
    REVIEWER = "reviewer"  # 보안 담당자 — 권한 검토 보드 + 회수
    ADMIN = "admin"        # 관리자 — 모든 설정 + IAM source + 지식 카드 관리


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    picture_url: Mapped[str | None] = mapped_column(String(1024))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False),
        nullable=False,
        default=Role.EMPLOYEE,
        index=True,
    )

    # SSO 메타 — 같은 이메일도 IdP가 다를 수 있어 subject로 식별
    sso_provider: Mapped[str | None] = mapped_column(String(64), index=True)
    sso_subject: Mapped[str | None] = mapped_column(String(255), index=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(Base, TimestampMixin):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # opaque token — SHA-256 of the raw cookie value (raw는 클라이언트만 보유)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512))
    ip: Mapped[str | None] = mapped_column(String(64))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions", lazy="joined")
