"""감사 로그 검색 — ADMIN 전용.

access_audit_logs 테이블을 시계열로 조회. 필터: 기간 · actor · event · request_id.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.core.database import get_db
from app.models.iam import AccessAuditLog, AccessRequest, AuditEvent
from app.models.user import Role

router = APIRouter(dependencies=[Depends(require_role(Role.ADMIN))])


@router.get("")
async def list_audit_log(
    start: datetime | None = Query(None, description="ISO 8601, created_at >= start"),
    end: datetime | None = Query(None, description="ISO 8601, created_at < end"),
    actor: str | None = Query(None, description="actor email substring (case-insensitive)"),
    event: AuditEvent | None = Query(None),
    request_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(AccessAuditLog).order_by(AccessAuditLog.created_at.desc())
    if start:
        stmt = stmt.where(AccessAuditLog.created_at >= start)
    if end:
        stmt = stmt.where(AccessAuditLog.created_at < end)
    if actor:
        stmt = stmt.where(AccessAuditLog.actor.ilike(f"%{actor}%"))
    if event:
        stmt = stmt.where(AccessAuditLog.event == event)
    if request_id:
        stmt = stmt.where(AccessAuditLog.request_id == request_id)

    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()

    # request_id별 requester/permission/identity 1회 fetch로 노출
    req_ids = sorted({r.request_id for r in rows})
    req_map: dict[int, dict] = {}
    if req_ids:
        reqs = (
            (await db.execute(select(AccessRequest).where(AccessRequest.id.in_(req_ids))))
            .scalars()
            .all()
        )
        for r in reqs:
            req_map[r.id] = {
                "requester": r.requester,
                "identity_id": r.target_identity_id,
                "permission_id": r.permission_id,
                "status": r.status.value,
            }

    return {
        "items": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "event": r.event.value,
                "actor": r.actor,
                "detail": r.detail,
                "created_at": r.created_at.isoformat(),
                "request": req_map.get(r.request_id),
            }
            for r in rows
        ],
        "limit": limit,
        "offset": offset,
        "count": len(rows),
    }
