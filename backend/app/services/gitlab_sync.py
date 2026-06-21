"""
GitLab group/user → Mond Asset 자동 동기화

GitHub sync와 같은 모양 — group의 projects 목록을 REST API로 받아와 Asset
(REPOSITORY)으로 upsert. self-host GitLab도 `GITLAB_API_URL`로 지원.

호출 흐름:
  1) GET {api}/groups/{group}/projects?include_subgroups=true (404면 users 폴백)
  2) 각 project → Asset(uri=web_url, asset_type=REPOSITORY)
  3) labels: source / default_branch / archived / visibility / language(N/A)

인증: Personal Access Token (PRIVATE-TOKEN 헤더). 비어있으면 public만 보임.
"""

from __future__ import annotations

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import Asset, AssetType

logger = structlog.get_logger(__name__)

PER_PAGE = 100
MAX_PAGES = 20


async def discover_projects(group: str, token: str | None) -> tuple[list[dict], str | None]:
    """group(또는 user)의 projects를 페이지네이션으로 모두 수집."""
    if not group:
        return [], "group 이름이 비어 있습니다"

    api = (settings.GITLAB_API_URL or "https://gitlab.com/api/v4").rstrip("/")
    headers: dict[str, str] = {}
    if token:
        headers["PRIVATE-TOKEN"] = token

    # URL-encode 슬래시: GitLab은 'parent/sub' subgroup 경로를 지원
    g = group.replace("/", "%2F")
    url_group = f"{api}/groups/{g}/projects"
    url_user = f"{api}/users/{g}/projects"

    projects: list[dict] = []
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        url = url_group
        params_base = {"per_page": PER_PAGE, "include_subgroups": "true"}
        used_user_fallback = False
        for page in range(1, MAX_PAGES + 1):
            r = await client.get(url, params={**params_base, "page": page})
            if r.status_code == 404 and not used_user_fallback:
                used_user_fallback = True
                url = url_user
                params_base = {"per_page": PER_PAGE}
                r = await client.get(url, params={**params_base, "page": 1})
            if r.status_code == 401:
                return [], "GitLab token 인증 실패 (401)"
            if r.status_code == 403:
                return [], "GitLab API 권한 부족 (403)"
            if r.status_code == 404:
                return [], f"group/user '{group}'를 찾을 수 없습니다 (404)"
            if r.status_code >= 400:
                return [], f"GitLab API {r.status_code}: {r.text[:200]}"

            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            projects.extend(batch)
            if len(batch) < PER_PAGE:
                break

    return projects, None


def _labels_from_project(p: dict) -> dict:
    return {
        "source": "gitlab_sync",
        "default_branch": p.get("default_branch") or "main",
        "archived": bool(p.get("archived")),
        "visibility": p.get("visibility") or "unknown",  # public / internal / private
    }


async def sync_group(
    db: AsyncSession,
    group: str,
    *,
    token: str | None,
    dry_run: bool,
    include_archived: bool = False,
) -> dict:
    projects, err = await discover_projects(group, token)
    if err:
        return {"discovered": 0, "created": 0, "updated": 0, "skipped_archived": 0, "error": err, "repos": []}

    created = 0
    updated = 0
    skipped = 0
    preview: list[dict] = []

    for p in projects:
        full_path = p.get("path_with_namespace") or p.get("name")
        web_url = p.get("web_url")
        if not full_path or not web_url:
            continue
        if p.get("archived") and not include_archived:
            skipped += 1
            continue

        existing = (await db.execute(select(Asset).where(Asset.uri == web_url))).scalar_one_or_none()
        labels = _labels_from_project(p)
        description = (p.get("description") or "")[:1024] or None
        action = "skip"

        if existing is None:
            if not dry_run:
                db.add(
                    Asset(
                        name=full_path,
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
            "name": full_path,
            "visibility": labels["visibility"],
            "default_branch": labels["default_branch"],
            "action": action,
        })

    if not dry_run:
        await db.commit()

    logger.info("gitlab_sync_done", group=group, created=created, updated=updated, dry_run=dry_run)
    return {
        "discovered": len(projects),
        "created": created,
        "updated": updated,
        "skipped_archived": skipped,
        "error": None,
        "repos": preview[:200],
    }


def status_payload() -> dict:
    return {
        "token_configured": bool(settings.GITLAB_TOKEN),
        "default_group": settings.GITLAB_GROUP,
        "api_url": settings.GITLAB_API_URL or "https://gitlab.com/api/v4",
    }
