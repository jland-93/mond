"""
Scan 서비스 — 어댑터 호출 + Finding 저장
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
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
    """스캔을 시작한다.

    기본은 인라인 동기 실행 — 빠르게 끝나는 단일 자산 스캔에 적합.
    `SCAN_QUEUE_ENABLED=true`면 PENDING 상태로 Scan만 만들고 Celery 큐에 enqueue,
    worker가 비동기로 실행. 운영의 대용량/장시간 스캔에서 backend 타임아웃 회피.
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

    # Celery 모드 — PENDING으로 생성하고 worker에 위임.
    if settings.SCAN_QUEUE_ENABLED:
        scan = Scan(
            asset_id=asset.id,
            scanner=scanner_name,
            trigger=trigger,
            status=ScanStatus.PENDING,
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        # task import는 여기서만 — celery_app이 backend 부팅 시 매번 로드되지 않도록.
        from app.tasks.scan_tasks import run_scan as run_scan_task

        run_scan_task.delay(scan.id)
        return scan

    # 인라인 모드 — 그대로 실행.
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


async def execute_pending_scan(scan_id: int) -> dict:
    """worker entrypoint — PENDING Scan 하나를 받아 실제 스캔을 끝까지 진행.

    호출 측에서 새 DB session을 열어 사용한다 (각 task는 독립).
    반환은 task 결과로 쓸 요약 dict (Celery task가 그대로 반환).
    """
    async with AsyncSessionLocal() as db:
        scan = (await db.execute(select(Scan).where(Scan.id == scan_id))).scalar_one_or_none()
        if scan is None:
            return {"scan_id": scan_id, "status": "not_found"}
        asset = (await db.execute(select(Asset).where(Asset.id == scan.asset_id))).scalar_one_or_none()
        if asset is None:
            scan.status = ScanStatus.FAILED
            scan.error_message = "asset not found"
            await db.commit()
            return {"scan_id": scan_id, "status": "failed", "error": "asset not found"}

        adapter = get_scanner(scan.scanner)
        if adapter is None:
            scan.status = ScanStatus.FAILED
            scan.error_message = f"Unknown scanner: {scan.scanner}"
            await db.commit()
            return {"scan_id": scan_id, "status": "failed", "error": scan.error_message}

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(scan)

        start = time.monotonic()
        try:
            result = await adapter.scan(asset)
        except Exception as exc:
            logger.exception("scanner_unexpected_error", scanner=scan.scanner, asset_id=asset.id)
            scan.status = ScanStatus.FAILED
            scan.error_message = str(exc)
            scan.finished_at = datetime.now(timezone.utc)
            scan.duration_ms = int((time.monotonic() - start) * 1000)
            await db.commit()
            return {"scan_id": scan_id, "status": "failed", "error": str(exc)}

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
                scanner=scan.scanner,
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

        asset.last_scanned_at_str = scan.finished_at.isoformat() if scan.finished_at else None
        await asset_service.refresh_open_findings_count(db, asset.id)

        for f in created_findings:
            try:
                await notify.notify_finding(f)
            except Exception as exc:
                logger.warning("notify_failed", finding_id=f.id, error=str(exc))

        return {
            "scan_id": scan_id,
            "status": scan.status.value,
            "findings": saved,
            "duration_ms": scan.duration_ms,
        }
