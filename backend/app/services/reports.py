"""
Reports — SBOM (CycloneDX 1.5) + Compliance 리포트

cyclonedx_sbom
  - REPOSITORY 자산이면 GitHub default branch의 의존성 파일을 fetch해
    components[]를 채운다 (npm/pypi/go/docker). 실패하면 components는 빈 배열.
  - vulnerabilities[]는 자산의 findings를 CycloneDX 1.5 vulnerability 객체로 변환.
  - serialNumber/timestamp/tools 등 표준 metadata 충족.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.data.regulations import SCENARIOS, regulation_dict
from app.models.asset import Asset, AssetType
from app.models.finding import Finding, FindingStatus, Severity
from app.services import sbom_parser

logger = get_logger(__name__)

MOND_TOOL_VERSION = "0.3"

# GitHub repo에서 시도할 의존성 파일 후보. 발견되는 만큼 components에 합집합.
_DEFAULT_DEP_FILES = (
    "package.json",
    "package-lock.json",
    "requirements.txt",
    "go.mod",
    "Dockerfile",
)


def _purl(eco: str, name: str, version: str | None) -> str:
    """ecosystem → CycloneDX/SPDX 표준 Package URL.

    spec: https://github.com/package-url/purl-spec
      npm:    pkg:npm/<name>@<version>
      pypi:   pkg:pypi/<name>@<version>
      go:     pkg:golang/<module>@<version>
      docker: pkg:oci/<image>@<tag>
    """
    scheme = {"npm": "npm", "pypi": "pypi", "go": "golang", "docker": "oci"}.get(eco, eco)
    base = f"pkg:{scheme}/{name}"
    return f"{base}@{version}" if version else base


def _bom_ref(eco: str, name: str, version: str | None) -> str:
    """components와 vulnerabilities를 잇는 참조. purl 기반이지만 짧게."""
    v = version or "unspecified"
    return f"{eco}:{name}@{v}"


def _to_component(pkg: sbom_parser.Package) -> dict:
    return {
        "type": "library",
        "bom-ref": _bom_ref(pkg.ecosystem, pkg.name, pkg.version),
        "name": pkg.name,
        "version": pkg.version or "",
        "purl": _purl(pkg.ecosystem, pkg.name, pkg.version),
        "properties": [
            {"name": "mond:ecosystem", "value": pkg.ecosystem},
            *([{"name": "mond:source", "value": pkg.source_file}] if pkg.source_file else []),
            *([{"name": "mond:dev", "value": "true"}] if pkg.dev else []),
        ],
    }


def _to_vulnerability(f: Finding) -> dict:
    """Finding → CycloneDX 1.5 vulnerability."""
    method = "OWASP" if f.scanner in {"semgrep", "nuclei"} else "CVSSv3"
    return {
        "bom-ref": f.fingerprint,
        "id": f.rule_id or f.fingerprint,
        "source": {"name": f.scanner},
        "ratings": [
            {"severity": f.severity.value, "method": method, "score": 0.0}
        ],
        "description": f.title,
        "advisories": [
            {"url": ref} for ref in (f.references or []) if isinstance(ref, str)
        ],
        "properties": [
            {"name": "mond:status", "value": f.status.value},
            *([{"name": "mond:location", "value": f.location}] if f.location else []),
        ],
    }


def _parse_github_uri(uri: str | None) -> tuple[str, str] | None:
    """https://github.com/<owner>/<repo>(.git)? 에서 owner/repo 추출."""
    if not uri:
        return None
    u = uri.rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    if "github.com/" not in u:
        return None
    tail = u.split("github.com/", 1)[1]
    parts = tail.split("/")
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


async def _fetch_repo_components(asset: Asset) -> list[dict]:
    """REPOSITORY 자산이면 default branch의 의존성 파일들에서 components 합집합."""
    if asset.asset_type != AssetType.REPOSITORY:
        return []
    parsed = _parse_github_uri(asset.uri)
    if parsed is None:
        return []
    owner, repo = parsed

    token = settings.GITHUB_TOKEN
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # default branch 조회 — 실패하면 main fallback
    branch = "main"
    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if r.status_code < 400:
                branch = (r.json().get("default_branch") or "main")
    except Exception as exc:
        logger.info("sbom_default_branch_lookup_failed", error=str(exc))

    components: list[dict] = []
    seen_refs: set[str] = set()
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        for fname in _DEFAULT_DEP_FILES:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{fname}"
            try:
                r = await client.get(url, follow_redirects=True)
                if r.status_code >= 400:
                    continue
                _, pkgs = sbom_parser.parse(r.text, fname)
            except Exception as exc:
                logger.info("sbom_fetch_failed", file=fname, error=str(exc))
                continue
            for p in pkgs:
                comp = _to_component(p)
                ref = comp["bom-ref"]
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                components.append(comp)
    return components


