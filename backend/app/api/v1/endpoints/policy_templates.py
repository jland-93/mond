"""
정책 템플릿 카탈로그 — 한국·글로벌 규제 매핑된 정책을 한 번에 install

GET  /policy/templates                       — 전체 카탈로그
GET  /policy/templates/frameworks            — 프레임워크 목록 (필터 칩)
POST /policy/templates/install {names: [..]} — 선택 템플릿을 Policy로 일괄 추가 (ADMIN)
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.data.policy_templates import FRAMEWORKS, TEMPLATES, list_templates
from app.models.policy import Policy
from app.models.user import Role

router = APIRouter()


@router.get("/templates")
async def get_templates(framework: str | None = Query(None)) -> list[dict]:
    """카탈로그 조회. framework 쿼리(예: 'ISMS-P')로 필터링."""
    items = list_templates(framework)
    # PolicyType enum은 JSON 직렬화 위해 value로
    return [
        {
            **t,
            "policy_type": t["policy_type"].value,
        }
        for t in items
    ]


@router.get("/templates/frameworks")
async def get_frameworks() -> list[dict]:
    return FRAMEWORKS


class InstallRequest(BaseModel):
    names: list[str] = Field(default_factory=list)


class InstallResult(BaseModel):
    installed: int
    skipped_existing: int
    names: list[str]


@router.post(
    "/templates/install",
    response_model=InstallResult,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def install_templates(
    payload: InstallRequest,
    db: AsyncSession = Depends(get_db),
) -> InstallResult:
    by_name = {t["name"]: t for t in TEMPLATES}
    chosen = [n for n in payload.names if n in by_name]

    # 이미 존재하는 정책은 skip
    existing = {
        row[0]
        for row in (await db.execute(select(Policy.name).where(Policy.name.in_(chosen)))).all()
    }
    installed = 0
    actually_added: list[str] = []
    for name in chosen:
        if name in existing:
            continue
        t = by_name[name]
        db.add(
            Policy(
                name=t["name"],
                policy_type=t["policy_type"],
                description=t["description"],
                enabled=True,
                severity_threshold=t["severity_threshold"],
                definition=t["definition"],
                compliance_refs=t["compliance_refs"],
            )
        )
        installed += 1
        actually_added.append(name)

    if installed:
        await db.commit()

    return InstallResult(
        installed=installed,
        skipped_existing=len(chosen) - installed,
        names=actually_added,
    )
