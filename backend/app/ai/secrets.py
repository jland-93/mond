"""
🌙 AI Provider 자격증명 암호화

SECRET_KEY를 SHA-256로 유도해 Fernet 키로 사용한다. SECRET_KEY가 바뀌면 기존
암호문은 복호화 불가 → 운영에서는 키 회전 시 마이그레이션 절차 필요.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt(plaintext: str) -> bytes:
    return _fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(token: bytes | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(bytes(token)).decode("utf-8")
    except InvalidToken:
        return None


def mask(api_key: str | None) -> str:
    """write-only 노출용 — 마지막 4자만 보이게."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "•" * len(api_key)
    return api_key[:4] + "•" * 6 + api_key[-4:]
