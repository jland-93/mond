"""
PR diff에서 의존성 변경분 추출.

흐름:
  1. GitHub PR webhook payload에서 repo + base/head sha + 변경된 파일 받기
  2. 변경된 파일 중 sbom_parser가 인식하는 ecosystem 파일만 필터
  3. base/head 각각 raw content fetch → sbom_parser.parse
  4. diff (added · removed · changed)
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services import sbom_parser

logger = get_logger(__name__)


@dataclass
class PackageDiff:
    name: str
    ecosystem: str
    before: str | None
    after: str | None

    @property
    def kind(self) -> str:
        if self.before is None:
            return "added"
        if self.after is None:
            return "removed"
        return "changed"


def diff_packages(
    before: list[sbom_parser.Package],
    after: list[sbom_parser.Package],
) -> list[PackageDiff]:
    """before/after 패키지 리스트를 (ecosystem, name) 키로 비교."""
    key = lambda p: (p.ecosystem, p.name)  # noqa: E731
    before_map = {key(p): p for p in before}
    after_map = {key(p): p for p in after}

    diffs: list[PackageDiff] = []
    for k, p in after_map.items():
        b = before_map.get(k)
        if b is None:
            diffs.append(PackageDiff(name=p.name, ecosystem=p.ecosystem, before=None, after=p.version))
        elif (b.version or "") != (p.version or ""):
            diffs.append(PackageDiff(name=p.name, ecosystem=p.ecosystem, before=b.version, after=p.version))
    for k, p in before_map.items():
        if k not in after_map:
            diffs.append(PackageDiff(name=p.name, ecosystem=p.ecosystem, before=p.version, after=None))
    return diffs


async def _fetch_raw(client: httpx.AsyncClient, url: str, token: str | None) -> str | None:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
        if r.status_code >= 400:
            return None
        return r.text
    except Exception as exc:
        logger.warning("github_fetch_failed", url=url, error=str(exc))
        return None


async def diff_for_pr(
    owner: str,
    repo: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
) -> list[PackageDiff]:
    """PR의 변경 파일을 GitHub API로 조회 후 의존성 파일만 diff."""
    token = settings.GITHUB_TOKEN
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        # PR의 변경 파일 (최대 100개)
        files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100"
        r = await client.get(files_url)
        if r.status_code >= 400:
            logger.warning("github_pr_files_failed", status=r.status_code, body=r.text[:200])
            return []
        files = r.json()

        all_diffs: list[PackageDiff] = []
        for f in files:
            path = f.get("filename") or ""
            if sbom_parser.detect_ecosystem(path) is None:
                continue
            before_raw = await _fetch_raw(
                client, f"https://raw.githubusercontent.com/{owner}/{repo}/{base_sha}/{path}", token
            )
            after_raw = await _fetch_raw(
                client, f"https://raw.githubusercontent.com/{owner}/{repo}/{head_sha}/{path}", token
            )
            before_pkgs = sbom_parser.parse(before_raw, path)[1] if before_raw else []
            after_pkgs = sbom_parser.parse(after_raw, path)[1] if after_raw else []
            all_diffs.extend(diff_packages(before_pkgs, after_pkgs))
        return all_diffs


def format_slack(owner: str, repo: str, pr_number: int, diffs: list[PackageDiff]) -> dict:
    if not diffs:
        return {"text": f"*Mond* — `{owner}/{repo}` PR #{pr_number} 의존성 변경 없음"}
    added = [d for d in diffs if d.kind == "added"]
    removed = [d for d in diffs if d.kind == "removed"]
    changed = [d for d in diffs if d.kind == "changed"]

    lines = [
        f"*Mond* — `{owner}/{repo}` PR #{pr_number}",
        f"의존성 변경: 신규 {len(added)} · 제거 {len(removed)} · 버전 변경 {len(changed)}",
    ]
    for d in added[:8]:
        lines.append(f"➕ {d.ecosystem}: `{d.name}` @{d.after}")
    if len(added) > 8:
        lines.append(f"… 외 {len(added) - 8}건")
    for d in changed[:8]:
        lines.append(f"↗ {d.ecosystem}: `{d.name}` {d.before} → {d.after}")
    if len(changed) > 8:
        lines.append(f"… 외 {len(changed) - 8}건")
    for d in removed[:8]:
        lines.append(f"➖ {d.ecosystem}: `{d.name}`")
    if len(removed) > 8:
        lines.append(f"… 외 {len(removed) - 8}건")
    return {"text": "\n".join(lines)}


def format_pr_comment(diffs: list[PackageDiff]) -> str:
    """GitHub PR comment markdown."""
    if not diffs:
        return "🌙 **Mond SBOM diff** — 의존성 변경 없음."
    added = [d for d in diffs if d.kind == "added"]
    removed = [d for d in diffs if d.kind == "removed"]
    changed = [d for d in diffs if d.kind == "changed"]
    parts = [
        "🌙 **Mond SBOM diff**",
        "",
        f"- 신규 추가: **{len(added)}**",
        f"- 제거: **{len(removed)}**",
        f"- 버전 변경: **{len(changed)}**",
    ]
    if added:
        parts += ["", "### Added", "| ecosystem | package | version |", "|---|---|---|"]
        parts += [f"| {d.ecosystem} | `{d.name}` | {d.after} |" for d in added[:40]]
    if changed:
        parts += ["", "### Changed", "| ecosystem | package | before → after |", "|---|---|---|"]
        parts += [f"| {d.ecosystem} | `{d.name}` | {d.before} → {d.after} |" for d in changed[:40]]
    if removed:
        parts += ["", "### Removed", "| ecosystem | package |", "|---|---|"]
        parts += [f"| {d.ecosystem} | `{d.name}` |" for d in removed[:40]]
    return "\n".join(parts)


async def post_pr_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
) -> bool:
    """선택적 — GITHUB_TOKEN이 있으면 PR에 comment 작성."""
    token = settings.GITHUB_TOKEN
    if not token:
        return False
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            r = await client.post(url, json={"body": body})
            if r.status_code >= 400:
                logger.warning("github_pr_comment_failed", status=r.status_code, body=r.text[:200])
                return False
            return True
    except Exception as exc:
        logger.warning("github_pr_comment_exception", error=str(exc))
        return False
