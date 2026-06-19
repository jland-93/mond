"""
'내 페이지' 엔드포인트 — 본인 자산 / 자기 발견사항 / 권한 요청 / 만료 임박 집계 + 갱신.

권한: 인증된 사용자만. 본인 데이터만 노출 (다른 사용자 데이터 leak 금지).
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.iam import AccessRequest
from app.models.user import User
from app.models.user_slack import UserSlackPreference
from app.schemas.iam import AccessRequestCreate, AccessRequestRead
from app.services import iam as iam_service
from app.services import me as me_service
from app.services import slack as slack_service

router = APIRouter()


class SlackPrefIn(BaseModel):
    slack_dm_webhook_url: str | None = None
    slack_user_id: str | None = None
    notify_finding: bool = True


def _mask(url: str | None) -> str | None:
    if not url:
        return None
    if len(url) <= 30:
        return "…"
    return url[:30] + "…" + url[-4:]


@router.get("/slack-preference")
async def get_slack_pref(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    pref = (await db.execute(
        select(UserSlackPreference).where(UserSlackPreference.user_id == user.id)
    )).scalar_one_or_none()
    if pref is None:
        return {"configured": False, "notify_finding": True}
    return {
        "configured": True,
        "webhook_masked": _mask(pref.slack_dm_webhook_url),
        "slack_user_id": pref.slack_user_id,
        "notify_finding": pref.notify_finding,
    }


@router.put("/slack-preference")
async def put_slack_pref(
    payload: SlackPrefIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payload.slack_dm_webhook_url and not payload.slack_dm_webhook_url.startswith("https://hooks.slack.com/"):
        raise HTTPException(status_code=400, detail="Slack incoming webhook URL이어야 합니다")
    if payload.slack_user_id and not payload.slack_user_id.startswith(("U", "W")):
        raise HTTPException(status_code=400, detail="Slack user ID는 U.. 또는 W..로 시작합니다")

    pref = (await db.execute(
        select(UserSlackPreference).where(UserSlackPreference.user_id == user.id)
    )).scalar_one_or_none()
    if pref is None:
        pref = UserSlackPreference(user_id=user.id)
        db.add(pref)
    pref.slack_dm_webhook_url = payload.slack_dm_webhook_url or None
    pref.slack_user_id = payload.slack_user_id or None
    pref.notify_finding = payload.notify_finding
    await db.commit()
    await db.refresh(pref)
    return {
        "configured": True,
        "webhook_masked": _mask(pref.slack_dm_webhook_url),
        "slack_user_id": pref.slack_user_id,
        "notify_finding": pref.notify_finding,
    }


@router.delete("/slack-preference")
async def delete_slack_pref(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    pref = (await db.execute(
        select(UserSlackPreference).where(UserSlackPreference.user_id == user.id)
    )).scalar_one_or_none()
    if pref is None:
        return {"deleted": False}
    await db.delete(pref)
    await db.commit()
    return {"deleted": True}


@router.post("/slack-preference/test")
async def test_slack_pref(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    pref = (await db.execute(
        select(UserSlackPreference).where(UserSlackPreference.user_id == user.id)
    )).scalar_one_or_none()
    if pref is None or not pref.slack_dm_webhook_url:
        raise HTTPException(status_code=400, detail="등록된 webhook URL이 없습니다")
    text = f"Mond — {user.email} 본인 DM 테스트"
    ok, err = await slack_service.test_send(pref.slack_dm_webhook_url, text)
    return {"ok": ok, "error": err}


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
