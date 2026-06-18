"""
IAM 셀프서비스 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.iam import AccessRequestStatus
from app.models.user import Role, User
from app.schemas.iam import (
    AccessRequestCreate,
    AccessRequestRead,
    AuditLogRead,
    HumanDecisionIn,
    IAMIdentityRead,
    IAMSourceCreate,
    IAMSourceRead,
    PermissionRead,
    RevokeRequest,
)
from app.iam.providers import get_capabilities
from app.services import iam as iam_service

router = APIRouter()


# ── Capabilities ───────────────────────────────────────────────────
@router.get("/capabilities")
async def list_capabilities() -> list[dict]:
    """각 IAM 유형의 실제 동작 가능 여부 (sync/grant/revoke + status)를 정직하게 노출.

    UI dropdown은 이 값을 받아 'Ready'/'Coming soon'/'Demo only' 배지로 표시한다.
    """
    return get_capabilities()


# ── Sources ────────────────────────────────────────────────────────
@router.get("/sources", response_model=list[IAMSourceRead])
async def list_sources(
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[IAMSourceRead]:
    items = await iam_service.list_sources(db)
    return [IAMSourceRead.model_validate(i) for i in items]


@router.post(
    "/sources",
    response_model=IAMSourceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def create_source(payload: IAMSourceCreate, db: AsyncSession = Depends(get_db)) -> IAMSourceRead:
    source = await iam_service.create_source(db, payload)
    return IAMSourceRead.model_validate(source)


@router.post(
    "/sources/{source_id}/sync",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def sync_source(source_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    source = await iam_service.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="source not found")
    return await iam_service.sync_source(db, source)


# ── Identities / Permissions ─────────────────────────────────────────
@router.get("/identities", response_model=list[IAMIdentityRead])
async def list_identities(
    source_id: int | None = Query(None),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[IAMIdentityRead]:
    items = await iam_service.list_identities(db, source_id)
    return [IAMIdentityRead.model_validate(i) for i in items]


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(
    source_id: int | None = Query(None),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionRead]:
    items = await iam_service.list_permissions(db, source_id)
    return [PermissionRead.model_validate(i) for i in items]


# ── Access requests ─────────────────────────────────────────────────
@router.get("/access-requests", response_model=list[AccessRequestRead])
async def list_requests(
    status_filter: AccessRequestStatus | None = Query(None, alias="status"),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AccessRequestRead]:
    items = await iam_service.list_requests(db, status_filter)
    return [AccessRequestRead.model_validate(i) for i in items]


@router.post("/access-requests", response_model=AccessRequestRead)
async def create_request(
    payload: AccessRequestCreate,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessRequestRead:
    try:
        req = await iam_service.create_request(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AccessRequestRead.model_validate(req)


@router.post("/access-requests/preview")
async def preview_request(
    payload: AccessRequestCreate,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """저장 없이 AI 1차 평가만 미리 보여줌 — AccessCenter UI 사전 미리보기용."""
    from app.iam import ai_review
    from app.models.iam import IAMIdentity, Permission
    from sqlalchemy import select as _select

    identity = (
        await db.execute(_select(IAMIdentity).where(IAMIdentity.id == payload.target_identity_id))
    ).scalar_one_or_none()
    permission = (
        await db.execute(_select(Permission).where(Permission.id == payload.permission_id))
    ).scalar_one_or_none()
    if identity is None or permission is None:
        raise HTTPException(status_code=400, detail="identity/permission not found")

    review = await ai_review.review(
        db,
        requester=payload.requester,
        reason=payload.reason,
        duration_hours=payload.duration_hours,
        identity=identity,
        permission=permission,
    )
    return {
        "decision": review.decision,
        "risk_level": review.risk_level,
        "reason": review.reason,
        "model": review.model,
        "confidence": review.confidence,
        "expected_status": (
            "granted" if review.decision == "auto_approve"
            else "needs_human_review" if review.decision == "needs_human"
            else "denied"
        ),
    }


@router.post(
    "/access-requests/{request_id}/human-decision",
    response_model=AccessRequestRead,
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
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


@router.post(
    "/access-requests/{request_id}/revoke",
    response_model=AccessRequestRead,
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
async def revoke_request(
    request_id: int,
    payload: RevokeRequest,
    db: AsyncSession = Depends(get_db),
) -> AccessRequestRead:
    """granted 상태의 요청을 수동 회수. 일반적으론 만료 sweep이 자동 처리."""
    req = await iam_service.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="request not found")
    try:
        updated = await iam_service.manual_revoke(db, req, actor=payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AccessRequestRead.model_validate(updated)


@router.post(
    "/access-requests/sweep-expired",
    dependencies=[Depends(require_role(Role.REVIEWER))],
)
async def sweep_expired(db: AsyncSession = Depends(get_db)) -> dict:
    """만료된 granted 요청을 즉시 모두 회수. cron 또는 수동 호출용."""
    n = await iam_service.revoke_expired(db)
    return {"revoked": n}


@router.get("/access-requests/{request_id}/audit", response_model=list[AuditLogRead])
async def get_audit(
    request_id: int,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogRead]:
    items = await iam_service.list_audit(db, request_id)
    return [AuditLogRead.model_validate(i) for i in items]
