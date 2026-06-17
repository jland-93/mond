"""
🌙 Finding — 스캔이 발견한 보안 이슈
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ai_insight import AIInsight
    from app.models.asset import Asset
    from app.models.scan import Scan


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"          # 의도된 무시 (정책 인정)
    FALSE_POSITIVE = "false_positive"  # 오탐


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_id: Mapped[int | None] = mapped_column(
        ForeignKey("scans.id", ondelete="SET NULL"),
        index=True,
    )

    rule_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity", native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, name="finding_status", native_enum=False),
        nullable=False,
        default=FindingStatus.NEW,
        index=True,
    )

    scanner: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(1024))  # path:line, URL, 리소스 식별자
    references: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # CVE/CWE/외부 링크
    fingerprint: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="findings", lazy="joined")
    scan: Mapped["Scan | None"] = relationship(back_populates="findings")
    ai_insights: Mapped[list["AIInsight"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
    )
