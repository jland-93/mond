"""
ISMS-P 인증 심사 패키지 — 통제별 evidence collector.

용도: KISA ISMS-P 인증 심사 시 심사원에게 제출하는 증빙 자료를 Mond가 가진
실 데이터로부터 자동 추출. v0.3 MVP는 핵심 10개 통제만 다룬다.

흐름:
  build_package(db, days)
    → 각 통제의 evidence_source를 dispatch
    → 컨트롤별 dict(records + summary)을 모아 반환
  render_markdown(package)
    → 위 결과를 사람이 읽는 markdown으로 직렬화 (PDF 변환은 외부 도구 권장)
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.isms_p_controls import ISMS_P_CONTROLS, ISMSControl
from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus, Severity
from app.models.iam import AccessAuditLog, AccessRequest, AccessRequestStatus
from app.models.policy import Policy
from app.models.user import Role, User


async def _policies_catalog(db: AsyncSession, **_: Any) -> dict:
    rows = list((await db.execute(select(Policy))).scalars().all())
    return {
        "summary": f"등록된 정책 {len(rows)}건 (활성 {sum(1 for p in rows if p.enabled)})",
        "records": [
            {
                "name": p.name,
                "type": p.policy_type.value if p.policy_type else None,
                "engine": getattr(p, "engine", "builtin"),
                "enabled": p.enabled,
                "threshold": getattr(p, "threshold", None),
            }
            for p in rows
        ],
    }


async def _assets_inventory(db: AsyncSession, **_: Any) -> dict:
    rows = list((await db.execute(select(Asset))).scalars().all())
    by_env: Counter = Counter((a.environment or "unspecified") for a in rows)
    by_type: Counter = Counter(a.asset_type.value for a in rows)
    return {
        "summary": (
            f"총 자산 {len(rows)} · 환경 {dict(by_env)} · 유형 {dict(by_type)}"
        ),
        "records": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.asset_type.value,
                "environment": a.environment,
                "owner": a.owner,
                "uri": a.uri,
            }
            for a in rows
        ],
    }


async def _risk_assessment(db: AsyncSession, **_: Any) -> dict:
    open_statuses = (FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS)
    q = select(Finding).where(Finding.status.in_(open_statuses))
    rows = list((await db.execute(q)).scalars().all())
    by_severity: Counter = Counter(f.severity.value for f in rows)
    critical_high = sum(by_severity.get(s, 0) for s in ("critical", "high"))
    return {
        "summary": (
            f"open finding {len(rows)} · severity {dict(by_severity)} · "
            f"critical+high {critical_high}"
        ),
        "records": [
            {
                "asset_id": f.asset_id,
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "status": f.status.value,
                "scanner": f.scanner,
                "title": f.title,
            }
            for f in rows
        ],
    }


async def _access_request_lifecycle(db: AsyncSession, *, since: datetime, **_: Any) -> dict:
    rows = list(
        (
            await db.execute(
                select(AccessRequest).where(AccessRequest.created_at >= since).order_by(AccessRequest.created_at.desc())
            )
        ).scalars().all()
    )
    by_status: Counter = Counter(r.status.value for r in rows)
    granted = by_status.get(AccessRequestStatus.GRANTED.value, 0)
    denied = by_status.get(AccessRequestStatus.HUMAN_DENIED.value, 0)
    revoked = by_status.get(AccessRequestStatus.EXPIRED_REVOKED.value, 0)
    return {
        "summary": (
            f"총 요청 {len(rows)} (기간 내) · 부여 {granted} · 거부 {denied} · "
            f"만료 자동회수 {revoked}"
        ),
        "records": [
            {
                "id": r.id,
                "requester": r.requester,
                "status": r.status.value,
                "ai_decision": (r.ai_decision or {}).get("decision"),
                "human_decision": (r.human_decision or {}).get("decision"),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
            }
            for r in rows[:50]  # 본문 보호
        ],
    }


async def _privileged_users(db: AsyncSession, **_: Any) -> dict:
    rows = list(
        (
            await db.execute(
                select(User).where(User.role.in_([Role.ADMIN, Role.REVIEWER]))
            )
        ).scalars().all()
    )
    mfa_ok = sum(1 for u in rows if getattr(u, "mfa_enrolled", False))
    missing_mfa = [u.email for u in rows if not getattr(u, "mfa_enrolled", False)]
    return {
        "summary": (
            f"권한자 {len(rows)} (ADMIN/REVIEWER) · MFA 등록 {mfa_ok} / 미등록 {len(missing_mfa)}"
        ),
        "records": [
            {
                "email": u.email,
                "name": u.name,
                "role": u.role.value,
                "mfa_enrolled": bool(getattr(u, "mfa_enrolled", False)),
                "last_login_at": u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None,
            }
            for u in rows
        ],
        "missing_mfa": missing_mfa,  # 심사 시 우선 시정 대상
    }


async def _access_control_policies(db: AsyncSession, **_: Any) -> dict:
    # 접근통제 관련 정책 — name/description에 키워드 매칭. 간단한 휴리스틱.
    rows = list((await db.execute(select(Policy).where(Policy.enabled.is_(True)))).scalars().all())
    keywords = ("접근", "access", "auth", "rbac", "권한", "iam")

    def is_access(p: Policy) -> bool:
        blob = " ".join(filter(None, [(p.name or ""), (p.description or "")])).lower()
        return any(k in blob for k in keywords)

    matched = [p for p in rows if is_access(p)]
    return {
        "summary": f"활성 접근통제 정책 {len(matched)}건 (전체 활성 {len(rows)})",
        "records": [
            {"name": p.name, "engine": getattr(p, "engine", "builtin"), "description": p.description}
            for p in matched
        ],
    }


async def _audit_log_recent(db: AsyncSession, *, since: datetime, **_: Any) -> dict:
    count = (
        await db.execute(
            select(func.count(AccessAuditLog.id)).where(AccessAuditLog.created_at >= since)
        )
    ).scalar_one()
    sample = list(
        (
            await db.execute(
                select(AccessAuditLog)
                .where(AccessAuditLog.created_at >= since)
                .order_by(AccessAuditLog.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
    )
    return {
        "summary": f"기간 내 audit 이벤트 {int(count or 0)}건 (sample 최대 20건 첨부)",
        "records": [
            {
                "id": e.id,
                "request_id": e.request_id,
                "event": e.event.value,
                "actor": e.actor,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in sample
        ],
    }


async def _vulnerability_handling(db: AsyncSession, **_: Any) -> dict:
    total = list((await db.execute(select(Finding))).scalars().all())
    by_status: Counter = Counter(f.status.value for f in total)
    open_critical = sum(
        1 for f in total
        if f.severity == Severity.CRITICAL and f.status in (FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS)
    )
    open_high = sum(
        1 for f in total
        if f.severity == Severity.HIGH and f.status in (FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS)
    )
    fixed = by_status.get(FindingStatus.FIXED.value, 0)
    rate = (fixed / len(total) * 100) if total else 0.0
    return {
        "summary": (
            f"총 finding {len(total)} · 상태분포 {dict(by_status)} · "
            f"잔여 critical {open_critical} · 잔여 high {open_high} · 해결률 {rate:.1f}%"
        ),
        "records": [],  # 본문은 risk_assessment와 중복되니 records 생략
    }


async def _incident_response(db: AsyncSession, **_: Any) -> dict:
    rows = list(
        (
            await db.execute(
                select(Finding).where(Finding.severity.in_([Severity.CRITICAL, Severity.HIGH]))
            )
        ).scalars().all()
    )
    triaged = sum(1 for f in rows if f.status == FindingStatus.TRIAGED)
    in_prog = sum(1 for f in rows if f.status == FindingStatus.IN_PROGRESS)
    fixed = sum(1 for f in rows if f.status == FindingStatus.FIXED)
    return {
        "summary": (
            f"critical+high finding {len(rows)} · triaged {triaged} · in_progress {in_prog} · fixed {fixed}"
        ),
        "records": [],
    }


async def _production_assets(db: AsyncSession, **_: Any) -> dict:
    rows = list(
        (
            await db.execute(
                select(Asset).where(Asset.environment.in_(["production", "prod"]))
            )
        ).scalars().all()
    )
    no_owner = [a.name for a in rows if not a.owner]
    return {
        "summary": (
            f"production 자산 {len(rows)}건 · 담당자 미지정 {len(no_owner)}건"
        ),
        "records": [
            {"id": a.id, "name": a.name, "owner": a.owner, "uri": a.uri, "type": a.asset_type.value}
            for a in rows
        ],
        "missing_owner": no_owner,
    }


_COLLECTORS = {
    "policies_catalog": _policies_catalog,
    "assets_inventory": _assets_inventory,
    "risk_assessment": _risk_assessment,
    "access_request_lifecycle": _access_request_lifecycle,
    "privileged_users": _privileged_users,
    "access_control_policies": _access_control_policies,
    "audit_log_recent": _audit_log_recent,
    "vulnerability_handling": _vulnerability_handling,
    "incident_response": _incident_response,
    "production_assets": _production_assets,
}


async def build_package(db: AsyncSession, *, days: int = 90) -> dict:
    """ISMS-P 통제 10개 + 각 통제별 evidence."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    sections: list[dict] = []
    for ctrl in ISMS_P_CONTROLS:
        collector = _COLLECTORS.get(ctrl.evidence_source)
        if collector is None:
            sections.append({
                "control": _control_to_dict(ctrl),
                "evidence": {"summary": "(collector 미구현)", "records": []},
            })
            continue
        try:
            evidence = await collector(db, since=since)
        except Exception as exc:  # 한 통제 실패가 패키지 전체를 막지 않게
            evidence = {"summary": f"(수집 실패: {exc})", "records": []}
        sections.append({"control": _control_to_dict(ctrl), "evidence": evidence})

    return {
        "framework": "ISMS-P",
        "version": "v0.3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": days,
        "since": since.isoformat(),
        "sections": sections,
    }


