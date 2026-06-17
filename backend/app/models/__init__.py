"""
🌙 ORM 모델 모음

create_all 호출 전에 모든 모델 모듈이 임포트되어야 메타데이터에 등록된다.
"""

from app.models.ai_insight import AIInsight, InsightKind
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
]
