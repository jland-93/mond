"""
🌙 MFA 모듈 — 패스키(WebAuthn/FIDO2) + TOTP + 백업 코드

설계 요지
---------
- 1차 인증(이메일·SSO) 후 강제 대상 role이면 `pre-MFA` 세션으로 발급한다.
- pre-MFA 세션은 cookie는 동일하나 `mfa_verified=False`. 보호 리소스 접근 시
  `current_user_verified` 의존성이 401/403으로 막는다.
- MFA challenge(패스키/TOTP/백업코드)가 통과되면 같은 UserSession.row의
  `mfa_verified=True`로 승격.

운영 권장사항
-------------
- TOTP secret과 백업 코드 hash는 DB에 평문 저장된다(개발 편의). 실 운영에서는
  KMS 또는 애플리케이션-수준 암호화로 wrapping을 권장.
- MFA_RP_ID는 cookie domain과 같은 등록형 도메인이어야 한다(서브도메인 OK).
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import (
    MfaBackupCode,
    TotpSecret,
    User,
    WebAuthnChallenge,
    WebAuthnCredential,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def mfa_required_for(user: User) -> bool:
    """이 사용자 role이 MFA 강제 대상인지."""
    roles_csv = (settings.MFA_REQUIRED_ROLES or "").strip().lower()
    if not roles_csv:
        return False
    required = {r.strip() for r in roles_csv.split(",") if r.strip()}
    return user.role.value in required


def hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_backup_codes(n: int = 10) -> list[str]:
    """사람이 입력하기 좋은 8자리-8자리 코드 N개. raw는 생성 직후에만 노출."""
    raw: list[str] = []
    for _ in range(n):
        a = secrets.token_hex(4).upper()
        b = secrets.token_hex(4).upper()
        raw.append(f"{a}-{b}")
    return raw


# ── WebAuthn ─────────────────────────────────────────────────────
def _rp_options():
    """py_webauthn의 PublicKeyCredentialRpEntity 등 옵션 빌더."""
    from webauthn.helpers.structs import PublicKeyCredentialRpEntity

    return PublicKeyCredentialRpEntity(id=settings.MFA_RP_ID, name=settings.MFA_RP_NAME)


async def begin_passkey_registration(db: AsyncSession, user: User) -> dict:
    """등록 challenge를 생성하고 클라이언트가 navigator.credentials.create에 줄 옵션을 반환."""
    from webauthn import generate_registration_options, options_to_json
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    # 이미 등록된 credential은 exclude (중복 방지)
    rows = (
        await db.execute(
            select(WebAuthnCredential.credential_id).where(WebAuthnCredential.user_id == user.id)
        )
    ).all()
    exclude = [PublicKeyCredentialDescriptor(id=r[0]) for r in rows]

    options = generate_registration_options(
        rp_id=settings.MFA_RP_ID,
        rp_name=settings.MFA_RP_NAME,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.email,
        user_display_name=user.name or user.email,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    # challenge 저장
    chal = WebAuthnChallenge(
        user_id=user.id,
        purpose="registration",
        challenge=options.challenge,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.MFA_CHALLENGE_TTL),
    )
    db.add(chal)
    await db.commit()

    import json
    return json.loads(options_to_json(options))


async def complete_passkey_registration(
    db: AsyncSession,
    user: User,
    name: str,
    credential_response: dict,
) -> WebAuthnCredential:
    from webauthn import verify_registration_response

    # 사용자의 가장 최근 registration challenge 가져오기
    stmt = (
        select(WebAuthnChallenge)
        .where(WebAuthnChallenge.user_id == user.id)
        .where(WebAuthnChallenge.purpose == "registration")
        .order_by(WebAuthnChallenge.id.desc())
        .limit(1)
    )
    chal = (await db.execute(stmt)).scalar_one_or_none()
    if not chal or chal.expires_at <= datetime.now(timezone.utc):
        raise ValueError("등록 challenge가 만료되었거나 존재하지 않습니다. 다시 시작하세요.")

    verification = verify_registration_response(
        credential=credential_response,
        expected_challenge=bytes(chal.challenge),
        expected_origin=settings.MFA_RP_ORIGIN,
        expected_rp_id=settings.MFA_RP_ID,
    )

    cred = WebAuthnCredential(
        user_id=user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        name=name[:120] or "패스키",
        transports=",".join(credential_response.get("response", {}).get("transports", []) or []) or None,
    )
    db.add(cred)
    # challenge 소비
    await db.delete(chal)
    user.mfa_enrolled = True
    await db.commit()
    await db.refresh(cred)
    return cred


async def begin_passkey_authentication(
    db: AsyncSession,
    user: User,
    pre_session_id: int,
) -> dict:
    from webauthn import generate_authentication_options, options_to_json
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement

    rows = (
        await db.execute(
            select(WebAuthnCredential.credential_id).where(WebAuthnCredential.user_id == user.id)
        )
    ).all()
    if not rows:
        raise ValueError("등록된 패스키가 없습니다.")

    allow = [PublicKeyCredentialDescriptor(id=r[0]) for r in rows]

    options = generate_authentication_options(
        rp_id=settings.MFA_RP_ID,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    chal = WebAuthnChallenge(
        user_id=user.id,
        pre_session_id=pre_session_id,
        purpose="authentication",
        challenge=options.challenge,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.MFA_CHALLENGE_TTL),
    )
    db.add(chal)
    await db.commit()

    import json
    return json.loads(options_to_json(options))


async def complete_passkey_authentication(
    db: AsyncSession,
    user: User,
    pre_session_id: int,
    credential_response: dict,
) -> bool:
    from webauthn import verify_authentication_response

    stmt = (
        select(WebAuthnChallenge)
        .where(WebAuthnChallenge.user_id == user.id)
        .where(WebAuthnChallenge.purpose == "authentication")
        .where(WebAuthnChallenge.pre_session_id == pre_session_id)
        .order_by(WebAuthnChallenge.id.desc())
        .limit(1)
    )
    chal = (await db.execute(stmt)).scalar_one_or_none()
    if not chal or chal.expires_at <= datetime.now(timezone.utc):
        raise ValueError("인증 challenge가 만료되었거나 존재하지 않습니다. 다시 시도하세요.")

    raw_id = credential_response.get("rawId") or credential_response.get("id")
    if not raw_id:
        raise ValueError("rawId가 없습니다")
    credential_id_bytes = _b64url_decode(raw_id) if isinstance(raw_id, str) else bytes(raw_id)

    cred_stmt = select(WebAuthnCredential).where(
        WebAuthnCredential.user_id == user.id,
        WebAuthnCredential.credential_id == credential_id_bytes,
    )
    cred = (await db.execute(cred_stmt)).scalar_one_or_none()
    if not cred:
        raise ValueError("이 패스키는 이 계정에 등록되어 있지 않습니다.")

    verification = verify_authentication_response(
        credential=credential_response,
        expected_challenge=bytes(chal.challenge),
        expected_origin=settings.MFA_RP_ORIGIN,
        expected_rp_id=settings.MFA_RP_ID,
        credential_public_key=bytes(cred.public_key),
        credential_current_sign_count=cred.sign_count,
    )
    # sign count 갱신 + challenge 소비
    cred.sign_count = verification.new_sign_count
    cred.last_used_at = datetime.now(timezone.utc)
    await db.delete(chal)
    await db.commit()
    return True


# ── TOTP ────────────────────────────────────────────────────────
def totp_setup_for(user: User) -> tuple[str, str]:
    """(base32 secret, otpauth:// URI) 튜플. UI는 URI를 QR로 그려서 보여준다."""
    import pyotp

    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=settings.MFA_RP_NAME)
    return secret, uri


