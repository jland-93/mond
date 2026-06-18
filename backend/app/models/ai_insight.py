"""
AIInsight — LLM 기반 분석 산출물 (triage / remediation / summary / explain)
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.finding import Finding


class InsightKind(str, enum.Enum):
    TRIAGE = "triage"            # severity 재평가 + 우선순위
    REMEDIATION = "remediation"  # 수정 코드/명령 제안
    SUMMARY = "summary"          # 자연어 요약
    EXPLAIN = "explain"          # 왜 이게 위험한지 설명


class AIInsight(Base, TimestampMixin):
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"),
        index=True,
    )

    kind: Mapped[InsightKind] = mapped_column(
        Enum(InsightKind, name="insight_kind", native_enum=False),
        nullable=False,
        index=True,
    )
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    recommended_severity: Mapped[str | None] = mapped_column(String(16))

    # 수정 가이드: {"steps": [...], "code": "...", "references": [...]}
    remediation: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)

    finding: Mapped["Finding | None"] = relationship(back_populates="ai_insights")
