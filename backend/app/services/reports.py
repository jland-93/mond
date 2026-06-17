"""
🌙 Reports — SBOM (lightweight) + Compliance 리포트
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.regulations import SCENARIOS, regulation_dict
from app.models.asset import Asset
from app.models.finding import Finding, FindingStatus, Severity


async def lightweight_sbom(db: AsyncSession, asset_id: int) -> dict:
    """완전한 SBOM은 아니지만, 대상 자산의 발견사항을 묶어 CycloneDX-유사 JSON 생성."""
    asset = (await db.execute(select(Asset).where(Asset.id == asset_id))).scalar_one_or_none()
    if not asset:
        return {"error": "asset_not_found"}

    findings = list(
        (
            await db.execute(select(Finding).where(Finding.asset_id == asset_id))
        ).scalars().all()
    )

    return {
        "$schema": "https://cyclonedx.org/docs/1.5/json/",
        "bomFormat": "CycloneDX-lite",
        "specVersion": "1.5",
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "tool": "mond",
            "asset": {
                "id": asset.id,
                "name": asset.name,
                "type": asset.asset_type.value,
                "uri": asset.uri,
                "owner": asset.owner,
                "environment": asset.environment,
            },
        },
        "vulnerabilities": [
            {
                "id": f.fingerprint,
                "ruleId": f.rule_id,
                "title": f.title,
                "severity": f.severity.value,
                "scanner": f.scanner,
                "location": f.location,
                "status": f.status.value,
                "references": f.references,
            }
            for f in findings
        ],
    }


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
    md.append(f"_Generated at {report['generated_at']} by 🌙 Mond_")
    return "\n".join(md)