def totp_verify(secret: str, code: str) -> bool:
    import pyotp

    code = (code or "").strip().replace(" ", "")
    if not code.isdigit() or len(code) not in (6, 8):
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


async def upsert_unconfirmed_totp(db: AsyncSession, user: User, secret: str) -> TotpSecret:
    existing = (
        await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))
    ).scalar_one_or_none()
    if existing:
        existing.secret = secret
        existing.confirmed = False
        await db.commit()
        return existing
    row = TotpSecret(user_id=user.id, secret=secret, confirmed=False)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def confirm_totp(db: AsyncSession, user: User, code: str) -> bool:
    row = (
        await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))
    ).scalar_one_or_none()
    if not row:
        return False
    if not totp_verify(row.secret, code):
        return False
    row.confirmed = True
    row.last_used_at = datetime.now(timezone.utc)
    user.mfa_enrolled = True
    await db.commit()
    return True


async def consume_totp(db: AsyncSession, user: User, code: str) -> bool:
    row = (
        await db.execute(
            select(TotpSecret).where(TotpSecret.user_id == user.id, TotpSecret.confirmed.is_(True))
        )
    ).scalar_one_or_none()
    if not row:
        return False
    if not totp_verify(row.secret, code):
        return False
    row.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return True


# ── 백업 코드 ──────────────────────────────────────────────────
async def replace_backup_codes(db: AsyncSession, user: User) -> list[str]:
    # 기존 모두 폐기
    await db.execute(
        MfaBackupCode.__table__.delete().where(MfaBackupCode.user_id == user.id)
    )
    raw_codes = generate_backup_codes()
    for raw in raw_codes:
        db.add(MfaBackupCode(user_id=user.id, code_hash=hash_backup_code(raw)))
    user.mfa_enrolled = True
    await db.commit()
    return raw_codes


async def consume_backup_code(db: AsyncSession, user: User, code: str) -> bool:
    h = hash_backup_code((code or "").strip().upper())
    row = (
        await db.execute(
            select(MfaBackupCode)
            .where(MfaBackupCode.user_id == user.id)
            .where(MfaBackupCode.code_hash == h)
            .where(MfaBackupCode.used_at.is_(None))
        )
    ).scalar_one_or_none()
    if not row:
        return False
    row.used_at = datetime.now(timezone.utc)
    await db.commit()
    return True


# ── 등록 상태 요약 ──────────────────────────────────────────────
async def get_mfa_status(db: AsyncSession, user: User) -> dict:
    creds = (
        await db.execute(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
        )
    ).scalars().all()
    totp = (
        await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))
    ).scalar_one_or_none()
    backup_unused = (
        await db.execute(
            select(MfaBackupCode)
            .where(MfaBackupCode.user_id == user.id)
            .where(MfaBackupCode.used_at.is_(None))
        )
    ).scalars().all()
    return {
        "required": mfa_required_for(user),
        "enrolled": bool(creds) or (totp is not None and totp.confirmed),
        "passkeys": [
            {
                "id": c.id,
                "name": c.name,
                "transports": (c.transports or "").split(",") if c.transports else [],
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
            }
            for c in creds
        ],
        "totp_confirmed": bool(totp and totp.confirmed),
        "backup_codes_remaining": len(backup_unused),
    }
