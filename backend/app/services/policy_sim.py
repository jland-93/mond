"""
Policy Simulator — 가상의 finding 목록을 받아 활성 정책 게이트를 시뮬레이션
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Severity
from app.models.policy import Policy

SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


@dataclass
class SimFinding:
    rule_id: str
    severity: str
    scanner: str | None = None


@dataclass
class SimResult:
    policy_id: int
    policy_name: str
    policy_type: str
    enabled: bool
    threshold: str
    blocked: bool
    reason: str
    matched: list[str]


def _at_or_above(threshold_str: str) -> set[Severity]:
    try:
        threshold = Severity(threshold_str.lower())
    except ValueError:
        threshold = Severity.MEDIUM
    return {s for s in Severity if SEVERITY_RANK[s] >= SEVERITY_RANK[threshold]}


async def simulate(db: AsyncSession, findings: list[SimFinding]) -> list[SimResult]:
    """모든 활성 정책에 대해 가상 finding 모음이 게이트를 통과하는지 평가."""
    policies = list((await db.execute(select(Policy))).scalars().all())

    results: list[SimResult] = []
    for p in policies:
        blocking = _at_or_above(p.severity_threshold)
        matched = [
            f"{f.rule_id} ({f.severity})"
            for f in findings
            if _coerce(f.severity) in blocking
        ]
        if not p.enabled:
            results.append(
                SimResult(
                    policy_id=p.id,
                    policy_name=p.name,
                    policy_type=p.policy_type.value,
                    enabled=False,
                    threshold=p.severity_threshold,
                    blocked=False,
                    reason="정책이 비활성화 상태",
                    matched=matched,
                )
            )
            continue
        blocked = bool(matched)
        results.append(
            SimResult(
                policy_id=p.id,
                policy_name=p.name,
                policy_type=p.policy_type.value,
                enabled=True,
                threshold=p.severity_threshold,
                blocked=blocked,
                reason=(
                    f"{len(matched)}건이 임계치 '{p.severity_threshold}' 이상에 해당"
                    if blocked
                    else "임계치 이상 발견사항 없음"
                ),
                matched=matched,
            )
        )
    return results


def _coerce(value: str) -> Severity:
    try:
        return Severity(value.lower())
    except ValueError:
        return Severity.INFO
