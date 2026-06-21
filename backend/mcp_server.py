"""
Mond MCP Server

Claude Desktop / Claude Code에서 Mond를 직접 다룰 수 있게 한다.

전송 방식:
  1) stdio  — `python -m mcp_server` (또는 docker exec). 권장.
  2) HTTP+SSE — FastAPI의 /mcp 마운트는 mcp 패키지의 type 검사 호환 문제로 실험적.

도구 시그너처는 FastMCP 1.12+의 type 검사 호환을 위해 union(X | None)을 피하고
기본값 sentinel(빈 문자열 / 0 / None 인자 후처리)을 사용한다.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, List

from mcp.server.fastmcp import FastMCP

from app.ai import insights as ai_insights
from app.core.database import AsyncSessionLocal, engine
from app.data.regulations import REGULATIONS, SCENARIOS, regulation_dict, scenario_dict
from app.models import Base
from app.models.finding import Severity
from app.models.scan import ScanTrigger
from app.scanners.registry import list_scanners
from app.services import ai as ai_service
from app.services import asset as asset_service
from app.services import finding as finding_service
from app.services import scan as scan_service


mcp = FastMCP("mond")
# FastMCP 기본 streamable_http_path는 '/mcp', sse_path는 '/sse'다.
# Mond는 FastAPI에서 app.mount('/mcp', mcp_app)로 한 번 더 prefix를 붙이므로
# 외부 노출 path가 '/mcp/mcp'·'/mcp/sse'로 이중이 된다. 안쪽을 '/'로 풀어
# 외부 path를 '/mcp'·'/mcp/sse'로 단순화한다.
mcp.settings.streamable_http_path = "/"
mcp.settings.sse_path = "/sse"


@asynccontextmanager
async def _db():
    async with AsyncSessionLocal() as session:
        yield session


@mcp.tool(description="Mond에 등록된 자산(보호 대상) 목록을 반환한다. q는 부분일치 검색.")
async def list_assets(limit: int = 50, q: str = "") -> List[dict]:
    async with _db() as db:
        items, _ = await asset_service.list_assets(db, limit=limit, q=q or None)
        return [
            {
                "id": a.id,
                "name": a.name,
                "asset_type": a.asset_type.value,
                "uri": a.uri,
                "environment": a.environment,
                "owner": a.owner,
                "open_findings_count": a.open_findings_count,
            }
            for a in items
        ]


@mcp.tool(description="자산 ID로 단일 자산을 조회한다.")
async def get_asset(asset_id: int) -> dict:
    async with _db() as db:
        a = await asset_service.get_asset(db, asset_id)
        if not a:
            return {"error": "not_found"}
        return {
            "id": a.id,
            "name": a.name,
            "asset_type": a.asset_type.value,
            "uri": a.uri,
            "description": a.description,
            "labels": a.labels,
            "environment": a.environment,
            "owner": a.owner,
            "open_findings_count": a.open_findings_count,
        }


@mcp.tool(description="발견사항 목록을 severity(빈문자열 ''=전체)/asset_id(0=전체)/scanner로 필터.")
async def list_findings(
    limit: int = 50,
    severity: str = "",
    asset_id: int = 0,
    scanner: str = "",
) -> List[dict]:
    sev: Any = None
    if severity:
        try:
            sev = Severity(severity.lower())
        except ValueError:
            sev = None
    async with _db() as db:
        items, _ = await finding_service.list_findings(
            db,
            limit=limit,
            severity=sev,
            asset_id=asset_id if asset_id else None,
            scanner=scanner or None,
        )
        return [
            {
                "id": f.id,
                "asset_id": f.asset_id,
                "title": f.title,
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "status": f.status.value,
                "scanner": f.scanner,
                "location": f.location,
            }
            for f in items
        ]


@mcp.tool(description="자산에 대해 스캔을 실행한다 (trivy / semgrep / nuclei).")
async def trigger_scan(asset_id: int, scanner: str = "trivy") -> dict:
    async with _db() as db:
        asset = await asset_service.get_asset(db, asset_id)
        if not asset:
            return {"error": "asset_not_found"}
        s = await scan_service.trigger_scan(
            db, asset=asset, scanner_name=scanner, trigger=ScanTrigger.AI
        )
        return {
            "scan_id": s.id,
            "status": s.status.value,
            "findings_count": s.findings_count,
            "scanner": s.scanner,
        }


@mcp.tool(description="발견사항을 Claude로 triage 한다 (severity 재평가 + remediation 제안).")
async def triage_finding(finding_id: int, deep: bool = False) -> dict:
    async with _db() as db:
        f = await finding_service.get_finding(db, finding_id)
        if not f:
            return {"error": "finding_not_found"}
        insight = await ai_service.analyze_and_store(db, f, deep=deep)
        return {
            "id": insight.id,
            "model": insight.model,
            "summary": insight.summary,
            "recommended_severity": insight.recommended_severity,
            "confidence": insight.confidence,
            "remediation": insight.remediation,
        }


@mcp.tool(description="등록된 스캐너 어댑터 목록.")
async def list_scanners_tool() -> List[dict]:
    return list_scanners()


@mcp.tool(description="자연어 쿼리를 의도(scan/list_findings/explain/unknown)로 분류.")
async def ask(query: str) -> dict:
    return await ai_insights.route_query(query)


@mcp.tool(description="사업 시나리오 ID(예: kr-personal-data)에 해당하는 규제 목록.")
async def regulations_for(scenario_id: str, lang: str = "ko") -> dict:
    result = scenario_dict(scenario_id, lang)
    if not result:
        return {"error": "scenario_not_found", "available": list(SCENARIOS.keys())}
    return result


@mcp.tool(description="규제 코드(K-PIPA, GDPR 등) 단건 상세.")
async def regulation_detail(code: str, lang: str = "ko") -> dict:
    r = regulation_dict(code.upper(), lang)
    if not r:
        return {"error": "regulation_not_found", "available": list(REGULATIONS.keys())}
    return r


async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def run_stdio() -> None:
    """stdio 모드 진입점. Claude Desktop/Code MCP 설정에서 호출."""
    asyncio.run(_ensure_schema())
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
