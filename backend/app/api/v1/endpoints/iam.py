"""
🌙 IAM 셀프서비스 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.iam import AccessRequestStatus
from app.schemas.iam import (
    AccessRequestCreate,
    AccessRequestRead,
    HumanDecisionIn,
    IAMIdentityRead,
    IAMSourceCreate,
    IAMSourceRead,
    PermissionRead,
)
from app.services import iam as iam_service

router = APIRouter()


# ── Sources ────────────────────────────────────────────────────────
@router.get("/sources", response_model=list[IAMSourceRead])
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[IAMSourceRead]:
    items = await iam_service.list_sources(db)
    return [IAMSourceRead.model_validate(i) for i in items]


@router.post("/sources", response_model=IAMSourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(payload: IAMSourceCreate, db: AsyncSession = Depends(get_db)) -> IAMSourceRead:
    source = await iam_service.create_source(db, payload)
    return IAMSourceRead.model_validate(source)


@router.post("/sources/{source_id}/sync")
async def sync_source(source_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    source = await iam_service.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="source not found")
    return await iam_service.sync_source(db, source)


# ── Identities / Permissions ─────────────────────────────────────────
@router.get("/identities", response_model=list[IAMIdentityRead])
async def list_identities(
    source_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[IAMIdentityRead]:
    items = await iam_service.list_identities(db, source_id)
    return [IAMIdentityRead.model_validate(i) for i in items]


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(
    source_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionRead]:
    items = await iam_service.list_permissions(db, source_id)
    return [PermissionRead.model_validate(i) for i in items]


# ── Access requests ─────────────────────────────────────────────────
@router.get("/access-requests", response_model=list[AccessRequestRead])
async def list_requests(
    status_filter: AccessRequestStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[AccessRequestRead]:
    items = await iam_service.list_requests(db, status_filter)
    return [AccessRequestRead.model_validate(i) for i in items]


@router.post("/access-requests", response_model=AccessRequestRead)
async def create_request(
    payload: AccessRequestCreate,
    db: AsyncSession = Depends(get_db),
) -> AccessRequestRead:
    try:
        req = await iam_service.create_request(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AccessRequestRead.model_validate(req)


@router.post("/access-requests/{request_id}/human-decision", response_model=AccessRequestRead)
async def human_decision(
    request_id: int,
    payload: HumanDecisionIn,
    db: AsyncSession = Depends(get_db),
) -> AccessRequestRead:
    req = await iam_service.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="request not found")
    if req.status != AccessRequestStatus.NEEDS_HUMAN_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"request is in {req.status.value} state; cannot apply human decision",
        )
    updated = await iam_service.apply_human_decision(
        db, req, approve=payload.approve, reviewer=payload.reviewer, note=payload.note
    )
    return AccessRequestRead.model_validate(updated)
