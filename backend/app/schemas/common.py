"""
공용 스키마 — 페이지네이션, 타임스탬프 베이스
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """SQLAlchemy 객체에서 바로 직렬화 가능한 베이스."""

    model_config = ConfigDict(from_attributes=True)


class Timestamped(ORMModel):
    created_at: datetime
    updated_at: datetime


class Page(BaseModel, Generic[T]):
    """오프셋 페이지네이션 응답."""

    items: list[T]
    total: int
    limit: int
    offset: int


class PageParams(BaseModel):
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
