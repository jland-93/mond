"""
🌙 사용자별 Personal Webhook Token

CI/CD 파이프라인이 사용자 인증 없이 사내 자동화에서 Mond에 finding/scan을
보낼 수 있게 발급. 같은 사용자는 여러 토큰 발급 가능 (CI별로 분리).

raw token은 발급 직후 1회만 노출하고 DB는 SHA-256 해시만 저장.
revoke 시 즉시 무효화.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WebhookToken(Base, TimestampMixin):
    __tablename__ = "webhook_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 사용자가 단 라벨 (예: "GitHub Actions · main repo")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # opaque token의 SHA-256 (raw는 발급 직후 1회만 클라이언트에 반환)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    # 앞 6자만 마스킹으로 노출 (예: "mond_a1b2••••")
    token_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
