"""
🌙 AI 서비스 — Finding 분석을 DB에 영속화
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import insights as ai_insights
from app.models.ai_insight import AIInsight, InsightKind
from app.models.finding import Finding


async def analyze_and_store(
    db: AsyncSession,
    finding: Finding,
    *,
    kind: InsightKind = InsightKind.TRIAGE,
    deep: bool = False,
) -> AIInsight:
    result = await ai_insights.analyze_finding(db, finding, deep=deep)
    insight = AIInsight(
        finding_id=finding.id,
        kind=kind,
        model=result.model,
        summary=result.summary,
        confidence=result.confidence,
        recommended_severity=result.recommended_severity.value,
        remediation=result.remediation,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


async def list_insights_for_finding(db: AsyncSession, finding_id: int) -> list[AIInsight]:
    stmt = (
        select(AIInsight)
        .where(AIInsight.finding_id == finding_id)
        .order_by(AIInsight.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())
