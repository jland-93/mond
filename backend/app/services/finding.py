"""
Finding 서비스 — fingerprint 기반 dedup + 조회/상태 변경
"""

from __future__ import annotations

import hashlib

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding, FindingStatus, Severity
from app.schemas.finding import FindingUpdate


def build_fingerprint(*, scanner: str, rule_id: str, asset_id: int, location: str | None) -> str:
    """동일 스캐너 × 룰 × 자산 × 위치의 중복을 묶기 위한 안정 해시."""
    raw = f"{scanner}|{rule_id}|{asset_id}|{location or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]


async def upsert_finding(
    db: AsyncSession,
    *,
    asset_id: int,
    scan_id: int | None,
    scanner: str,
    rule_id: str,
    title: str,
    severity: Severity,
    description: str | None = None,
    location: str | None = None,
    references: list[str] | None = None,
    extra: dict | None = None,
) -> Finding:
    fingerprint = build_fingerprint(
        scanner=scanner, rule_id=rule_id, asset_id=asset_id, location=location
    )

    # PG 전용 upsert. 중복 시 최신 scan_id/severity로 갱신, status는 유지.
    stmt = (
        pg_insert(Finding)
        .values(
            asset_id=asset_id,
            scan_id=scan_id,
            rule_id=rule_id,
            title=title,
            description=description,
            severity=severity,
            scanner=scanner,
            location=location,
            references=references or [],
            extra=extra or {},
            fingerprint=fingerprint,
        )
        .on_conflict_do_update(
            index_elements=["fingerprint"],
            set_={
                "scan_id": scan_id,
                "severity": severity,
                "title": title,
                "description": description,
                "references": references or [],
                "extra": extra or {},
            },
        )
        .returning(Finding)
    )
    result = await db.execute(stmt)
    finding = result.scalar_one()
    return finding


async def list_findings(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    severity: Severity | None = None,
    status: FindingStatus | None = None,
    asset_id: int | None = None,
    scanner: str | None = None,
) -> tuple[list[Finding], int]:
    stmt = select(Finding)
    count_stmt = select(func.count(Finding.id))

    filters = []
    if severity:
        filters.append(Finding.severity == severity)
    if status:
        filters.append(Finding.status == status)
    if asset_id is not None:
        filters.append(Finding.asset_id == asset_id)
    if scanner:
        filters.append(Finding.scanner == scanner)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = (await db.execute(count_stmt)).scalar_one()
    items = (
        await db.execute(
            stmt.order_by(Finding.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return list(items), int(total)


async def get_finding(db: AsyncSession, finding_id: int) -> Finding | None:
    return (await db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()


async def update_finding(db: AsyncSession, finding: Finding, payload: FindingUpdate) -> Finding:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(finding, key, value)
    await db.commit()
    await db.refresh(finding)
    return finding
