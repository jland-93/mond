"""
🌙 User + UserSession — SSO/OIDC 또는 Dev Login으로 발급된 임직원 계정과 세션

세션은 stateless JWT 대신 DB에 opaque token으로 저장한다 (즉시 revoke + 로그아웃 확실성).
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, LargeBinary, String
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

    # MFA 등록 여부 캐시 (실제 검증은 webauthn/totp 테이블 + 정책)
    # 사용자가 등록한 factor가 1개 이상이면 True.
    mfa_enrolled: Mapped[bool] = mapped_column(
        default=False, nullable=False, server_default="false"
    )

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

    # MFA가 아직 통과되지 않은 pre-mfa 세션은 정상 보호 리소스 접근 불가.
    # 1차 인증(이메일/SSO) 직후 발급되고, MFA 검증이 성공해야 mfa_verified=True가 된다.
    mfa_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )

    user: Mapped["User"] = relationship(back_populates="sessions", lazy="joined")


# ── WebAuthn 자격증명 (패스키 / FIDO2 / 보안 키) ──────────────────
class WebAuthnCredential(Base, TimestampMixin):
    """사용자가 등록한 패스키 1개. 한 사용자가 여러 디바이스에서 여러 키를 등록할 수 있다."""

    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # WebAuthn credential_id — 인증 단계의 allowCredentials와 비교에 쓰임.
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, unique=True, index=True)
    # COSE-encoded public key — 서명 검증에 사용.
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # 누적 서명 카운터 — 복제 탐지(클론된 키).
    sign_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 사용자가 직접 붙인 라벨 (예: "MacBook Touch ID", "YubiKey 5C")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # 콤마 join transports (예: "usb,nfc")
    transports: Mapped[str | None] = mapped_column(String(64))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── TOTP secret (Google Authenticator 등) ────────────────────────
class TotpSecret(Base, TimestampMixin):
    __tablename__ = "totp_secrets"

    id: Mapped[int] = mapped_column(primary_key=True)
    # User 1:1
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    # base32 secret. 진짜 운영에선 KMS·앱 단 암호화 권장 — 코멘트로만 안내.
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    # setup 완료(verify) 전에는 confirmed=False — 미확정은 로그인 시 무시.
    confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── 백업 코드 ──────────────────────────────────────────────────
class MfaBackupCode(Base, TimestampMixin):
    """일회용 백업 코드. raw는 표시 직후 사용자만 보관, DB는 sha256만."""

    __tablename__ = "mfa_backup_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── WebAuthn challenge (등록/인증 라운드 1회용) ────────────────
class WebAuthnChallenge(Base, TimestampMixin):
    """begin → complete 사이 짧게 유지되는 challenge 저장소. Redis로 옮겨도 OK."""

    __tablename__ = "webauthn_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 등록은 user_id로, 인증은 session_id로 묶는다.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pre_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="CASCADE"), index=True
    )
    # 'registration' | 'authentication'
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)
    challenge: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
