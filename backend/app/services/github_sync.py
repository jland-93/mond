"""
GitHub org → Mond Asset 자동 동기화

org 안의 repo 목록을 GitHub REST API로 받아와서 Mond Asset으로 등록.
이미 같은 uri로 등록된 자산은 라벨/설명만 업데이트.

호출 흐름:
  1) GET /orgs/{org}/repos (org 아니면 /users/{user}/repos로 fallback)
  2) 각 repo → Asset(uri=https://github.com/{full_name}, asset_type=REPOSITORY)
  3) labels에 language · archived · private · default_branch 기록

토큰 없이도 public repo는 보임 (rate limit 60/h). PAT 권장.
"""

from __future__ import annotations

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import Asset, AssetType

logger = structlog.get_logger(__name__)

GH_API = "https://api.github.com"
PER_PAGE = 100
MAX_PAGES = 20  # 토큰 없는 사용자가 실수로 거대 org 입력 시 보호


async def discover_repos(org: str, token: str | None) -> tuple[list[dict], str | None]:
    """org 또는 user의 repo 목록을 페이지네이션으로 모두 수집.

    Returns: (repos, error_message). error_message가 None이면 성공.
    """
    if not org:
        return [], "org 이름이 비어 있습니다"

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1) /orgs/{org} 시도
    base_org = f"{GH_API}/orgs/{org}/repos"
    base_user = f"{GH_API}/users/{org}/repos"

    repos: list[dict] = []
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        url = base_org
        used_user_fallback = False
        for page in range(1, MAX_PAGES + 1):
            resp = await client.get(url, params={"per_page": PER_PAGE, "page": page, "type": "all"})
            if resp.status_code == 404 and not used_user_fallback:
                # org가 아니라 user 계정인 경우
                used_user_fallback = True
                url = base_user
                page = 1
                resp = await client.get(url, params={"per_page": PER_PAGE, "page": page})
            if resp.status_code == 401:
                return [], "GitHub token 인증 실패 (401)"
            if resp.status_code == 403:
                return [], "GitHub API rate limit 또는 권한 부족 (403)"
            if resp.status_code == 404:
                return [], f"org/user '{org}'를 찾을 수 없습니다 (404)"
            if resp.status_code >= 400:
                return [], f"GitHub API {resp.status_code}: {resp.text[:200]}"

            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            repos.extend(batch)
            if len(batch) < PER_PAGE:
                break

    return repos, None


def _labels_from_repo(repo: dict) -> dict:
    return {
        "source": "github_sync",
        "language": repo.get("language") or "unknown",
        "default_branch": repo.get("default_branch") or "main",
        "archived": bool(repo.get("archived")),
        "private": bool(repo.get("private")),
    }


async def sync_org(
    db: AsyncSession,
    org: str,
    *,
    token: str | None,
    dry_run: bool,
    include_archived: bool = False,
) -> dict:
    """org 안의 repo들을 Asset으로 upsert.

    Returns:
      {discovered, created, updated, skipped_archived, error, repos: [...]}
    """
    repos, err = await discover_repos(org, token)
    if err:
        return {"discovered": 0, "created": 0, "updated": 0, "skipped_archived": 0, "error": err, "repos": []}

    created = 0
    updated = 0
    skipped = 0
    preview: list[dict] = []

    for r in repos:
        full_name = r.get("full_name")
        if not full_name:
            continue
        if r.get("archived") and not include_archived:
            skipped += 1
            continue

        uri = f"https://github.com/{full_name}"
        existing = (await db.execute(select(Asset).where(Asset.uri == uri))).scalar_one_or_none()
        labels = _labels_from_repo(r)
        description = (r.get("description") or "")[:1024] or None
        action = "skip"

        if existing is None:
            if not dry_run:
                db.add(
                    Asset(
                        name=full_name,
                        asset_type=AssetType.REPOSITORY,
                        uri=uri,
                        description=description,
                        labels=labels,
                    )
                )
            created += 1
            action = "create"
        else:
            # 사용자가 손으로 바꾼 owner/environment는 건드리지 않음
            changed = False
            if existing.description != description and description:
                existing.description = description
                changed = True
            # github_sync가 채운 라벨만 갱신, 사용자 라벨은 보존
            current = dict(existing.labels or {})
            for k, v in labels.items():
                if current.get(k) != v:
                    current[k] = v
                    changed = True
            if changed:
                existing.labels = current
                updated += 1
                action = "update"

        preview.append({"name": full_name, "private": labels["private"], "language": labels["language"], "action": action})

    if not dry_run:
        await db.commit()

    logger.info("github_sync_done", org=org, created=created, updated=updated, dry_run=dry_run)
    return {
        "discovered": len(repos),
        "created": created,
        "updated": updated,
        "skipped_archived": skipped,
        "error": None,
        "repos": preview[:200],  # UI 보호
    }


def status_payload() -> dict:
    """admin UI가 토큰/기본 org 설정 상태를 확인하는 용도."""
    return {
        "token_configured": bool(settings.GITHUB_TOKEN),
        "default_org": settings.GITHUB_ORG,
    }
