"""
PR Bot — push 스캔 결과를 PR 코멘트로.

흐름:
  1) GitHub push webhook → scan_service.trigger_scan (인라인) 완료
  2) head_sha → /repos/{owner}/{repo}/commits/{sha}/pulls 로 open PR 검색
  3) finding 요약 + (AI 활성 시) top critical 1건 AI triage 1-liner를 markdown으로
  4) post_pr_comment로 작성 (SBOM diff와 같은 라우트 재사용)

운영:
  - GITHUB_TOKEN 필요. 없으면 silent skip.
  - inline scan 완료 후에만 동작. Celery 비동기 큐는 worker가 별도로 트리거해야 함 (v0.4).
  - 자산이 GitHub repo 자산일 때만 동작.
"""

from __future__ import annotations

from collections import Counter

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import is_enabled as ai_enabled
from app.ai.insights import analyze_finding
from app.core.config import settings
from app.models.asset import Asset, AssetType
from app.models.finding import Finding, Severity
from app.models.scan import Scan
from app.services import sbom_diff as sbom_diff_service

logger = structlog.get_logger(__name__)

SEVERITY_RANK = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.INFO: 0,
}


async def find_open_prs(owner: str, repo: str, head_sha: str) -> list[int]:
    """given head sha에 열린 PR 번호 목록 (보통 0~1건)."""
    token = settings.GITHUB_TOKEN
    if not token:
        return []
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{head_sha}/pulls"
    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            r = await client.get(url)
            if r.status_code >= 400:
                logger.info("pr_bot_lookup_failed", status=r.status_code, sha=head_sha[:8])
                return []
            data = r.json()
            return [
                int(item["number"])
                for item in data
                if isinstance(item, dict) and item.get("state") == "open" and item.get("number")
            ]
    except Exception as exc:
        logger.info("pr_bot_lookup_exception", error=str(exc))
        return []


def _severity_summary(findings: list[Finding]) -> tuple[Counter, list[Finding]]:
    """severity별 카운트 + critical/high 우선 정렬 top 5."""
    counter: Counter = Counter(f.severity.value for f in findings)
    by_rank = sorted(findings, key=lambda f: -SEVERITY_RANK.get(f.severity, 0))
    return counter, by_rank[:5]


async def _ai_one_liner(db: AsyncSession, finding: Finding) -> str | None:
    """top critical에 대한 AI 1-liner. provider 없으면 None."""
    if not await ai_enabled(db):
        return None
    try:
        result = await analyze_finding(db, finding, deep=False)
        text = (result.summary or "").strip()
        if not text:
            return None
        # 1줄로 (~140자)
        first = text.splitlines()[0]
        return first[:140] + ("…" if len(first) > 140 else "")
    except Exception as exc:
        logger.info("pr_bot_ai_oneliner_failed", error=str(exc))
        return None


def format_pr_comment(
    *,
    scan: Scan,
    asset_name: str,
    findings: list[Finding],
    ai_oneliner: str | None,
) -> str:
    counter, top = _severity_summary(findings)
    total = sum(counter.values())

    parts: list[str] = []
    parts.append("## 🌙 Mond — scan summary")
    parts.append("")
    parts.append(
        f"`{asset_name}` · scanner=`{scan.scanner}` · status=`{scan.status.value}` · {scan.duration_ms or 0} ms"
    )
    if total == 0:
        parts.append("")
        parts.append("✅ No findings.")
        return "\n".join(parts)

    parts.append("")
    sev_line = " · ".join(f"{k}: **{v}**" for k, v in counter.most_common())
    parts.append(f"**{total}** finding(s) — {sev_line}")

    if top:
        parts.append("")
        parts.append("### Top findings")
        parts.append("| sev | rule | title |")
        parts.append("|---|---|---|")
        for f in top:
            title = (f.title or "").replace("|", "\\|")
            rule = (f.rule_id or "").replace("|", "\\|")
            parts.append(f"| `{f.severity.value}` | `{rule}` | {title} |")

    if ai_oneliner:
        parts.append("")
        parts.append(f"🤖 **AI triage** — {ai_oneliner}")

    parts.append("")
    parts.append("> Open Mond → Findings to see remediation guides + severity reassessment.")
    return "\n".join(parts)


async def notify_pr_for_scan(
    db: AsyncSession,
    *,
    scan: Scan,
    asset: Asset,
    repo_full_name: str,
    head_sha: str,
) -> dict:
    """scan 완료 직후 호출. 매칭 PR이 있고 GITHUB_TOKEN이 있으면 코멘트 작성."""
    if asset.asset_type != AssetType.REPOSITORY:
        return {"skipped": "asset_not_repository"}
    if "/" not in repo_full_name:
        return {"skipped": "invalid_repo"}
    if not settings.GITHUB_TOKEN:
        return {"skipped": "no_github_token"}

    owner, repo = repo_full_name.split("/", 1)
    prs = await find_open_prs(owner, repo, head_sha)
    if not prs:
        return {"skipped": "no_open_pr"}

    findings = list(
        (await db.execute(select(Finding).where(Finding.scan_id == scan.id))).scalars().all()
    )

    top_critical = next(
        (f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)),
        None,
    )
    ai_one = await _ai_one_liner(db, top_critical) if top_critical else None

    body = format_pr_comment(
        scan=scan,
        asset_name=asset.name,
        findings=findings,
        ai_oneliner=ai_one,
    )

    posted: list[int] = []
    for pr_number in prs:
        ok = await sbom_diff_service.post_pr_comment(owner, repo, pr_number, body)
        if ok:
            posted.append(pr_number)

    return {"posted_to_prs": posted, "finding_count": len(findings)}
