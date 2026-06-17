"""
🌙 Policy — 룰셋/표준 (SAST / SCA / IaC / DAST / Compliance)
"""

import enum

from sqlalchemy import JSON, Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PolicyType(str, enum.Enum):
    SAST = "sast"
    SCA = "sca"
    IAC = "iac"
    DAST = "dast"
    CONTAINER = "container"
    SECRETS = "secrets"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    policy_type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, name="policy_type", native_enum=False),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 차단 임계치 (이 이상의 severity가 발견되면 게이트 실패)
    severity_threshold: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    # 정책 정의 — OPA Rego, JSON Schema, semgrep config 등 어댑터가 해석한다.
    definition: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # 컴플라이언스 매핑: ["CIS-AWS-1.4", "OWASP-A01", "NIST-800-53-AC-2"]
    compliance_refs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
