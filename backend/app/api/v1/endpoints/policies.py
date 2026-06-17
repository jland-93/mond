"""
🌙 Policy 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate
from app.services import policy as policy_service

router = APIRouter()


@router.get("", response_model=list[PolicyRead])
async def list_policies(
    enabled_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list[PolicyRead]:
    items = await policy_service.list_policies(db, enabled_only=enabled_only)
    return [PolicyRead.model_validate(i) for i in items]


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(payload: PolicyCreate, db: AsyncSession = Depends(get_db)) -> PolicyRead:
    policy = await policy_service.create_policy(db, payload)
    return PolicyRead.model_validate(policy)


@router.get("/{policy_id}", response_model=PolicyRead)
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)) -> PolicyRead:
    policy = await policy_service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyRead.model_validate(policy)


@router.patch("/{policy_id}", response_model=PolicyRead)
async def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
) -> PolicyRead:
    policy = await policy_service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    updated = await policy_service.update_policy(db, policy, payload)
    return PolicyRead.model_validate(updated)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db)) -> None:
    policy = await policy_service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    await policy_service.delete_policy(db, policy)
