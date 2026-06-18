"""
MFA 엔드포인트 — 패스키 / TOTP / 백업 코드

흐름 요지
---------
- 등록 계열은 *항상* pre-MFA 세션이어도 접근 가능 (사용자가 등록 안 했는데
  강제 정책이 켜진 직후엔 등록할 길이 있어야 한다).
- challenge 계열도 pre-MFA 세션 허용.
- 등록 해제는 verified 상태에서만 가능 (자기 자신을 잠그지 못하게).
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_session, current_user, current_user_pre_mfa
from app.auth.mfa import (
    begin_passkey_authentication,
    begin_passkey_registration,
    complete_passkey_authentication,
    complete_passkey_registration,
    confirm_totp,
    consume_backup_code,
    consume_totp,
    get_mfa_status,
    replace_backup_codes,
    totp_setup_for,
    upsert_unconfirmed_totp,
)
from app.core.database import get_db
from app.models.user import TotpSecret, User, UserSession, WebAuthnCredential

router = APIRouter()


# ── 상태 ─────────────────────────────────────────────────────
@router.get("/status")
async def status_(
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _sess = pre
    return await get_mfa_status(db, user)


# ── 패스키 등록 ──────────────────────────────────────────────
@router.post("/passkey/register/begin")
async def passkey_register_begin(
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _sess = pre
    return await begin_passkey_registration(db, user)


class PasskeyRegisterIn(BaseModel):
    name: str
    credential: dict  # @simplewebauthn/browser가 보낸 attestation response 그대로


@router.post("/passkey/register/complete")
async def passkey_register_complete(
    payload: PasskeyRegisterIn,
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _sess = pre
    try:
        cred = await complete_passkey_registration(db, user, payload.name, payload.credential)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"id": cred.id, "name": cred.name}


@router.delete("/passkey/{cred_id}")
async def passkey_delete(
    cred_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """등록된 패스키 제거. 자기 자신 잠금 방지를 위해 verified 상태 필수."""
    row = (
        await db.execute(
            select(WebAuthnCredential)
            .where(WebAuthnCredential.id == cred_id)
            .where(WebAuthnCredential.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="패스키를 찾을 수 없습니다.")
    await db.delete(row)
    # 남은 인증 수단이 없으면 mfa_enrolled = False로 되돌림
    remain = (
        await db.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
        )
    ).scalars().all()
    totp = (
        await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))
    ).scalar_one_or_none()
    user.mfa_enrolled = bool(remain) or (totp is not None and totp.confirmed)
    await db.commit()
    return {"ok": True}


# ── 패스키 인증 (로그인 시 MFA challenge) ────────────────────
@router.post("/passkey/login/begin")
async def passkey_login_begin(
    sess: UserSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        return await begin_passkey_authentication(db, sess.user, pre_session_id=sess.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class PasskeyLoginIn(BaseModel):
    credential: dict


@router.post("/passkey/login/complete")
async def passkey_login_complete(
    payload: PasskeyLoginIn,
    sess: UserSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        ok = await complete_passkey_authentication(
            db, sess.user, pre_session_id=sess.id, credential_response=payload.credential
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=400, detail="패스키 검증 실패")
    sess.mfa_verified = True
    await db.commit()
    return {"ok": True}


# ── TOTP ────────────────────────────────────────────────────
@router.post("/totp/setup")
async def totp_setup(
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """새 secret 발급 + QR PNG(base64). 사용자가 QR 스캔 후 /verify로 확정한다."""
    import base64

    import qrcode

    user, _sess = pre
    secret, uri = totp_setup_for(user)
    await upsert_unconfirmed_totp(db, user, secret)

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return {"secret": secret, "uri": uri, "qr_png_base64": qr_b64}


class TotpCodeIn(BaseModel):
    code: str


@router.post("/totp/verify")
async def totp_verify_(
    payload: TotpCodeIn,
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _sess = pre
    ok = await confirm_totp(db, user, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="TOTP 코드가 올바르지 않습니다.")
    return {"ok": True}


@router.post("/totp/challenge")
async def totp_challenge(
    payload: TotpCodeIn,
    sess: UserSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """로그인 시 TOTP 코드 검증 → mfa_verified=True 승격."""
    ok = await consume_totp(db, sess.user, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="TOTP 코드가 올바르지 않습니다.")
    sess.mfa_verified = True
    sess.user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.delete("/totp")
async def totp_disable(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = (
        await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))
    ).scalar_one_or_none()
    if row:
        await db.delete(row)
    # mfa_enrolled 재계산
    remain = (
        await db.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
        )
    ).scalars().all()
    user.mfa_enrolled = bool(remain)
    await db.commit()
    return {"ok": True}


# ── 백업 코드 ──────────────────────────────────────────────
@router.post("/backup-codes/regenerate")
async def backup_codes_regenerate(
    pre=Depends(current_user_pre_mfa),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """raw 10개를 한 번만 반환. 화면 닫으면 다시 못 본다(저장 안내 필수)."""
    user, _sess = pre
    codes = await replace_backup_codes(db, user)
    return {"codes": codes}


class BackupCodeIn(BaseModel):
    code: str


@router.post("/backup-codes/challenge")
async def backup_codes_challenge(
    payload: BackupCodeIn,
    sess: UserSession = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    ok = await consume_backup_code(db, sess.user, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="백업 코드가 올바르지 않거나 이미 사용됨.")
    sess.mfa_verified = True
    await db.commit()
    return {"ok": True}
