"""
🌙 Scan 서비스 — 어댑터 호출 + Finding 저장
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.asset import Asset
from app.models.finding import Severity
from app.models.scan import Scan, ScanStatus, ScanTrigger
from app.scanners.registry import get_scanner
from app.services import asset as asset_service
from app.services import finding as finding_service
from app.services import notifications as notify

logger = get_logger(__name__)


async def list_scans(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    asset_id: int | None = None,
) -> list[Scan]:
    stmt = select(Scan)
    if asset_id is not None:
        stmt = stmt.where(Scan.asset_id == asset_id)
    items = (await db.execute(stmt.order_by(Scan.id.desc()).limit(limit).offset(offset))).scalars().all()
    return list(items)


async def get_scan(db: AsyncSession, scan_id: int) -> Scan | None:
    return (await db.execute(select(Scan).where(Scan.id == scan_id))).scalar_one_or_none()


async def trigger_scan(
    db: AsyncSession,
    *,
    asset: Asset,
    scanner_name: str,
    trigger: ScanTrigger = ScanTrigger.MANUAL,
) -> Scan:
    """스캔을 동기적으로 실행한다.

    OSS MVP는 작은 환경을 가정하므로 인라인 실행으로 충분하다.
    프로덕션에서는 Celery로 옮기는 게 자연스럽다.
    """
    adapter = get_scanner(scanner_name)
    if adapter is None:
        scan = Scan(
            asset_id=asset.id,
            scanner=scanner_name,
            trigger=trigger,
            status=ScanStatus.FAILED,
            error_message=f"Unknown scanner: {scanner_name}",
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        return scan

    if not adapter.supports(asset):
        scan = Scan(
            asset_id=asset.id,
            scanner=scanner_name,
            trigger=trigger,
            status=ScanStatus.FAILED,
            error_message=(
                f"Scanner '{scanner_name}'은 자산 타입 '{asset.asset_type.value}'을 지원하지 않습니다."
            ),
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        return scan

    scan = Scan(
        asset_id=asset.id,
        scanner=scanner_name,
        trigger=trigger,
        status=ScanStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    start = time.monotonic()
    try:
        result = await adapter.scan(asset)
    except Exception as exc:  # adapter 내부에서 예상 못한 실패
        logger.exception("scanner_unexpected_error", scanner=scanner_name, asset_id=asset.id)
        scan.status = ScanStatus.FAILED
        scan.error_message = str(exc)
        scan.finished_at = datetime.now(timezone.utc)
        scan.duration_ms = int((time.monotonic() - start) * 1000)
        await db.commit()
        await db.refresh(scan)
        return scan

    saved = 0
    created_findings = []
    for raw in result.findings:
        try:
            severity = Severity(raw.severity.lower())
        except ValueError:
            severity = Severity.INFO
        finding = await finding_service.upsert_finding(
            db,
            asset_id=asset.id,
            scan_id=scan.id,
            scanner=scanner_name,
            rule_id=raw.rule_id,
            title=raw.title,
            severity=severity,
            description=raw.description,
            location=raw.location,
            references=raw.references,
            extra=raw.extra,
        )
        created_findings.append(finding)
        saved += 1

    scan.finished_at = datetime.now(timezone.utc)
    scan.duration_ms = int((time.monotonic() - start) * 1000)
    scan.findings_count = saved
    scan.raw_output = result.raw_output
    scan.status = ScanStatus.FAILED if result.error else ScanStatus.COMPLETED
    if result.error:
        scan.error_message = result.error
    await db.commit()
    await db.refresh(scan)

    asset.last_scanned_at_str = scan.finished_at.isoformat() if scan.finished_at else None
    await asset_service.refresh_open_findings_count(db, asset.id)

    # 임계치 이상의 finding을 알림 채널로 전송 (Slack/Generic webhook)
    for f in created_findings:
        try:
            await notify.notify_finding(f)
        except Exception as exc:
            logger.warning("notify_failed", finding_id=f.id, error=str(exc))

    return scan
