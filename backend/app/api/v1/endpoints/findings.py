"""
🌙 Finding 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import FindingStatus, Severity
from app.schemas.common import Page
from app.schemas.finding import FindingRead, FindingUpdate
from app.services import finding as finding_service

router = APIRouter()


@router.get("", response_model=Page[FindingRead])
async def list_findings(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: Severity | None = Query(None),
    status: FindingStatus | None = Query(None),
    asset_id: int | None = Query(None),
    scanner: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Page[FindingRead]:
    items, total = await finding_service.list_findings(
        db,
        limit=limit,
        offset=offset,
        severity=severity,
        status=status,
        asset_id=asset_id,
        scanner=scanner,
    )
    return Page(
        items=[FindingRead.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: int, db: AsyncSession = Depends(get_db)) -> FindingRead:
    f = await finding_service.get_finding(db, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingRead.model_validate(f)


@router.patch("/{finding_id}", response_model=FindingRead)
async def update_finding(
    finding_id: int,
    payload: FindingUpdate,
    db: AsyncSession = Depends(get_db),
) -> FindingRead:
    f = await finding_service.get_finding(db, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    updated = await finding_service.update_finding(db, f, payload)
    return FindingRead.model_validate(updated)
