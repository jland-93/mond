"""
Asset 스키마
"""

from pydantic import BaseModel, Field

from app.models.asset import AssetType
from app.schemas.common import Timestamped


class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: AssetType
    uri: str = Field(..., min_length=1, max_length=1024)
    description: str | None = None
    labels: dict = Field(default_factory=dict)
    owner: str | None = None
    environment: str | None = None
    workspace_id: int | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    labels: dict | None = None
    owner: str | None = None
    environment: str | None = None
    workspace_id: int | None = None


class AssetRead(AssetBase, Timestamped):
    id: int
    open_findings_count: int = 0
    last_scanned_at_str: str | None = None
