"""
Reports 엔드포인트 — SBOM / Compliance

권한 모델: 인증된 사용자만 (감사·컴플라이언스 리포트는 외부 공개 금지)
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.user import User
from app.services import sbom_parser
from app.services.reports import (
    compliance_report,
    compliance_report_markdown,
    lightweight_sbom,
)

router = APIRouter()


@router.post("/sbom/parse")
async def sbom_parse(
    payload: dict = Body(
        ...,
        example={
            "filename": "package.json",
            "content": "{...}",
        },
    ),
    _user: User = Depends(current_user),
) -> dict:
    """의존성 파일 내용을 받아 ecosystem 감지 + 패키지 리스트 반환.

    지원 파일:
      - package.json / package-lock.json (npm)
      - requirements.txt (pypi)
      - go.mod (Go modules)
      - Dockerfile (base images)
    """
    filename = payload.get("filename") or ""
    content = payload.get("content") or ""
    if not filename or not content:
        raise HTTPException(status_code=400, detail="filename · content 모두 필요")
    eco, pkgs = sbom_parser.parse(content, filename)
    if eco is None:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 — package.json / package-lock.json / requirements.txt / go.mod / Dockerfile",
        )
    return {
        "filename": filename,
        "ecosystem": eco,
        "count": len(pkgs),
        "packages": [
            {
                "name": p.name,
                "version": p.version,
                "ecosystem": p.ecosystem,
                "dev": p.dev,
            }
            for p in pkgs
        ],
    }


@router.get("/sbom")
async def sbom(
    asset_id: int = Query(..., description="대상 자산 ID"),
    _user: User = Depends(current_user),
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
    _user: User = Depends(current_user),
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
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    result = await compliance_report(db, scenario, lang)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return compliance_report_markdown(result)
