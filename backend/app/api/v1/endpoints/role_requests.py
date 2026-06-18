"""
🌙 역할 변경 셀프서비스 요청 + ADMIN 검토

  - POST   /me/role-request          — 임직원이 자기 role 변경 요청
  - GET    /me/role-request          — 자기 요청 이력
  - GET    /admin/role-requests       — ADMIN: 모든 요청 목록 (필터: status)
  - POST   /admin/role-requests/{id}/decision — ADMIN: 승인/거부

AI 1차 검토:
  - VIEWER → EMPLOYEE 강등 또는 평행 이동 : auto_approve
  - EMPLOYEE → REVIEWER 승급             : needs_human_review
  - 무엇이든 ADMIN으로 승급              : needs_human_review (자기 자신을 ADMIN으로 못 함)
  - REVIEWER/ADMIN → 낮은 role 강등      : auto_approve (스스로 권한 내려놓는 것)

(현재는 휴리스틱만. Claude 호출은 다음 PR로 미룸.)
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.role_request import RoleChangeRequest, RoleRequestStatus
from app.models.user import Role, User

router = APIRouter()


# ── 휴리스틱 평가 ─────────────────────────────────────────────────
def _evaluate(from_role: Role, to_role: Role) -> dict:
    rank = {Role.VIEWER: 1, Role.EMPLOYEE: 2, Role.REVIEWER: 3, Role.ADMIN: 4}
    delta = rank[to_role] - rank[from_role]
    if to_role == Role.ADMIN:
        return {"decision": "needs_human_review", "risk": "high",
                "reason": "ADMIN 승급은 보안 담당자 검토 필요"}
    if delta > 0:
        return {"decision": "needs_human_review", "risk": "medium",
                "reason": f"{from_role.value} → {to_role.value} 승급은 검토 필요"}
    if delta == 0:
        return {"decision": "auto_approve", "risk": "low",
                "reason": "동일 role — 변경 없음"}
    return {"decision": "auto_approve", "risk": "low",
            "reason": "강등은 스스로 권한 내려놓는 것이므로 자동 승인"}


# ── 스키마 ────────────────────────────────────────────────────────
class RoleRequestIn(BaseModel):
    to_role: Role
    reason: str = Field(min_length=10, max_length=2000)


class RoleRequestRead(BaseModel):
    id: int
    requester_email: str
    from_role: Role
    to_role: Role
    reason: str
    status: RoleRequestStatus
    ai_decision: dict
    reviewer_email: str | None = None
    review_note: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class DecisionIn(BaseModel):
    approve: bool
    note: str = Field(default="", max_length=2000)


def _to_read(row: RoleChangeRequest, requester_email: str) -> RoleRequestRead:
    return RoleRequestRead(
        id=row.id,
        requester_email=requester_email,
        from_role=row.from_role,
        to_role=row.to_role,
        reason=row.reason,
        status=row.status,
        ai_decision=row.ai_decision or {},
        reviewer_email=row.reviewer_email,
        review_note=row.review_note,
        created_at=row.created_at,
        decided_at=row.decided_at,
    )


# ── 직원 self-service ──────────────────────────────────────────
@router.post("/me/role-request", response_model=RoleRequestRead)
async def request_role(
    payload: RoleRequestIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> RoleRequestRead:
    if payload.to_role == user.role:
        raise HTTPException(status_code=400, detail="이미 같은 role입니다.")

    decision = _evaluate(user.role, payload.to_role)
    req = RoleChangeRequest(
        requester_id=user.id,
        from_role=user.role,
        to_role=payload.to_role,
        reason=payload.reason.strip(),
        ai_decision=decision,
        status=(
            RoleRequestStatus.AI_AUTO_APPROVED
            if decision["decision"] == "auto_approve"
            else RoleRequestStatus.NEEDS_HUMAN_REVIEW
        ),
    )
    db.add(req)

    # auto_approve이면 즉시 role 적용
    if decision["decision"] == "auto_approve":
        user.role = payload.to_role
        req.reviewer_email = "ai"
        req.review_note = decision["reason"]
        req.decided_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(req)
    return _to_read(req, user.email)


@router.get("/me/role-request", response_model=list[RoleRequestRead])
async def my_requests(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RoleRequestRead]:
    rows = (
        await db.execute(
            select(RoleChangeRequest)
            .where(RoleChangeRequest.requester_id == user.id)
            .order_by(RoleChangeRequest.created_at.desc())
        )
    ).scalars().all()
    return [_to_read(r, user.email) for r in rows]


# ── ADMIN 검토 ───────────────────────────────────────────────
@router.get(
    "/admin/role-requests",
    response_model=list[RoleRequestRead],
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def list_all(
    status_filter: RoleRequestStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[RoleRequestRead]:
    stmt = select(RoleChangeRequest, User).join(User, User.id == RoleChangeRequest.requester_id)
    if status_filter:
        stmt = stmt.where(RoleChangeRequest.status == status_filter)
    stmt = stmt.order_by(RoleChangeRequest.created_at.desc())
    rows = (await db.execute(stmt)).all()
    return [_to_read(r, u.email) for r, u in rows]


@router.post(
    "/admin/role-requests/{request_id}/decision",
    response_model=RoleRequestRead,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def decide(
    request_id: int,
    payload: DecisionIn,
    reviewer: User = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> RoleRequestRead:
    row = (
        await db.execute(select(RoleChangeRequest).where(RoleChangeRequest.id == request_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="request not found")
    if row.status not in {RoleRequestStatus.NEEDS_HUMAN_REVIEW, RoleRequestStatus.PENDING_AI_REVIEW}:
        raise HTTPException(status_code=400, detail=f"already decided: {row.status.value}")

    requester = (
        await db.execute(select(User).where(User.id == row.requester_id))
    ).scalar_one_or_none()
    if requester is None:
        raise HTTPException(status_code=404, detail="requester not found")

    # 자기 자신을 ADMIN에서 강등하려는 모든 경로 차단 (lock-out 방지)
    if requester.id == reviewer.id and row.to_role != Role.ADMIN and requester.role == Role.ADMIN:
        raise HTTPException(status_code=400, detail="ADMIN은 자기 자신의 강등을 승인할 수 없습니다.")

    row.reviewer_email = reviewer.email
    row.review_note = payload.note
    row.decided_at = datetime.now(timezone.utc)
    if payload.approve:
        row.status = RoleRequestStatus.APPROVED
        requester.role = row.to_role
    else:
        row.status = RoleRequestStatus.DENIED

    await db.commit()
    await db.refresh(row)
    return _to_read(row, requester.email)
