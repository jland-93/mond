"""
Policy 서비스
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate


async def list_policies(db: AsyncSession, *, enabled_only: bool = False) -> list[Policy]:
    stmt = select(Policy).order_by(Policy.name)
    if enabled_only:
        stmt = stmt.where(Policy.enabled.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def get_policy(db: AsyncSession, policy_id: int) -> Policy | None:
    return (await db.execute(select(Policy).where(Policy.id == policy_id))).scalar_one_or_none()


async def create_policy(db: AsyncSession, payload: PolicyCreate) -> Policy:
    policy = Policy(**payload.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


async def update_policy(db: AsyncSession, policy: Policy, payload: PolicyUpdate) -> Policy:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(policy, key, value)
    await db.commit()
    await db.refresh(policy)
    return policy


async def delete_policy(db: AsyncSession, policy: Policy) -> None:
    await db.delete(policy)
    await db.commit()
