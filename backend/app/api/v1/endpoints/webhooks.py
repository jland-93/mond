"""
Webhooks — 외부 시스템 이벤트 수신

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
from app.core.rate_limit import RateLimiter
from app.models.asset import Asset, AssetType
from app.models.scan import ScanTrigger
from app.models.user import Role
from app.models.slack import SlackPurpose
from app.models.webhook_token import WebhookToken
from app.services import sbom_diff, scan as scan_service, slack as slack_service

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


@router.post("/github", dependencies=[Depends(RateLimiter("webhook_github", 120, 60, "ip"))])
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

    # pull_request opened/synchronize → 의존성 diff + Slack + (선택) PR comment
    if x_github_event == "pull_request":
        action = payload.get("action")
        if action not in ("opened", "synchronize", "reopened"):
            return {"ignored": f"pull_request.{action}"}
        pr = payload.get("pull_request") or {}
        repo = payload.get("repository") or {}
        full_name = repo.get("full_name") or ""
        if "/" not in full_name:
            return {"ignored": "missing repository full_name"}
        owner, name = full_name.split("/", 1)
        pr_number = pr.get("number")
        base_sha = (pr.get("base") or {}).get("sha")
        head_sha = (pr.get("head") or {}).get("sha")
        if not (pr_number and base_sha and head_sha):
            return {"ignored": "missing PR sha"}

        diffs = await sbom_diff.diff_for_pr(owner, name, pr_number, base_sha, head_sha)
        commented = False
        if diffs:
            commented = await sbom_diff.post_pr_comment(
                owner, name, pr_number, sbom_diff.format_pr_comment(diffs)
            )
            # Slack 알림 (FINDING purpose)
            slack_url = await slack_service.resolve_webhook(db, SlackPurpose.FINDING)
            if slack_url:
                import httpx

                msg = sbom_diff.format_slack(owner, name, pr_number, diffs)
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(slack_url, json=msg)
                except Exception as exc:
                    logger.warning("sbom_diff_slack_failed", error=str(exc))
        return {
            "kind": "pull_request",
            "repository": full_name,
            "pr": pr_number,
            "diff_count": len(diffs),
            "pr_comment_posted": commented,
        }

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


@router.post("/personal", dependencies=[Depends(RateLimiter("webhook_personal", 30, 60, "ip"))])
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
