"""
AI 토큰 사용량 — record + 집계.

record는 complete_json 직후 호출되고, 집계는 Admin UI/대시보드용.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.ai_usage import AIUsageLog

logger = get_logger(__name__)


async def record(
    db: AsyncSession,
    *,
    provider: str,
    model: str,
    tier: str,
    intent: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    failed: bool,
) -> None:
    """호출 1건의 토큰 사용량을 기록. None은 0으로 fallback."""
    row = AIUsageLog(
        provider=provider,
        model=model,
        tier=tier,
        intent=intent,
        input_tokens=int(input_tokens or 0),
        output_tokens=int(output_tokens or 0),
        failed=failed,
    )
    db.add(row)
    await db.commit()


async def summary(db: AsyncSession, *, days: int = 7) -> dict[str, Any]:
    """최근 N일 집계 — provider/tier/intent별 합계 + 일별 시계열."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # 전체 카운트
    total_q = select(
        func.count(AIUsageLog.id),
        func.coalesce(func.sum(AIUsageLog.input_tokens), 0),
        func.coalesce(func.sum(AIUsageLog.output_tokens), 0),
    ).where(AIUsageLog.created_at >= since)
    total_row = (await db.execute(total_q)).one()
    total_calls, total_in, total_out = total_row

    failed_q = select(func.count(AIUsageLog.id)).where(
        AIUsageLog.created_at >= since, AIUsageLog.failed.is_(True)
    )
    total_failed = (await db.execute(failed_q)).scalar_one()

    # provider별
    by_provider_q = (
        select(
            AIUsageLog.provider,
            func.count(AIUsageLog.id),
            func.coalesce(func.sum(AIUsageLog.input_tokens), 0),
            func.coalesce(func.sum(AIUsageLog.output_tokens), 0),
        )
        .where(AIUsageLog.created_at >= since)
        .group_by(AIUsageLog.provider)
        .order_by(func.count(AIUsageLog.id).desc())
    )
    by_provider = [
        {"provider": p, "calls": c, "input_tokens": int(i), "output_tokens": int(o)}
        for p, c, i, o in (await db.execute(by_provider_q)).all()
    ]

    # tier별 (default vs deep)
    by_tier_q = (
        select(
            AIUsageLog.tier,
            func.count(AIUsageLog.id),
            func.coalesce(func.sum(AIUsageLog.input_tokens), 0),
            func.coalesce(func.sum(AIUsageLog.output_tokens), 0),
        )
        .where(AIUsageLog.created_at >= since)
        .group_by(AIUsageLog.tier)
    )
    by_tier = [
        {"tier": t, "calls": c, "input_tokens": int(i), "output_tokens": int(o)}
        for t, c, i, o in (await db.execute(by_tier_q)).all()
    ]

    # intent별
    by_intent_q = (
        select(
            AIUsageLog.intent,
            func.count(AIUsageLog.id),
            func.coalesce(func.sum(AIUsageLog.input_tokens), 0),
            func.coalesce(func.sum(AIUsageLog.output_tokens), 0),
        )
        .where(AIUsageLog.created_at >= since)
        .group_by(AIUsageLog.intent)
        .order_by(func.count(AIUsageLog.id).desc())
        .limit(20)
    )
    by_intent = [
        {"intent": i or "—", "calls": c, "input_tokens": int(inp), "output_tokens": int(out)}
        for i, c, inp, out in (await db.execute(by_intent_q)).all()
    ]

    # 일별 시계열
    day_expr = func.date_trunc("day", AIUsageLog.created_at)
    by_day_q = (
        select(
            day_expr.label("day"),
            func.count(AIUsageLog.id),
            func.coalesce(func.sum(AIUsageLog.input_tokens), 0),
            func.coalesce(func.sum(AIUsageLog.output_tokens), 0),
        )
        .where(AIUsageLog.created_at >= since)
        .group_by(day_expr)
        .order_by(day_expr)
    )
    by_day = [
        {
            "day": d.isoformat() if hasattr(d, "isoformat") else str(d),
            "calls": c,
            "input_tokens": int(i),
            "output_tokens": int(o),
        }
        for d, c, i, o in (await db.execute(by_day_q)).all()
    ]

    return {
        "days": days,
        "since": since.isoformat(),
        "total": {
            "calls": int(total_calls or 0),
            "input_tokens": int(total_in or 0),
            "output_tokens": int(total_out or 0),
            "failed": int(total_failed or 0),
        },
        "by_provider": by_provider,
        "by_tier": by_tier,
        "by_intent": by_intent,
        "by_day": by_day,
    }
