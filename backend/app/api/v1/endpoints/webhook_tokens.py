"""
🌙 Personal Webhook Tokens — CI/CD에서 사용자 인증 없이 Mond를 호출.

흐름:
  1) POST /webhook-tokens — 라벨과 함께 발급. raw token은 응답에 1회만 노출.
  2) GET  /webhook-tokens — 내 토큰 목록 (마스킹 + 사용 이력)
  3) DELETE /webhook-tokens/{id} — revoke (즉시 무효화)
  4) GET  /webhook-tokens/ci-snippets/github-actions?asset_id={n} — YAML 스니펫

토큰은 모두 본인 것만 보고 본인 것만 회수할 수 있다.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.asset import Asset
from app.models.user import User
from app.models.webhook_token import WebhookToken

router = APIRouter()


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _issue() -> tuple[str, str, str]:
    raw = "mond_" + secrets.token_urlsafe(32)
    return raw, _hash(raw), raw[:10]


class TokenRead(BaseModel):
    id: int
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class TokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class TokenCreateOut(TokenRead):
    raw_token: str  # 1회만 응답


@router.get("", response_model=list[TokenRead])
async def list_tokens(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TokenRead]:
    rows = (
        await db.execute(
            select(WebhookToken)
            .where(WebhookToken.user_id == user.id)
            .order_by(WebhookToken.created_at.desc())
        )
    ).scalars().all()
    return [TokenRead.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=TokenCreateOut, status_code=201)
async def create_token(
    payload: TokenCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> TokenCreateOut:
    raw, h, prefix = _issue()
    row = WebhookToken(user_id=user.id, name=payload.name, token_hash=h, token_prefix=prefix)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TokenCreateOut(
        id=row.id,
        name=row.name,
        token_prefix=row.token_prefix,
        created_at=row.created_at,
        raw_token=raw,
    )


@router.delete("/{token_id}")
async def revoke_token(
    token_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = (
        await db.execute(
            select(WebhookToken)
            .where(WebhookToken.id == token_id)
            .where(WebhookToken.user_id == user.id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="token not found")
    row.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.get("/ci-snippets/github-actions")
async def github_actions_snippet(
    asset_id: int = Query(..., description="대상 자산 ID"),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GitHub Actions step YAML 스니펫. 사용자가 자기 토큰을 직접 넣어 사용."""
    asset = (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    snippet = f"""- name: Mond — security scan trigger
  run: |
    curl -sS -X POST \\
      -H "Authorization: Bearer ${{{{ secrets.MOND_WEBHOOK_TOKEN }}}}" \\
      -H "Content-Type: application/json" \\
      -d '{{"asset_id": {asset_id}, "scanner": "trivy"}}' \\
      https://${{{{ vars.MOND_HOST }}}}/api/v1/webhooks/personal
"""
    gitlab = f"""mond_security_scan:
  stage: security
  script:
    - |
      curl -sS -X POST \\
        -H "Authorization: Bearer $MOND_WEBHOOK_TOKEN" \\
        -H "Content-Type: application/json" \\
        -d '{{"asset_id": {asset_id}, "scanner": "trivy"}}' \\
        https://$MOND_HOST/api/v1/webhooks/personal
"""
    return {
        "asset_id": asset_id,
        "asset_name": asset.name,
        "github_actions": snippet,
        "gitlab_ci": gitlab,
        "secrets_required": ["MOND_WEBHOOK_TOKEN", "MOND_HOST"],
        "note": "MOND_WEBHOOK_TOKEN은 위에서 발급한 raw 토큰을 GitHub Secrets/Vars로 등록하세요.",
    }
