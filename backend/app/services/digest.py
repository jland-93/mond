"""
어제 일어난 일을 Slack에 한 카드로 묶어 전송.
보통 외부 cron(k8s CronJob 등)이 매일 한 번 endpoint를 호출한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.finding import Finding, Severity
from app.models.iam import AccessRequest, AccessRequestStatus
from app.models.scan import Scan, ScanStatus

logger = get_logger(__name__)


async def build_daily_digest(
    session: AsyncSession,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    if until is None:
        until = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if since is None:
        since = until - timedelta(days=1)

    sev_rows = (await session.execute(
        select(Finding.severity, func.count(Finding.id))
        .where(Finding.created_at >= since, Finding.created_at < until)
        .group_by(Finding.severity)
    )).all()
    by_sev = {s.value: 0 for s in Severity}
    for sev, cnt in sev_rows:
        by_sev[sev.value] = int(cnt)
    findings_total = sum(by_sev.values())

    scans_total = int((await session.execute(
        select(func.count(Scan.id)).where(Scan.created_at >= since, Scan.created_at < until)
    )).scalar_one() or 0)
    scans_failed = int((await session.execute(
        select(func.count(Scan.id)).where(
            Scan.created_at >= since,
            Scan.created_at < until,
            Scan.status == ScanStatus.FAILED,
        )
    )).scalar_one() or 0)

    req_rows = (await session.execute(
        select(AccessRequest.status, func.count(AccessRequest.id))
        .where(AccessRequest.created_at >= since, AccessRequest.created_at < until)
        .group_by(AccessRequest.status)
    )).all()
    req_count = {status.value: int(cnt) for status, cnt in req_rows}
    req_total = sum(req_count.values())
    # 승인 흐름은 단계가 여러 개라 사용자가 보는 "승인"은 셋을 합친 값.
    req_granted = (
        req_count.get(AccessRequestStatus.GRANTED.value, 0)
        + req_count.get(AccessRequestStatus.HUMAN_APPROVED.value, 0)
        + req_count.get(AccessRequestStatus.AI_AUTO_APPROVED.value, 0)
    )
    req_denied = req_count.get(AccessRequestStatus.HUMAN_DENIED.value, 0)
    req_pending = (
        req_count.get(AccessRequestStatus.PENDING_AI_REVIEW.value, 0)
        + req_count.get(AccessRequestStatus.NEEDS_HUMAN_REVIEW.value, 0)
    )

    # 만료 임박 — 향후 3일 이내 expires_at, 아직 revoke 안 됨, granted 상태.
    expiring_until = until + timedelta(days=3)
    expiring_count = int((await session.execute(
        select(func.count(AccessRequest.id)).where(
            AccessRequest.status == AccessRequestStatus.GRANTED,
            AccessRequest.revoked_at.is_(None),
            AccessRequest.expires_at.is_not(None),
            AccessRequest.expires_at <= expiring_until,
            AccessRequest.expires_at >= until,
        )
    )).scalar_one() or 0)

    return {
        "period": {"since": since.isoformat(), "until": until.isoformat()},
        "findings": {"total": findings_total, "by_severity": by_sev},
        "scans": {"total": scans_total, "failed": scans_failed},
        "access_requests": {
            "total": req_total,
            "granted": req_granted,
            "denied": req_denied,
            "pending": req_pending,
            "expiring_3d": expiring_count,
        },
    }


def format_slack_message(digest: dict) -> dict:
    f = digest["findings"]
    s = digest["scans"]
    a = digest["access_requests"]
    sev = f["by_severity"]
    day = digest["period"]["since"][:10]

    sev_line = (
        f"critical {sev.get('critical', 0)} · "
        f"high {sev.get('high', 0)} · "
        f"medium {sev.get('medium', 0)} · "
        f"low {sev.get('low', 0)} · "
        f"info {sev.get('info', 0)}"
    )

    lines = [
        f"*Mond Daily Digest* — {day}",
        "",
        f"*Findings* — 신규 {f['total']}건",
        sev_line,
        "",
        f"*Scans* — 실행 {s['total']}건, 실패 {s['failed']}건",
        f"*Access Requests* — 신규 {a['total']}건, 승인 {a['granted']}, 거부 {a['denied']}, 대기 {a['pending']}",
    ]
    if a.get("expiring_3d"):
        lines.append(f"⏰ 3일 내 만료 권한 {a['expiring_3d']}건 — /me에서 갱신 가능")
    return {"text": "\n".join(lines)}


async def send_daily_digest(
    session: AsyncSession,
    slack_webhook_url: str | None = None,
    generic_webhook_url: str | None = None,
) -> dict:
    digest = await build_daily_digest(session)

    slack_url = slack_webhook_url or settings.DIGEST_SLACK_WEBHOOK_URL or settings.SLACK_WEBHOOK_URL
    generic_url = generic_webhook_url or settings.GENERIC_WEBHOOK_URL

    sent: list[str] = []
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        if slack_url:
            try:
                await client.post(slack_url, json=format_slack_message(digest))
                sent.append("slack")
            except Exception as exc:
                logger.warning("digest_slack_failed", error=str(exc))
                errors.append(f"slack: {exc}")
        if generic_url:
            try:
                await client.post(generic_url, json={"source": "mond", "kind": "daily_digest", **digest})
                sent.append("generic")
            except Exception as exc:
                logger.warning("digest_generic_failed", error=str(exc))
                errors.append(f"generic: {exc}")

    return {"digest": digest, "sent": sent, "errors": errors}
