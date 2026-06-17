"""
🌙 Reports 엔드포인트 — SBOM / Compliance
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.reports import (
    compliance_report,
    compliance_report_markdown,
    lightweight_sbom,
)

router = APIRouter()


@router.get("/sbom")
async def sbom(
    asset_id: int = Query(..., description="대상 자산 ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """CycloneDX-lite JSON 형식의 SBOM 다운로드."""
    result = await lightweight_sbom(db, asset_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/compliance")
async def compliance(
    scenario: str = Query(..., description="시나리오 ID (예: kr-personal-data)"),
    lang: str = Query("ko", pattern="^(ko|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await compliance_report(db, scenario, lang)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/compliance/markdown", response_class=PlainTextResponse)
async def compliance_md(
    scenario: str = Query(...),
    lang: str = Query("ko", pattern="^(ko|en)$"),
    db: AsyncSession = Depends(get_db),
) -> str:
    result = await compliance_report(db, scenario, lang)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return compliance_report_markdown(result)
