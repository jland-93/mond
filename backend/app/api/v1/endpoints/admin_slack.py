"""조직 Slack 채널 매핑 — Admin 전용."""

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.models.slack import SlackPurpose
from app.models.user import Role
from app.services import slack as slack_service

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


class ChannelUpsert(BaseModel):
    purpose: SlackPurpose
    webhook_url: str
    label: str | None = None
    enabled: bool = True


@router.get("")
async def list_channels(db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = await slack_service.list_channels(db)
    return [
        {
            "id": r.id,
            "purpose": r.purpose.value,
            "label": r.label,
            "enabled": r.enabled,
            # webhook_url은 마스킹 — UI에 raw 노출 금지
            "webhook_masked": _mask(r.webhook_url),
        }
        for r in rows
    ]


@router.put("")
async def upsert(payload: ChannelUpsert, db: AsyncSession = Depends(get_db)) -> dict:
    if not payload.webhook_url.startswith("https://hooks.slack.com/"):
        raise HTTPException(status_code=400, detail="Slack incoming webhook URL이어야 합니다")
    ch = await slack_service.upsert_channel(
        db,
        payload.purpose,
        payload.webhook_url,
        payload.label,
        payload.enabled,
    )
    return {
        "id": ch.id,
        "purpose": ch.purpose.value,
        "label": ch.label,
        "enabled": ch.enabled,
        "webhook_masked": _mask(ch.webhook_url),
    }


@router.delete("/{purpose}")
async def delete(purpose: SlackPurpose, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await slack_service.delete_channel(db, purpose)
    if not ok:
        raise HTTPException(status_code=404, detail="해당 purpose 채널 없음")
    return {"deleted": purpose.value}


@router.post("/test")
async def test(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """저장된 채널(purpose)로 또는 임시 webhook_url로 테스트 메시지 전송."""
    text = payload.get("text") or "Mond 테스트 메시지 — 채널 연결 확인용"
    if payload.get("purpose"):
        try:
            purpose = SlackPurpose(payload["purpose"])
        except ValueError:
            raise HTTPException(status_code=400, detail="unknown purpose")
        url = await slack_service.resolve_webhook(db, purpose)
        if not url:
            raise HTTPException(status_code=400, detail="해당 purpose에 등록된 채널이 없습니다")
    elif payload.get("webhook_url"):
        url = payload["webhook_url"]
        if not url.startswith("https://hooks.slack.com/"):
            raise HTTPException(status_code=400, detail="Slack incoming webhook URL이어야 합니다")
    else:
        raise HTTPException(status_code=400, detail="purpose 또는 webhook_url 중 하나 필요")

    ok, err = await slack_service.test_send(url, text)
    return {"ok": ok, "error": err}


def _mask(url: str) -> str:
    if len(url) <= 30:
        return "…"
    return url[:30] + "…" + url[-4:]
