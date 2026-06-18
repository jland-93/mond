"""
🌙 셀프서비스 역할 변경 요청 — 임직원이 자기 role 변경을 요청, AI 1차 + ADMIN 2차.

흐름:
  pending → (AI 평가) → needs_review|auto_approved → (ADMIN) → approved|denied → 적용

설계 단순화: AccessRequest를 재사용하려고 했지만, identity/permission FK 의존이
있어 별도 모델로 분리. 모든 결정 이력은 단일 row의 JSON 필드들에 누적.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.user import Role


class RoleRequestStatus(str, enum.Enum):
    PENDING_AI_REVIEW = "pending_ai_review"
    AI_AUTO_APPROVED = "ai_auto_approved"     # 즉시 role 적용됨
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"
    DENIED = "denied"


class RoleChangeRequest(Base, TimestampMixin):
    __tablename__ = "role_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 요청 시점의 role (audit용)
    from_role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False), nullable=False
    )
    to_role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[RoleRequestStatus] = mapped_column(
        Enum(RoleRequestStatus, name="role_request_status", native_enum=False),
        nullable=False,
        default=RoleRequestStatus.PENDING_AI_REVIEW,
        index=True,
    )
    ai_decision: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reviewer_email: Mapped[str | None] = mapped_column(String(255))
    review_note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
