"""
🌙 Finding 스키마
"""

from pydantic import BaseModel, Field

from app.models.finding import FindingStatus, Severity
from app.schemas.common import Timestamped


class FindingBase(BaseModel):
    asset_id: int
    scan_id: int | None = None
    rule_id: str
    title: str
    description: str | None = None
    severity: Severity
    scanner: str
    location: str | None = None
    references: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class FindingCreate(FindingBase):
    fingerprint: str | None = None  # 미지정 시 서비스가 산출


class FindingUpdate(BaseModel):
    status: FindingStatus | None = None
    severity: Severity | None = None


class FindingRead(FindingBase, Timestamped):
    id: int
    status: FindingStatus
    fingerprint: str