async def cyclonedx_sbom(db: AsyncSession, asset_id: int) -> dict:
    """자산 1건의 CycloneDX 1.5 BOM. components(의존성) + vulnerabilities(findings)."""
    asset = (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()
    if not asset:
        return {"error": "asset_not_found"}

    findings = list(
        (await db.execute(select(Finding).where(Finding.asset_id == asset_id))).scalars().all()
    )
    components = await _fetch_repo_components(asset)

    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [
                {"vendor": "Mond", "name": "mond", "version": MOND_TOOL_VERSION}
            ],
            "component": {
                "type": "application" if asset.asset_type != AssetType.REPOSITORY else "library",
                "bom-ref": f"mond:asset:{asset.id}",
                "name": asset.name,
                "properties": [
                    {"name": "mond:asset_type", "value": asset.asset_type.value},
                    *([{"name": "mond:uri", "value": asset.uri}] if asset.uri else []),
                    *([{"name": "mond:owner", "value": asset.owner}] if asset.owner else []),
                    *([{"name": "mond:environment", "value": asset.environment}] if asset.environment else []),
                ],
            },
        },
        "components": components,
        "vulnerabilities": [_to_vulnerability(f) for f in findings],
    }


# 하위 호환 alias — 호출처가 점진 이행할 때까지 유지.
lightweight_sbom = cyclonedx_sbom


async def compliance_report(
    db: AsyncSession,
    scenario_id: str,
    lang: str = "ko",
) -> dict:
    """시나리오의 모든 규제에 대해 (1) 의무 목록 (2) 현재 시스템 발견사항 통계."""
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return {"error": "scenario_not_found"}

    open_critical = (
        await db.execute(
            select(Finding).where(
                Finding.severity == Severity.CRITICAL,
                Finding.status.in_(
                    [FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]
                ),
            )
        )
    ).scalars().all()
    open_high = (
        await db.execute(
            select(Finding).where(
                Finding.severity == Severity.HIGH,
                Finding.status.in_(
                    [FindingStatus.NEW, FindingStatus.TRIAGED, FindingStatus.IN_PROGRESS]
                ),
            )
        )
    ).scalars().all()

    regulation_sections = []
    for code in scenario.applicable:
        reg = regulation_dict(code, lang)
        if reg is None:
            continue
        regulation_sections.append(reg)

    return {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name_ko if lang == "ko" else scenario.name_en,
            "description": scenario.description_ko if lang == "ko" else scenario.description_en,
        },
        "regulations": regulation_sections,
        "current_state": {
            "open_critical": len(open_critical),
            "open_high": len(open_high),
            "ready_for_audit": len(open_critical) == 0 and len(open_high) == 0,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language": lang,
    }


def compliance_report_markdown(report: dict) -> str:
    """compliance_report 결과를 마크다운 문자열로 직렬화."""
    if report.get("error"):
        return f"# Compliance Report\n\nError: {report['error']}"
    sc = report["scenario"]
    md = [f"# Compliance Report — {sc['name']}", "", sc["description"], ""]
    cs = report["current_state"]
    md += [
        "## 현재 상태",
        f"- Open CRITICAL: **{cs['open_critical']}**",
        f"- Open HIGH: **{cs['open_high']}**",
        f"- Audit-ready: **{'✅' if cs['ready_for_audit'] else '❌'}**",
        "",
        "## 적용 규제",
        "",
    ]
    for reg in report["regulations"]:
        md.append(f"### {reg['code']} — {reg['name']}")
        md.append(f"_관할: {reg['jurisdiction']}_")
        md.append("")
        md.append(reg["summary"])
        md.append("")
        if reg.get("timings_detail"):
            md.append("**적용 시점**")
            for t in reg["timings_detail"]:
                md.append(f"- {t['label']}")
            md.append("")
        md.append("**필수 의무**")
        for ob in reg.get("obligations", []):
            md.append(f"- {ob}")
        md.append("")
        if reg.get("references"):
            md.append("**참고**")
            for ref in reg["references"]:
                md.append(f"- {ref}")
            md.append("")
    md.append(f"_Generated at {report['generated_at']} by Mond_")
    return "\n".join(md)
