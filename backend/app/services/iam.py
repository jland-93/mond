"""
🌙 IAM 셀프서비스 서비스 — Source import / Identities / Permissions / AccessRequest workflow
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.iam import ai_review
from app.iam import providers
from app.models.iam import (
    AccessAuditLog,
    AccessRequest,
    AccessRequestStatus,
    AuditEvent,
    IAMIdentity,
    IAMSource,
    Permission,
)
from app.schemas.iam import AccessRequestCreate, IAMSourceCreate

logger = get_logger(__name__)


async def _log(
    db: AsyncSession,
    *,
    request_id: int,
    event: AuditEvent,
    actor: str,
    detail: dict | None = None,
) -> None:
    db.add(
        AccessAuditLog(
            request_id=request_id,
            event=event,
            actor=actor,
            detail=detail or {},
        )
    )


# ── Source ──────────────────────────────────────────────────────
async def list_sources(db: AsyncSession) -> list[IAMSource]:
    return list((await db.execute(select(IAMSource).order_by(IAMSource.id))).scalars().all())


async def get_source(db: AsyncSession, source_id: int) -> IAMSource | None:
    return (await db.execute(select(IAMSource).where(IAMSource.id == source_id))).scalar_one_or_none()


async def create_source(db: AsyncSession, payload: IAMSourceCreate) -> IAMSource:
    source = IAMSource(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def sync_source(db: AsyncSession, source: IAMSource) -> dict:
    """프로바이더에서 identities + permissions를 가져와 DB에 upsert(name 기준 단순 교체)."""
    result = providers.fetch_for(source)

    # 단순 교체 — MVP. 차후 diff 기반 동기화로 발전.
    await db.execute(IAMIdentity.__table__.delete().where(IAMIdentity.source_id == source.id))
    await db.execute(Permission.__table__.delete().where(Permission.source_id == source.id))

    for ident in result.identities:
        db.add(
            IAMIdentity(
                source_id=source.id,
                identity_type=ident.identity_type,
                name=ident.name,
                external_id=ident.external_id,
                attributes=ident.attributes or {},
            )
        )
    for perm in result.permissions:
        db.add(
            Permission(
                source_id=source.id,
                name=perm.name,
                external_id=perm.external_id,
                description=perm.description,
                risk_hint=perm.risk_hint,
                attributes=perm.attributes or {},
            )
        )

    source.last_synced_at_str = datetime.now(timezone.utc).isoformat()
    await db.commit()
    return {
        "stub": result.stub,
        "error": result.error,
        "imported_identities": len(result.identities),
        "imported_permissions": len(result.permissions),
    }


# ── Identities / Permissions browse ─────────────────────────────────
async def list_identities(db: AsyncSession, source_id: int | None = None) -> list[IAMIdentity]:
    stmt = select(IAMIdentity).order_by(IAMIdentity.name)
    if source_id is not None:
        stmt = stmt.where(IAMIdentity.source_id == source_id)
    return list((await db.execute(stmt)).scalars().all())


async def list_permissions(db: AsyncSession, source_id: int | None = None) -> list[Permission]:
    stmt = select(Permission).order_by(Permission.name)
    if source_id is not None:
        stmt = stmt.where(Permission.source_id == source_id)
    return list((await db.execute(stmt)).scalars().all())


# ── AccessRequest workflow ──────────────────────────────────────────
async def list_requests(db: AsyncSession, status: AccessRequestStatus | None = None) -> list[AccessRequest]:
    stmt = select(AccessRequest).order_by(AccessRequest.id.desc())
    if status is not None:
        stmt = stmt.where(AccessRequest.status == status)
    return list((await db.execute(stmt)).scalars().all())


async def get_request(db: AsyncSession, request_id: int) -> AccessRequest | None:
    return (
        await db.execute(select(AccessRequest).where(AccessRequest.id == request_id))
    ).scalar_one_or_none()


async def create_request(db: AsyncSession, payload: AccessRequestCreate) -> AccessRequest:
    identity = (
        await db.execute(select(IAMIdentity).where(IAMIdentity.id == payload.target_identity_id))
    ).scalar_one_or_none()
    permission = (
        await db.execute(select(Permission).where(Permission.id == payload.permission_id))
    ).scalar_one_or_none()
    if not identity or not permission:
        raise ValueError("invalid target_identity_id or permission_id")

    req = AccessRequest(
        requester=payload.requester,
        reason=payload.reason,
        duration_hours=payload.duration_hours,
        target_identity_id=payload.target_identity_id,
        permission_id=payload.permission_id,
        status=AccessRequestStatus.PENDING_AI_REVIEW,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    # AI 1차 자율 판단 즉시 실행
    review_result = await ai_review.review(
        db,
        requester=req.requester,
        reason=req.reason,
        duration_hours=req.duration_hours,
        identity=identity,
        permission=permission,
    )
    req.ai_decision = asdict(review_result)
    await _log(db, request_id=req.id, event=AuditEvent.AI_DECIDED, actor="ai", detail=req.ai_decision)

    if review_result.decision == "auto_approve":
        req.status = AccessRequestStatus.AI_AUTO_APPROVED
        # 자동 승인이면 즉시 grant 진행
        await _grant(db, req, identity, permission)
    elif review_result.decision == "deny":
        req.status = AccessRequestStatus.HUMAN_DENIED  # AI가 명백히 거부 → 최종 거부
        req.human_decision = {"reviewer": "ai", "approve": False, "note": review_result.reason}
    else:
        req.status = AccessRequestStatus.NEEDS_HUMAN_REVIEW

    await db.commit()
    await db.refresh(req)
    return req


async def apply_human_decision(
    db: AsyncSession,
    req: AccessRequest,
    *,
    approve: bool,
    reviewer: str,
    note: str | None = None,
) -> AccessRequest:
    req.human_decision = {"approve": approve, "reviewer": reviewer, "note": note or ""}
    await _log(
        db,
        request_id=req.id,
        event=AuditEvent.HUMAN_DECIDED,
        actor=reviewer,
        detail=req.human_decision,
    )
    if not approve:
        req.status = AccessRequestStatus.HUMAN_DENIED
        await db.commit()
        await db.refresh(req)
        return req

    req.status = AccessRequestStatus.HUMAN_APPROVED
    identity = (
        await db.execute(select(IAMIdentity).where(IAMIdentity.id == req.target_identity_id))
    ).scalar_one()
    permission = (
        await db.execute(select(Permission).where(Permission.id == req.permission_id))
    ).scalar_one()
    await _grant(db, req, identity, permission)
    await db.commit()
    await db.refresh(req)
    return req


async def _grant(
    db: AsyncSession,
    req: AccessRequest,
    identity: IAMIdentity,
    permission: Permission,
) -> None:
    source = (
        await db.execute(select(IAMSource).where(IAMSource.id == identity.source_id))
    ).scalar_one()
    result = providers.attach_for(source, identity, permission)
    granted_at = datetime.now(timezone.utc)
    req.grant_result = {
        "success": result.success,
        "detail": result.detail,
        "granted_at": granted_at.isoformat(),
    }
    if result.success:
        req.status = AccessRequestStatus.GRANTED
        # duration_hours가 지정되어 있으면 만료 시각 설정 → 백그라운드 sweep이 자동 회수
        if req.duration_hours and req.duration_hours > 0:
            req.expires_at = granted_at + timedelta(hours=req.duration_hours)
        await _log(
            db,
            request_id=req.id,
            event=AuditEvent.GRANTED,
            actor="system",
            detail={"expires_at": req.expires_at.isoformat() if req.expires_at else None},
        )
    else:
        req.status = AccessRequestStatus.GRANT_FAILED
        await _log(db, request_id=req.id, event=AuditEvent.GRANT_FAILED, actor="system", detail=result.detail)


# ── 회수(revoke) ────────────────────────────────────────────────────
async def _revoke_one(
    db: AsyncSession,
    req: AccessRequest,
    *,
    triggered_by: str,
    event: AuditEvent = AuditEvent.EXPIRED_REVOKED,
) -> None:
    """granted 상태인 요청을 외부에 detach + DB 마킹 + audit."""
    identity = (
        await db.execute(select(IAMIdentity).where(IAMIdentity.id == req.target_identity_id))
    ).scalar_one()
    permission = (
        await db.execute(select(Permission).where(Permission.id == req.permission_id))
    ).scalar_one()
    source = (
        await db.execute(select(IAMSource).where(IAMSource.id == identity.source_id))
    ).scalar_one()

    result = providers.detach_for(source, identity, permission)
    now = datetime.now(timezone.utc)
    req.revoked_at = now
    req.revoke_result = {
        "success": result.success,
        "detail": result.detail,
        "revoked_at": now.isoformat(),
        "triggered_by": triggered_by,
    }
    if result.success:
        req.status = AccessRequestStatus.EXPIRED_REVOKED
        await _log(db, request_id=req.id, event=event, actor=triggered_by, detail=result.detail)
    else:
        req.status = AccessRequestStatus.REVOKE_FAILED
        await _log(
            db,
            request_id=req.id,
            event=AuditEvent.REVOKE_FAILED,
            actor=triggered_by,
            detail=result.detail,
        )


async def manual_revoke(db: AsyncSession, req: AccessRequest, actor: str) -> AccessRequest:
    if req.status != AccessRequestStatus.GRANTED:
        raise ValueError(f"only granted requests can be revoked; current={req.status.value}")
    await _revoke_one(db, req, triggered_by=actor, event=AuditEvent.MANUAL_REVOKED)
    await db.commit()
    await db.refresh(req)
    return req


async def revoke_expired(db: AsyncSession) -> int:
    """만료된 granted 요청을 모두 회수한다. 회수 처리한 건수 반환."""
    now = datetime.now(timezone.utc)
    stmt = select(AccessRequest).where(
        AccessRequest.status == AccessRequestStatus.GRANTED,
        AccessRequest.expires_at.is_not(None),
        AccessRequest.expires_at <= now,
    )
    expired = list((await db.execute(stmt)).scalars().all())
    for req in expired:
        try:
            await _revoke_one(db, req, triggered_by="expiry-sweeper", event=AuditEvent.EXPIRED_REVOKED)
        except Exception as exc:
            logger.warning("revoke_failed", request_id=req.id, error=str(exc))
    if expired:
        await db.commit()
    return len(expired)


async def expiry_sweep_loop(interval_seconds: int = 300) -> None:
    """백그라운드: 주기적으로 만료 회수 sweep."""
    import asyncio

    while True:
        try:
            async with AsyncSessionLocal() as session:
                n = await revoke_expired(session)
                if n:
                    logger.info("expiry_sweep", revoked=n)
        except Exception as exc:
            logger.warning("expiry_sweep_failed", error=str(exc))
        await asyncio.sleep(interval_seconds)


async def list_audit(db: AsyncSession, request_id: int) -> list[AccessAuditLog]:
    stmt = (
        select(AccessAuditLog)
        .where(AccessAuditLog.request_id == request_id)
        .order_by(AccessAuditLog.id)
    )
    return list((await db.execute(stmt)).scalars().all())
