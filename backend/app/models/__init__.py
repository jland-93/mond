"""
🌙 ORM 모델 모음

create_all 호출 전에 모든 모델 모듈이 임포트되어야 메타데이터에 등록된다.
"""

from app.models.ai_insight import AIInsight, InsightKind
from app.models.ai_provider import AIProviderConfig
from app.models.role_request import RoleChangeRequest, RoleRequestStatus
from app.models.webhook_token import WebhookToken
from app.models.asset import Asset, AssetType
from app.models.base import Base
from app.models.finding import Finding, FindingStatus, Severity
from app.models.iam import (
    AccessAuditLog,
    AccessRequest,
    AccessRequestStatus,
    AuditEvent,
    IAMIdentity,
    IAMSource,
    IAMSourceKind,
    IdentityType,
    Permission,
)
from app.models.knowledge import KnowledgeCard, KnowledgeCategory, KnowledgeSource
from app.models.policy import Policy, PolicyType
from app.models.scan import Scan, ScanStatus, ScanTrigger
from app.models.user import (
    MfaBackupCode,
    Role,
    TotpSecret,
    User,
    UserSession,
    WebAuthnChallenge,
    WebAuthnCredential,
)

__all__ = [
    "Base",
    "Asset",
    "AssetType",
    "Scan",
    "ScanStatus",
    "ScanTrigger",
    "Finding",
    "FindingStatus",
    "Severity",
    "Policy",
    "PolicyType",
    "AIInsight",
    "InsightKind",
    "AIProviderConfig",
    "WebhookToken",
    "RoleChangeRequest",
    "RoleRequestStatus",
    "IAMSource",
    "IAMSourceKind",
    "IAMIdentity",
    "IdentityType",
    "Permission",
    "AccessRequest",
    "AccessRequestStatus",
    "AccessAuditLog",
    "AuditEvent",
    "KnowledgeCard",
    "KnowledgeCategory",
    "KnowledgeSource",
    "User",
    "UserSession",
    "Role",
    "WebAuthnCredential",
    "WebAuthnChallenge",
    "TotpSecret",
    "MfaBackupCode",
]
