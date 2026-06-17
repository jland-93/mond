"""
🌙 Scan 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scan import ScanCreate, ScanRead
from app.services import asset as asset_service
from app.services import scan as scan_service

router = APIRouter()


@router.get("", response_model=list[ScanRead])
async def list_scans(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    asset_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[ScanRead]:
    scans = await scan_service.list_scans(db, limit=limit, offset=offset, asset_id=asset_id)
    return [ScanRead.model_validate(s) for s in scans]


@router.post("", response_model=ScanRead)
async def trigger_scan(payload: ScanCreate, db: AsyncSession = Depends(get_db)) -> ScanRead:
    asset = await asset_service.get_asset(db, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    scan = await scan_service.trigger_scan(
        db, asset=asset, scanner_name=payload.scanner, trigger=payload.trigger
    )
    return ScanRead.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)) -> ScanRead:
    scan = await scan_service.get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanRead.model_validate(scan)
