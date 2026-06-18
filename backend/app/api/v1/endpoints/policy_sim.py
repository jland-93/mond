"""
🌙 Policy Simulator 엔드포인트
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user
from app.core.database import get_db
from app.models.user import User
from app.services.policy_sim import SimFinding, simulate

router = APIRouter()


class SimulateFindingIn(BaseModel):
    rule_id: str
    severity: str
    scanner: str | None = None


class SimulateRequest(BaseModel):
    findings: list[SimulateFindingIn] = Field(default_factory=list)


@router.post("/simulate")
async def simulate_endpoint(
    payload: SimulateRequest,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """가상의 finding 모음을 받아 모든 활성 정책 게이트 통과 여부 시뮬레이션."""
    results = await simulate(
        db,
        [SimFinding(rule_id=f.rule_id, severity=f.severity, scanner=f.scanner) for f in payload.findings],
    )
    blocked_total = sum(1 for r in results if r.blocked)
    return {
        "results": [asdict(r) for r in results],
        "summary": {
            "total_policies": len(results),
            "blocked": blocked_total,
            "passed": len(results) - blocked_total,
        },
    }
