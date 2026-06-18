"""
🌙 Webhooks — 외부 시스템 이벤트 수신

지원:
  - GitHub `push` 이벤트 → 해당 레포 자산을 찾아 자동 스캔(기본 trivy)
  - Generic JSON push → 임의 자산 ID로 스캔 트리거 (EMPLOYEE 이상 인증 필요)

GitHub의 X-Hub-Signature-256은 GITHUB_WEBHOOK_SECRET이 설정되어 있을 때 검증한다.
운영 환경(ENVIRONMENT=production)에서 secret이 미설정이면 요청 자체를 거부 (fail-closed).
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.asset import Asset, AssetType
from app.models.scan import ScanTrigger
from app.models.user import Role
from app.models.webhook_token import WebhookToken
from app.services import scan as scan_service

router = APIRouter()
logger = get_logger(__name__)


def _verify_github(signature: str | None, body: bytes) -> bool:
    """GitHub HMAC 검증.

    secret 미설정 + production 환경 → fail-closed (요청 거부).
    secret 미설정 + 비-production 환경 → 검증 생략 (개발 편의).
    """
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        if settings.ENVIRONMENT.lower() == "production":
            logger.error("github_webhook_secret_required_in_production")
            return False
        logger.warning("github_webhook_signature_skip_dev_only")
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GitHub push 이벤트 → 매칭 자산이 있으면 trivy 스캔 자동 트리거."""
    body = await request.body()
    if not _verify_github(x_hub_signature_256, body):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    if x_github_event != "push":
        return {"ignored": x_github_event}

    repo = payload.get("repository", {})
    html_url = repo.get("html_url") or repo.get("url")
    ssh_url = repo.get("ssh_url")

    if not html_url:
        return {"ignored": "missing repository url"}

    # URI 또는 매칭 URL 기준 자산 검색
    stmt = select(Asset).where(
        Asset.asset_type == AssetType.REPOSITORY,
        (Asset.uri == html_url) | (Asset.uri == ssh_url),
    )
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if not asset:
        logger.info("webhook_no_matching_asset", url=html_url)
        return {"matched": False, "repository": html_url}

    scan = await scan_service.trigger_scan(
        db,
        asset=asset,
        scanner_name="trivy",
        trigger=ScanTrigger.WEBHOOK,
    )
    return {
        "matched": True,
        "asset_id": asset.id,
        "scan_id": scan.id,
        "status": scan.status.value,
    }


@router.post("/personal")
async def personal_webhook(
    request: Request,
    payload: dict = Body(...),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """CI/CD에서 Bearer 토큰으로 호출. user 세션 불필요.

    Authorization: Bearer mond_xxx
    Body: {"asset_id": <int>, "scanner": "trivy"|"semgrep"|"nuclei"}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    raw = authorization[7:].strip()
    if not raw.startswith("mond_"):
        raise HTTPException(status_code=401, detail="invalid token format")
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    row = (
        await db.execute(
            select(WebhookToken)
            .where(WebhookToken.token_hash == token_hash)
            .where(WebhookToken.revoked_at.is_(None))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="token revoked or unknown")

    asset_id = payload.get("asset_id")
    scanner = payload.get("scanner", "trivy")
    if not isinstance(asset_id, int):
        raise HTTPException(status_code=400, detail="asset_id (int) required")

    asset = (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")

    row.last_used_at = datetime.now(timezone.utc)
    scan = await scan_service.trigger_scan(
        db, asset=asset, scanner_name=scanner, trigger=ScanTrigger.WEBHOOK
    )
    await db.commit()
    return {"scan_id": scan.id, "status": scan.status.value, "token": row.token_prefix + "•••"}


@router.post(
    "/generic",
    dependencies=[Depends(require_role(Role.EMPLOYEE))],
)
async def generic_webhook(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """사내 CI/스크립트 통합용 — 인증된 직원만 호출. asset_id + scanner만 들어 있으면 스캔 시작."""
    asset_id = payload.get("asset_id")
    scanner = payload.get("scanner", "trivy")
    if not isinstance(asset_id, int):
        raise HTTPException(status_code=400, detail="asset_id (int) required")

    asset = (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="asset not found")

    scan = await scan_service.trigger_scan(
        db, asset=asset, scanner_name=scanner, trigger=ScanTrigger.WEBHOOK
    )
    return {"scan_id": scan.id, "status": scan.status.value}
