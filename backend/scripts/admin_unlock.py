"""
🌙 ADMIN MFA 복구 스크립트 — 사용자가 MFA에서 잠겼을 때 운영자가 직접 풀어준다.

사용:
  docker compose exec backend python -m scripts.admin_unlock admin@example.com

동작:
  - 해당 이메일의 모든 MFA factor 삭제 (passkey · TOTP · backup codes · pending challenges)
  - users.mfa_enrolled = false
  - 활성 세션의 mfa_verified = false → 다음 페이지 로드 시 /mfa로 이동

안전 장치:
  - 존재하지 않는 이메일이면 종료 코드 1
  - 확인 프롬프트 (--yes로 건너뜀)
  - 변경 전후 상태를 출력
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import (
    MfaBackupCode,
    TotpSecret,
    User,
    UserSession,
    WebAuthnChallenge,
    WebAuthnCredential,
)


async def _unlock(email: str) -> int:
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
        if user is None:
            print(f"❌ user not found: {email}", file=sys.stderr)
            return 1

        before = {
            "passkeys": (await db.execute(select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id))).scalars().all(),
            "totp":     (await db.execute(select(TotpSecret).where(TotpSecret.user_id == user.id))).scalars().all(),
            "backup":   (await db.execute(select(MfaBackupCode).where(MfaBackupCode.user_id == user.id))).scalars().all(),
            "sessions": (await db.execute(select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)))).scalars().all(),
        }
        print(f"🔍 {user.email} (role={user.role.value}) 현재 MFA 상태:")
        print(f"   · passkeys:     {len(before['passkeys'])}")
        print(f"   · totp:         {len(before['totp'])} (confirmed={sum(1 for t in before['totp'] if t.confirmed)})")
        print(f"   · backup codes: {len(before['backup'])}")
        print(f"   · 활성 세션:    {len(before['sessions'])}")

        await db.execute(delete(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id))
        await db.execute(delete(TotpSecret).where(TotpSecret.user_id == user.id))
        await db.execute(delete(MfaBackupCode).where(MfaBackupCode.user_id == user.id))
        await db.execute(delete(WebAuthnChallenge).where(WebAuthnChallenge.user_id == user.id))
        user.mfa_enrolled = False
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
            .values(mfa_verified=False)
        )
        await db.commit()
        print(f"✅ {user.email} MFA 복구 완료. 다음 새로고침 시 첫 등록 화면이 보입니다.")
        return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="ADMIN MFA 복구 — 사용자가 잠겼을 때 모든 MFA factor 삭제",
        epilog="예: docker compose exec backend python -m scripts.admin_unlock admin@example.com",
    )
    p.add_argument("email", help="복구할 사용자 이메일")
    p.add_argument("--yes", action="store_true", help="확인 프롬프트 건너뛰기")
    args = p.parse_args()

    if not args.yes:
        ok = input(f"⚠️  {args.email} 의 모든 MFA factor를 삭제합니다. 계속? [y/N] ")
        if ok.strip().lower() not in ("y", "yes"):
            print("취소됨.")
            return 0

    return asyncio.run(_unlock(args.email))


if __name__ == "__main__":
    sys.exit(main())
