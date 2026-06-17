"""
🌙 Auth 엔드포인트 — SSO login/callback, Dev login, /me, logout, providers
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import oidc
from app.auth.deps import current_user
from app.auth.session import clear_cookie, create_session, resolve_session, revoke_session, set_cookie
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import Role, User
from app.services import user as user_service

logger = get_logger(__name__)
router = APIRouter()


# ── /providers : FE 로그인 화면이 어떤 옵션을 표시할지 결정 ─────────────
@router.get("/providers")
async def list_providers() -> dict:
    return {
        "mode": settings.AUTH_MODE,
        "dev_login_enabled": settings.AUTH_MODE != "sso",
        "providers": [{"name": p.name, "display": p.display} for p in oidc.list_providers()],
    }


# ── /me : 현재 사용자 ──────────────────────────────────────────────
class MeOut(BaseModel):
    id: int
    email: str
    name: str | None = None
    picture_url: str | None = None
    role: Role


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(current_user)) -> MeOut:
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
        role=user.role,
    )


# ── Dev login ─────────────────────────────────────────────────────
class DevLoginIn(BaseModel):
    email: EmailStr
    name: str | None = None


@router.post("/dev-login", response_model=MeOut)
async def dev_login(
    payload: DevLoginIn,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    """IdP 미설정 환경에서 이메일만으로 즉시 로그인 (개발/데모용)."""
    if settings.AUTH_MODE == "sso":
        raise HTTPException(
            status_code=403,
            detail="dev-login은 AUTH_MODE=dev에서만 허용됩니다. SSO를 사용하세요.",
        )
    user = await user_service.upsert_user(
        db,
        email=str(payload.email),
        name=payload.name,
        sso_provider="dev",
    )
    _, raw = await create_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    set_cookie(response, raw)
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
        role=user.role,
    )


# ── SSO login start ───────────────────────────────────────────────
@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    client = oidc.get_client(provider)
    if client is None:
        raise HTTPException(status_code=404, detail=f"provider '{provider}' not configured")
    redirect_uri = f"{settings.SSO_REDIRECT_BASE.rstrip('/')}/api/v1/auth/callback/{provider}"
    return await client.authorize_redirect(request, redirect_uri)


# ── SSO callback ──────────────────────────────────────────────────
@router.get("/callback/{provider}")
async def callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client = oidc.get_client(provider)
    if client is None:
        raise HTTPException(status_code=404, detail=f"provider '{provider}' not configured")
    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:
        logger.warning("oidc_callback_failed", provider=provider, error=str(exc))
        raise HTTPException(status_code=401, detail="OIDC 인증 실패") from exc

    info = token.get("userinfo") or {}
    email = info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="IdP에서 email 클레임을 받지 못했습니다.")

    user = await user_service.upsert_user(
        db,
        email=email,
        name=info.get("name") or info.get("preferred_username"),
        picture_url=info.get("picture"),
        sso_provider=provider,
        sso_subject=str(info.get("sub")),
    )
    _, raw = await create_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )

    # FE로 cookie 심고 리다이렉트
    resp = RedirectResponse(url=f"{settings.SSO_REDIRECT_BASE.rstrip('/')}/")
    set_cookie(resp, raw)
    return resp


# ── Logout ────────────────────────────────────────────────────────
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw = request.cookies.get(settings.SESSION_COOKIE)
    sess = await resolve_session(db, raw)
    if sess:
        await revoke_session(db, sess)
    clear_cookie(response)
    return {"ok": True}
