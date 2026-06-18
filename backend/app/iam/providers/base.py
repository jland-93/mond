"""IAM provider 공통 — dataclasses와 자격증명 해석 helper."""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.iam import IAMSource, IdentityType

logger = get_logger(__name__)


@dataclass
class FetchedIdentity:
    identity_type: IdentityType
    name: str
    external_id: str | None = None
    attributes: dict | None = None


@dataclass
class FetchedPermission:
    name: str
    external_id: str | None = None
    description: str | None = None
    risk_hint: str | None = None
    attributes: dict | None = None


@dataclass
class FetchResult:
    identities: list[FetchedIdentity]
    permissions: list[FetchedPermission]
    stub: bool = False
    error: str | None = None


@dataclass
class AttachResult:
    success: bool
    detail: dict


def resolve_credentials(source: IAMSource) -> dict[str, str]:
    """credentials_env_ref가 {"access_key_id": "AWS_ACCESS_KEY_ID"} 형태일 때 ENV에서 실값을 가져온다."""
    return {k: os.environ.get(v, "") for k, v in (source.credentials_env_ref or {}).items()}
