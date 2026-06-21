"""
ISMS-P 인증 심사 증빙 패키지 — Admin 전용.

GET /admin/audit-package/isms-p
  format=json (기본) — 구조화된 통제별 dict
  format=markdown  — 심사원에게 그대로 전달 가능한 텍스트
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.models.user import Role
from app.services import audit_package as audit_package_service

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


@router.get("/isms-p")
async def isms_p_package(
    days: int = Query(90, ge=1, le=365, description="집계 기간(일). 권한 audit log 등 시계열 평가에 사용"),
    format: str = Query("json", regex="^(json|markdown)$"),
    db: AsyncSession = Depends(get_db),
):
    pkg = await audit_package_service.build_package(db, days=days)
    if format == "markdown":
        return PlainTextResponse(
            content=audit_package_service.render_markdown(pkg),
            media_type="text/markdown; charset=utf-8",
        )
    return pkg
