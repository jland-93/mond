"""
🌙 IAM 셀프서비스 도메인

- IAMSource    : 외부 IAM 시스템 등록 (AWS / GCP / Azure / k8s / custom)
- IAMIdentity  : 외부 시스템에서 가져온 user / role / service_account / group
- Permission   : 부여 가능한 권한 단위 (AWS Managed Policy / k8s ClusterRole / …)
- AccessRequest: 직원이 신청한 권한 요청 + AI 1차 + 담당자 2차 검토 + grant 결과
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


# ── IAMSource ────────────────────────────────────────────────────────
class IAMSourceKind(str, enum.Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    K8S = "k8s"
    CUSTOM = "custom"


class IAMSource(Base, TimestampMixin):
    __tablename__ = "iam_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    kind: Mapped[IAMSourceKind] = mapped_column(
        Enum(IAMSourceKind, name="iam_source_kind", native_enum=False),
        nullable=False,
        index=True,
    )
    # config: aws_region, account_id, role_arn 등. 자격증명은 ENV 참조 키만 저장.
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 자격증명은 DB에 저장하지 않음 — ENV 키 이름만 보관 (예: "AWS_ACCESS_KEY_ID")
    credentials_env_ref: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_synced_at_str: Mapped[str | None] = mapped_column(String(64))

    identities: Mapped[list["IAMIdentity"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


# ── IAMIdentity ──────────────────────────────────────────────────────
class IdentityType(str, enum.Enum):
    USER = "user"
    ROLE = "role"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"


class IAMIdentity(Base, TimestampMixin):
    __tablename__ = "iam_identities"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("iam_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identity_type: Mapped[IdentityType] = mapped_column(
        Enum(IdentityType, name="identity_type", native_enum=False),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(512))  # ARN, principal name 등
    attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source: Mapped["IAMSource"] = relationship(back_populates="identities")


# ── Permission ───────────────────────────────────────────────────────
class Permission(Base, TimestampMixin):
    __tablename__ = "iam_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("iam_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(512))  # ARN, role binding 등
    description: Mapped[str | None] = mapped_column(Text)
    risk_hint: Mapped[str | None] = mapped_column(String(32))  # 'admin' / 'write' / 'read' / 'unknown'
    attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source: Mapped["IAMSource"] = relationship(back_populates="permissions")


# ── AccessRequest ────────────────────────────────────────────────────
class AccessRequestStatus(str, enum.Enum):
    PENDING_AI_REVIEW = "pending_ai_review"
    AI_AUTO_APPROVED = "ai_auto_approved"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    HUMAN_APPROVED = "human_approved"
    HUMAN_DENIED = "human_denied"
    GRANTED = "granted"
    GRANT_FAILED = "grant_failed"


class AccessRequest(Base, TimestampMixin):
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    duration_hours: Mapped[int | None] = mapped_column()  # 임시 권한이면 만료 힌트

    target_identity_id: Mapped[int] = mapped_column(
        ForeignKey("iam_identities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("iam_permissions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[AccessRequestStatus] = mapped_column(
        Enum(AccessRequestStatus, name="access_request_status", native_enum=False),
        nullable=False,
        default=AccessRequestStatus.PENDING_AI_REVIEW,
        index=True,
    )

    # AI 1차 검토 (Claude 자율)
    ai_decision: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 담당자 2차 검토 (보안 담당자)
    human_decision: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # 실제 grant 결과 (AWS attach_policy 응답 또는 dry-run 메모)
    grant_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    target_identity: Mapped["IAMIdentity"] = relationship(lazy="joined")
    permission: Mapped["Permission"] = relationship(lazy="joined")