def _control_to_dict(c: ISMSControl) -> dict:
    return {
        "code": c.code,
        "name_ko": c.name_ko,
        "summary_ko": c.summary_ko,
        "kisa_ref": c.kisa_ref,
        "evidence_source": c.evidence_source,
    }


def render_markdown(package: dict) -> str:
    """JSON 패키지를 사람이 읽는 markdown으로. 심사원에게 그대로 전달 가능."""
    lines: list[str] = []
    lines.append(f"# {package['framework']} 인증 심사 증빙 패키지")
    lines.append("")
    lines.append(f"_생성 시각: {package['generated_at']} · 집계 기간: 최근 {package['period_days']}일_")
    lines.append("")
    lines.append(
        "이 문서는 Mond가 운영 중 수집·기록하는 데이터를 ISMS-P 핵심 통제 10개에 자동 매핑한 자료입니다. "
        "심사 시점의 실 데이터를 그대로 반영하므로 별도 정리 작업 없이 1차 증빙으로 활용할 수 있습니다."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    for sec in package["sections"]:
        c = sec["control"]
        e = sec["evidence"]
        lines.append(f"## {c['code']} · {c['name_ko']}")
        lines.append("")
        lines.append(f"_{c['kisa_ref']}_")
        lines.append("")
        lines.append(c["summary_ko"])
        lines.append("")
        lines.append(f"**집계 요약**: {e.get('summary', '—')}")
        lines.append("")
        recs = e.get("records") or []
        if recs:
            keys = list(recs[0].keys())
            lines.append("| " + " | ".join(keys) + " |")
            lines.append("|" + "|".join(["---"] * len(keys)) + "|")
            for r in recs[:30]:
                row = " | ".join(
                    str(r.get(k) if r.get(k) is not None else "—").replace("|", "\\|") for k in keys
                )
                lines.append(f"| {row} |")
            if len(recs) > 30:
                lines.append("")
                lines.append(f"_(전체 {len(recs)}건 중 상위 30건만 표시)_")
            lines.append("")
        # 보조 필드 (missing_mfa, missing_owner 등) — 시정 대상 강조
        for k in ("missing_mfa", "missing_owner"):
            extras = e.get(k)
            if extras:
                lines.append(f"**시정 권고 — {k}:** {', '.join(str(x) for x in extras[:20])}")
                if len(extras) > 20:
                    lines.append(f"_(총 {len(extras)}건)_")
                lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("_본 문서는 Mond가 자동 생성한 1차 증빙입니다. 최종 심사 자료로 사용하기 전 보안담당자가 검토하세요._")
    return "\n".join(lines)
