"""
🌙 Dashboard 서비스 — 메인 페이지 요약 통계
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus, Severity
from app.models.scan import Scan, ScanStatus


SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 20,
    Severity.HIGH: 8,
    Severity.MEDIUM: 3,
    Severity.LOW: 1,
    Severity.INFO: 0,
}


async def overview(db: AsyncSession) -> dict:
    asset_total = (await db.execute(select(func.count(Asset.id)))).scalar_one()

    open_finding_stmt = (
        select(Finding.severity, func.count(Finding.id))
        .where(
            Finding.status.in_(
                [FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]
            )
        )
        .group_by(Finding.severity)
    )
    severity_counts = {row[0]: int(row[1]) for row in (await db.execute(open_finding_stmt)).all()}

    open_total = sum(severity_counts.values())
    weighted = sum(SEVERITY_WEIGHTS[s] * severity_counts.get(s, 0) for s in Severity)
    # 100점에서 감점 — 단순 모델
    security_score = max(0, 100 - min(weighted, 100))

    recent_scans = (
        await db.execute(
            select(Scan).order_by(Scan.id.desc()).limit(5)
        )
    ).scalars().all()

    recent_findings = (
        await db.execute(
            select(Finding).order_by(Finding.id.desc()).limit(10)
        )
    ).scalars().all()

    # 최근 7일 스캔 추이
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    scans_recent = (
        await db.execute(
            select(func.count(Scan.id))
            .where(Scan.created_at >= seven_days_ago)
        )
    ).scalar_one()

    return {
        "security_score": security_score,
        "asset_total": int(asset_total),
        "open_findings_total": open_total,
        "open_findings_by_severity": {s.value: severity_counts.get(s, 0) for s in Severity},
        "scans_last_7d": int(scans_recent),
        "recent_scans": [
            {
                "id": s.id,
                "asset_id": s.asset_id,
                "scanner": s.scanner,
                "status": s.status.value,
                "findings_count": s.findings_count,
                "created_at": s.created_at.isoformat(),
            }
            for s in recent_scans
        ],
        "recent_findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "scanner": f.scanner,
                "asset_id": f.asset_id,
                "created_at": f.created_at.isoformat(),
            }
            for f in recent_findings
        ],
    }
