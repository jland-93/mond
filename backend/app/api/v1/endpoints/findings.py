"""
Finding 엔드포인트

권한 모델:
  - GET    : 인증된 사용자 (취약점 정보 조회)
  - PATCH  : REVIEWER 이상 — 상태 변경(False Positive 등)은 보안 담당자
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.finding import Finding, FindingStatus, Severity
from app.models.user import Role, User
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
    _user: User = Depends(current_user),
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
async def get_finding(
    finding_id: int,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> FindingRead:
    f = await finding_service.get_finding(db, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingRead.model_validate(f)


@router.patch(
    "/{finding_id}",
    response_model=FindingRead,
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
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


@router.patch(
    "/bulk/status",
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
async def bulk_update_status(
    payload: dict = Body(
        ...,
        example={
            "finding_ids": [1, 2, 3],
            "status": "resolved",
        },
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """선택된 발견사항에 같은 status를 일괄 적용.

    매주 finding 100개 이상 처리하는 보안 담당자의 시간을 1/10로.
    """
    ids = payload.get("finding_ids") or []
    status_str = payload.get("status")
    if not ids or not status_str:
        raise HTTPException(status_code=400, detail="finding_ids와 status 필요")
    try:
        new_status = FindingStatus(status_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unknown status: {status_str}")

    result = await db.execute(
        sa_update(Finding).where(Finding.id.in_(ids)).values(status=new_status)
    )
    await db.commit()
    return {"updated": result.rowcount or 0, "status": new_status.value, "ids": ids}
