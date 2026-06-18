"""
🌙 AIInsight 스키마
"""

from pydantic import BaseModel, Field

from app.models.ai_insight import InsightKind
from app.schemas.common import Timestamped


class AIInsightRead(Timestamped):
    id: int
    finding_id: int | None = None
    kind: InsightKind
    model: str
    summary: str
    confidence: float | None = None
    recommended_severity: str | None = None
    remediation: dict = Field(default_factory=dict)
    input_tokens: int | None = None
    output_tokens: int | None = None


class AnalyzeRequest(BaseModel):
    """자연어 → 스캔/분석 트리거"""

    query: str = Field(..., min_length=3, max_length=2000)
    asset_id: int | None = None


class AnalyzeResponse(BaseModel):
    intent: str
    summary: str
    suggested_actions: list[dict] = Field(default_factory=list)
    model: str
    citations: list[dict] = Field(default_factory=list)
