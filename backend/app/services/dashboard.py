"""
Dashboard 서비스 — 메인 페이지 요약 통계 + 시계열 + 활동 피드
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus, Severity
from app.models.iam import AccessRequest, AccessRequestStatus
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

    open_statuses = [FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]
    open_finding_stmt = (
        select(Finding.severity, func.count(Finding.id))
        .where(Finding.status.in_(open_statuses))
        .group_by(Finding.severity)
    )
    severity_counts = {row[0]: int(row[1]) for row in (await db.execute(open_finding_stmt)).all()}

    open_total = sum(severity_counts.values())
    weighted = sum(SEVERITY_WEIGHTS[s] * severity_counts.get(s, 0) for s in Severity)
    security_score = max(0, 100 - min(weighted, 100))

    recent_scans = (await db.execute(select(Scan).order_by(Scan.id.desc()).limit(5))).scalars().all()
    recent_findings = (
        await db.execute(select(Finding).order_by(Finding.id.desc()).limit(10))
    ).scalars().all()

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    scans_recent_total = (
        await db.execute(select(func.count(Scan.id)).where(Scan.created_at >= seven_days_ago))
    ).scalar_one()

    # ── 7일 시계열 — 일별 finding/scan 카운트 ────────────────────
    trend_days: list[dict] = []
    for offset in range(6, -1, -1):
        day_start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        scans_today = (
            await db.execute(
                select(func.count(Scan.id)).where(
                    Scan.created_at >= day_start, Scan.created_at < day_end
                )
            )
        ).scalar_one()
        findings_today = (
            await db.execute(
                select(func.count(Finding.id)).where(
                    Finding.created_at >= day_start, Finding.created_at < day_end
                )
            )
        ).scalar_one()
        critical_today = (
            await db.execute(
                select(func.count(Finding.id)).where(
                    Finding.created_at >= day_start,
                    Finding.created_at < day_end,
                    Finding.severity == Severity.CRITICAL,
                )
            )
        ).scalar_one()
        trend_days.append({
            "date": day_start.strftime("%m-%d"),
            "scans": int(scans_today),
            "findings": int(findings_today),
            "critical": int(critical_today),
        })

    # ── Top assets by 미해결 finding count ─────────────────────
    top_assets_rows = (
        await db.execute(
            select(Asset, func.count(Finding.id).label("c"))
            .join(Finding, Finding.asset_id == Asset.id)
            .where(Finding.status.in_(open_statuses))
            .group_by(Asset.id)
            .order_by(func.count(Finding.id).desc())
            .limit(5)
        )
    ).all()
    top_assets = [
        {
            "id": a.id,
            "name": a.name,
            "asset_type": a.asset_type.value,
            "open_findings": int(c),
        }
        for a, c in top_assets_rows
    ]

    # ── Activity 피드 — 최근 활동 통합 (scan / finding / access) ─
    activity: list[dict] = []
    for s in (await db.execute(select(Scan).order_by(Scan.id.desc()).limit(8))).scalars().all():
        activity.append({
            "kind": "scan",
            "id": s.id,
            "label": f"{s.scanner} scan",
            "meta": s.status.value,
            "severity": "low" if s.status == ScanStatus.COMPLETED else "high" if s.status == ScanStatus.FAILED else "info",
            "at": s.created_at.isoformat(),
        })
    for f in (await db.execute(select(Finding).order_by(Finding.id.desc()).limit(8))).scalars().all():
        activity.append({
            "kind": "finding",
            "id": f.id,
            "label": f.title,
            "meta": f.scanner,
            "severity": f.severity.value,
            "at": f.created_at.isoformat(),
        })
    for r in (await db.execute(select(AccessRequest).order_by(AccessRequest.id.desc()).limit(6))).scalars().all():
        risk = (r.ai_decision or {}).get("risk_level", "medium")
        activity.append({
            "kind": "access",
            "id": r.id,
            "label": f"{r.requester} — access request",
            "meta": r.status.value if isinstance(r.status, AccessRequestStatus) else str(r.status),
            "severity": risk if risk in {"critical", "high", "medium", "low", "info"} else "info",
            "at": r.created_at.isoformat(),
        })
    activity.sort(key=lambda x: x["at"], reverse=True)
    activity = activity[:12]

    return {
        "security_score": security_score,
        "asset_total": int(asset_total),
        "open_findings_total": open_total,
        "open_findings_by_severity": {s.value: severity_counts.get(s, 0) for s in Severity},
        "scans_last_7d": int(scans_recent_total),
        "trend_7d": trend_days,
        "top_assets": top_assets,
        "activity": activity,
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
