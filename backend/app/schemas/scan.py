"""
Scan 스키마
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.scan import ScanStatus, ScanTrigger
from app.schemas.common import Timestamped


class ScanCreate(BaseModel):
    asset_id: int
    scanner: str
    trigger: ScanTrigger = ScanTrigger.MANUAL


class ScanRead(Timestamped):
    id: int
    asset_id: int
    scanner: str
    trigger: ScanTrigger
    status: ScanStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    findings_count: int = 0
    error_message: str | None = None
