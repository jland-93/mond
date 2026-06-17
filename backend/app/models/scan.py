"""
🌙 Scan — 자산에 대한 1회 스캔 실행 (스캐너 어댑터를 호출한 결과)
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.finding import Finding


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanTrigger(str, enum.Enum):
    MANUAL = "manual"          # UI/API에서 사람이 트리거
    SCHEDULED = "scheduled"    # Celery beat (크론잡)
    WEBHOOK = "webhook"        # 외부 이벤트 (CI/SCM)
    AI = "ai"                  # 자연어 → 스캔 실행 경로


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scanner: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trigger: Mapped[ScanTrigger] = mapped_column(
        Enum(ScanTrigger, name="scan_trigger", native_enum=False),
        nullable=False,
        default=ScanTrigger.MANUAL,
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status", native_enum=False),
        nullable=False,
        default=ScanStatus.PENDING,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_output: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)

    asset: Mapped["Asset"] = relationship(back_populates="scans", lazy="joined")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
    )
