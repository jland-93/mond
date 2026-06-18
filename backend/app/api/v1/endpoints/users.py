"""
🌙 Users 관리 엔드포인트 — ADMIN 전용 (사용자 목록 + role 변경)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.user import Role, User
from app.schemas.common import Timestamped

router = APIRouter()


class UserRead(Timestamped):
    id: int
    email: str
    name: str | None = None
    picture_url: str | None = None
    role: Role
    sso_provider: str | None = None
    last_login_at_iso: str | None = None


class UpdateRoleIn(BaseModel):
    role: Role


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserRead]:
    items = list((await db.execute(select(User).order_by(User.id))).scalars().all())
    out: list[UserRead] = []
    for u in items:
        out.append(
            UserRead(
                id=u.id,
                email=u.email,
                name=u.name,
                picture_url=u.picture_url,
                role=u.role,
                sso_provider=u.sso_provider,
                last_login_at_iso=u.last_login_at.isoformat() if u.last_login_at else None,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
        )
    return out


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
)
async def update_role(
    user_id: int,
    payload: UpdateRoleIn,
    actor: User = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="user not found")
    if target.id == actor.id and payload.role != Role.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="자신의 role을 ADMIN 미만으로 낮출 수 없습니다 (계정 잠금 방지).",
        )
    target.role = payload.role
    await db.commit()
    await db.refresh(target)
    return UserRead(
        id=target.id,
        email=target.email,
        name=target.name,
        picture_url=target.picture_url,
        role=target.role,
        sso_provider=target.sso_provider,
        last_login_at_iso=target.last_login_at.isoformat() if target.last_login_at else None,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


@router.get("/me/refresh", response_model=UserRead)
async def me_refresh(
    user: User = Depends(current_user),
) -> UserRead:
    """최신 role/메타 재조회용."""
    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
        role=user.role,
        sso_provider=user.sso_provider,
        last_login_at_iso=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
