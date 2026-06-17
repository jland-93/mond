"""
🌙 Policy 스키마
"""

from pydantic import BaseModel, Field

from app.models.policy import PolicyType
from app.schemas.common import Timestamped


class PolicyBase(BaseModel):
    name: str
    policy_type: PolicyType
    description: str | None = None
    enabled: bool = True
    severity_threshold: str = "medium"
    definition: dict = Field(default_factory=dict)
    compliance_refs: list[str] = Field(default_factory=list)


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    enabled: bool | None = None
    severity_threshold: str | None = None
    definition: dict | None = None
    compliance_refs: list[str] | None = None


class PolicyRead(PolicyBase, Timestamped):
    id: int
