"""
'내 페이지' 집계 — 본인이 소유한 자산, 자기 발견사항, 자기 권한 요청, 활성 권한.

owner 매핑은 Asset.owner = user.email 기준.
세분화된 assignee 모델은 v0.2 backlog. 지금은 자산 소유로 derive.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus
from app.models.iam import AccessRequest, AccessRequestStatus
from app.models.scan import Scan
from app.models.user import User


async def get_me_overview(session: AsyncSession, user: User) -> dict:
    """본인 화면에 쓰일 데이터 한 묶음."""
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=7)

    # 내 자산 — owner == email
    my_assets_q = await session.execute(
        select(Asset).where(Asset.owner == user.email).order_by(Asset.created_at.desc()).limit(50)
    )
    my_assets = my_assets_q.scalars().all()
    asset_ids = [a.id for a in my_assets]

    # 미해결 발견사항 합계
    open_findings_total = 0
    open_by_severity: dict[str, int] = {}
    recent_findings: list[Finding] = []
    if asset_ids:
        q = await session.execute(
            select(Finding)
            .where(
                and_(
                    Finding.asset_id.in_(asset_ids),
                    Finding.status.in_([FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]),
                )
            )
            .order_by(Finding.created_at.desc())
            .limit(200)
        )
        all_open = q.scalars().all()
        open_findings_total = len(all_open)
        for f in all_open:
            sev = f.severity.value
            open_by_severity[sev] = open_by_severity.get(sev, 0) + 1
        recent_findings = all_open[:10]

    # 내 권한 요청 (requester == email) — 최근 20개
    req_q = await session.execute(
        select(AccessRequest)
        .where(AccessRequest.requester == user.email)
        .order_by(AccessRequest.created_at.desc())
        .limit(20)
    )
    my_requests = req_q.scalars().all()

    # 만료 임박 (현재로부터 7일 이내) 활성 권한
    expiring_q = await session.execute(
        select(AccessRequest)
        .where(
            and_(
                AccessRequest.requester == user.email,
                AccessRequest.status == AccessRequestStatus.GRANTED,
                AccessRequest.revoked_at.is_(None),
                AccessRequest.expires_at.is_not(None),
                AccessRequest.expires_at <= soon,
            )
        )
        .order_by(AccessRequest.expires_at.asc())
    )
    expiring = expiring_q.scalars().all()

    # 최근 스캔 (자산 기준) 5개
    recent_scans: list[Scan] = []
    if asset_ids:
        s_q = await session.execute(
            select(Scan)
            .where(Scan.asset_id.in_(asset_ids))
            .order_by(Scan.created_at.desc())
            .limit(5)
        )
        recent_scans = s_q.scalars().all()

    return {
        "user": {
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
        "summary": {
            "my_assets_total": len(my_assets),
            "open_findings_total": open_findings_total,
            "open_by_severity": open_by_severity,
            "active_requests": sum(
                1
                for r in my_requests
                if r.status
                in {AccessRequestStatus.PENDING_AI_REVIEW, AccessRequestStatus.NEEDS_HUMAN_REVIEW}
            ),
            "expiring_soon": len(expiring),
        },
        "my_assets": [
            {
                "id": a.id,
                "name": a.name,
                "asset_type": a.asset_type.value,
                "environment": a.environment,
                "open_findings_count": a.open_findings_count,
                "last_scanned_at_str": a.last_scanned_at_str,
            }
            for a in my_assets[:10]
        ],
        "recent_findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "status": f.status.value,
                "asset_id": f.asset_id,
                "created_at": f.created_at.isoformat(),
            }
            for f in recent_findings
        ],
        "my_requests": [
            {
                "id": r.id,
                "permission_name": r.permission.name if r.permission else "?",
                "status": r.status.value,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in my_requests
        ],
        "expiring_soon": [
            {
                "id": r.id,
                "permission_name": r.permission.name if r.permission else "?",
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "days_left": max(0, int((r.expires_at - now).total_seconds() / 86400)) if r.expires_at else None,
            }
            for r in expiring
        ],
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
    }
