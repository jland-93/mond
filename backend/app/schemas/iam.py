"""
IAM 셀프서비스 스키마
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.iam import AccessRequestStatus, IAMSourceKind, IdentityType
from app.schemas.common import Timestamped


# ── IAMSource ──
class IAMSourceCreate(BaseModel):
    name: str
    kind: IAMSourceKind
    config: dict = Field(default_factory=dict)
    credentials_env_ref: dict = Field(default_factory=dict)


class IAMSourceRead(Timestamped):
    id: int
    name: str
    kind: IAMSourceKind
    config: dict
    last_synced_at_str: str | None = None


# ── IAMIdentity ──
class IAMIdentityRead(Timestamped):
    id: int
    source_id: int
    identity_type: IdentityType
    name: str
    external_id: str | None = None
    attributes: dict


# ── Permission ──
class PermissionRead(Timestamped):
    id: int
    source_id: int
    name: str
    external_id: str | None = None
    description: str | None = None
    risk_hint: str | None = None
    attributes: dict


# ── AccessRequest ──
class AccessRequestCreate(BaseModel):
    requester: str
    reason: str = Field(..., min_length=5, max_length=2000)
    target_identity_id: int
    permission_id: int
    duration_hours: int | None = None


class HumanDecisionIn(BaseModel):
    approve: bool
    reviewer: str
    note: str | None = None


class AccessRequestRead(Timestamped):
    id: int
    requester: str
    reason: str
    duration_hours: int | None = None
    target_identity_id: int
    permission_id: int
    status: AccessRequestStatus
    ai_decision: dict
    human_decision: dict
    grant_result: dict
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revoke_result: dict = Field(default_factory=dict)


class AuditLogRead(Timestamped):
    id: int
    request_id: int
    event: str
    actor: str
    detail: dict


class RevokeRequest(BaseModel):
    actor: str
