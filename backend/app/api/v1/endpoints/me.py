"""
'내 페이지' 엔드포인트 — 본인 자산 / 자기 발견사항 / 권한 요청 / 만료 임박 집계 + 갱신.

권한: 인증된 사용자만. 본인 데이터만 노출 (다른 사용자 데이터 leak 금지).
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.iam import AccessRequest
from app.models.user import User
from app.schemas.iam import AccessRequestCreate, AccessRequestRead
from app.services import iam as iam_service
from app.services import me as me_service

router = APIRouter()


@router.get("/overview")
async def overview(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await me_service.get_me_overview(db, user)


@router.post("/access-requests/{request_id}/renew", response_model=AccessRequestRead)
async def renew_access(
    request_id: int,
    payload: dict = Body(default={}),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessRequestRead:
    """만료 임박/만료된 본인 권한을 같은 identity/permission으로 다시 요청.

    이전 요청과 동일한 (identity, permission) 페어로 새 AccessRequest 생성.
    AI 1차 + 사람 검토 흐름은 평소와 동일.
    """
    src = (await db.execute(select(AccessRequest).where(AccessRequest.id == request_id))).scalar_one_or_none()
    if src is None:
        raise HTTPException(status_code=404, detail="원본 권한 요청을 찾을 수 없습니다")
    if src.requester != user.email:
        raise HTTPException(status_code=403, detail="본인 권한만 갱신할 수 있습니다")

    new_reason = (payload or {}).get("reason") or f"갱신 — 원본 #{src.id}: {src.reason}"
    duration = (payload or {}).get("duration_hours", src.duration_hours)

    create = AccessRequestCreate(
        requester=user.email,
        reason=new_reason,
        target_identity_id=src.target_identity_id,
        permission_id=src.permission_id,
        duration_hours=duration,
    )
    try:
        new_req = await iam_service.create_request(db, create)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AccessRequestRead.model_validate(new_req)
