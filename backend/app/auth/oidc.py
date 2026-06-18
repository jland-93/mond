"""
OIDC provider 동적 등록 — Keycloak / Okta / Google / Azure AD 등

settings.SSO_PROVIDERS에 콤마로 묶인 provider 이름만 들어가면 자동 활성.
각 provider는 issuer URL을 ENV로 받아 discovery로 메타 자동 로드.
"""

from __future__ import annotations

from dataclasses import dataclass

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings


@dataclass
class ProviderInfo:
    name: str          # 내부 키 (소문자)
    display: str       # 사용자에게 보이는 라벨


_oauth = OAuth()
_REGISTERED: dict[str, ProviderInfo] = {}


def _maybe(name: str, display: str, issuer: str | None, client_id: str | None, client_secret: str | None) -> None:
    if name not in _active_providers():
        return
    if not issuer or not client_id or not client_secret:
        return
    _oauth.register(
        name=name,
        server_metadata_url=f"{issuer.rstrip('/')}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        client_kwargs={"scope": "openid email profile"},
    )
    _REGISTERED[name] = ProviderInfo(name=name, display=display)


def _maybe_google() -> None:
    """Google은 issuer 고정."""
    if "google" not in _active_providers():
        return
    if not settings.SSO_GOOGLE_CLIENT_ID or not settings.SSO_GOOGLE_CLIENT_SECRET:
        return
    _oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=settings.SSO_GOOGLE_CLIENT_ID,
        client_secret=settings.SSO_GOOGLE_CLIENT_SECRET,
        client_kwargs={"scope": "openid email profile"},
    )
    _REGISTERED["google"] = ProviderInfo(name="google", display="Google")


def _active_providers() -> set[str]:
    raw = (settings.SSO_PROVIDERS or "").strip()
    if not raw:
        return set()
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def init_providers() -> None:
    _maybe(
        "keycloak",
        "Keycloak",
        settings.SSO_KEYCLOAK_ISSUER,
        settings.SSO_KEYCLOAK_CLIENT_ID,
        settings.SSO_KEYCLOAK_CLIENT_SECRET,
    )
    _maybe(
        "okta",
        "Okta",
        settings.SSO_OKTA_ISSUER,
        settings.SSO_OKTA_CLIENT_ID,
        settings.SSO_OKTA_CLIENT_SECRET,
    )
    _maybe_google()


def list_providers() -> list[ProviderInfo]:
    return list(_REGISTERED.values())


def get_client(name: str):
    if name not in _REGISTERED:
        return None
    return _oauth.create_client(name)
