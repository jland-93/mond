"""
Bitbucket workspace → Mond Asset 자동 동기화

Bitbucket Cloud REST API v2 — workspace의 repositories를 페이지네이션으로
수집해 Asset(REPOSITORY)으로 upsert. 인증은 username + app password Basic auth
(Bitbucket Cloud의 표준).

호출 흐름:
  1) GET https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=100
     (response.next 따라 페이지 진행)
  2) 각 repo → Asset(uri=links.html.href, asset_type=REPOSITORY)
  3) labels: source / language / is_private / main_branch
"""

from __future__ import annotations

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import Asset, AssetType

logger = structlog.get_logger(__name__)

BB_API = "https://api.bitbucket.org/2.0"
PER_PAGE = 100
MAX_PAGES = 20


async def discover_repos(workspace: str, username: str | None, app_password: str | None) -> tuple[list[dict], str | None]:
    if not workspace:
        return [], "workspace 이름이 비어 있습니다"

    auth: tuple[str, str] | None = None
    if username and app_password:
        auth = (username, app_password)

    repos: list[dict] = []
    next_url: str | None = f"{BB_API}/repositories/{workspace}?pagelen={PER_PAGE}"

    async with httpx.AsyncClient(timeout=20, auth=auth) as client:
        for _ in range(MAX_PAGES):
            if not next_url:
                break
            r = await client.get(next_url, headers={"Accept": "application/json"})
            if r.status_code == 401:
                return [], "Bitbucket 인증 실패 (401) — username/app password 확인"
            if r.status_code == 403:
                return [], "Bitbucket API 권한 부족 (403)"
            if r.status_code == 404:
                return [], f"workspace '{workspace}'를 찾을 수 없습니다 (404)"
            if r.status_code >= 400:
                return [], f"Bitbucket API {r.status_code}: {r.text[:200]}"

            data = r.json()
            values = data.get("values") or []
            if not isinstance(values, list) or not values:
                break
            repos.extend(values)
            next_url = data.get("next")

    return repos, None


def _labels_from_repo(r: dict) -> dict:
    main_branch = ((r.get("mainbranch") or {}).get("name")) or "main"
    return {
        "source": "bitbucket_sync",
        "language": r.get("language") or "unknown",
        "is_private": bool(r.get("is_private")),
        "main_branch": main_branch,
    }


async def sync_workspace(
    db: AsyncSession,
    workspace: str,
    *,
    username: str | None,
    app_password: str | None,
    dry_run: bool,
) -> dict:
    repos, err = await discover_repos(workspace, username, app_password)
    if err:
        return {"discovered": 0, "created": 0, "updated": 0, "skipped_archived": 0, "error": err, "repos": []}

    created = 0
    updated = 0
    preview: list[dict] = []

    for r in repos:
        full_name = r.get("full_name")  # 'workspace/repo'
        links = (r.get("links") or {}).get("html") or {}
        web_url = links.get("href")
        if not full_name or not web_url:
            continue

        existing = (await db.execute(select(Asset).where(Asset.uri == web_url))).scalar_one_or_none()
        labels = _labels_from_repo(r)
        description = (r.get("description") or "")[:1024] or None
        action = "skip"

        if existing is None:
            if not dry_run:
                db.add(
                    Asset(
                        name=full_name,
                        asset_type=AssetType.REPOSITORY,
                        uri=web_url,
                        description=description,
                        labels=labels,
                    )
                )
            created += 1
            action = "create"
        else:
            changed = False
            if existing.description != description and description:
                existing.description = description
                changed = True
            current = dict(existing.labels or {})
            for k, v in labels.items():
                if current.get(k) != v:
                    current[k] = v
                    changed = True
            if changed:
                existing.labels = current
                updated += 1
                action = "update"

        preview.append({
            "name": full_name,
            "is_private": labels["is_private"],
            "language": labels["language"],
            "action": action,
        })

    if not dry_run:
        await db.commit()

    logger.info("bitbucket_sync_done", workspace=workspace, created=created, updated=updated, dry_run=dry_run)
    return {
        "discovered": len(repos),
        "created": created,
        "updated": updated,
        "skipped_archived": 0,  # Bitbucket API에 archived 필드 없음 (Cloud 한정)
        "error": None,
        "repos": preview[:200],
    }


def status_payload() -> dict:
    return {
        "credentials_configured": bool(settings.BITBUCKET_USERNAME and settings.BITBUCKET_APP_PASSWORD),
        "default_workspace": settings.BITBUCKET_WORKSPACE,
    }
