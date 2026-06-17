"""
🌙 Knowledge 스키마
"""

from pydantic import BaseModel, Field

from app.models.knowledge import KnowledgeCategory, KnowledgeSource
from app.schemas.common import Timestamped


class KnowledgeCardBase(BaseModel):
    slug: str
    category: KnowledgeCategory
    title_ko: str
    title_en: str
    summary_ko: str
    summary_en: str
    ask_ko: str
    ask_en: str
    refs: list[str] = Field(default_factory=list)
    source: KnowledgeSource = KnowledgeSource.MANUAL
    published: bool = True


class KnowledgeCardCreate(KnowledgeCardBase):
    pass


class KnowledgeCardUpdate(BaseModel):
    title_ko: str | None = None
    title_en: str | None = None
    summary_ko: str | None = None
    summary_en: str | None = None
    ask_ko: str | None = None
    ask_en: str | None = None
    refs: list[str] | None = None
    published: bool | None = None


class KnowledgeCardRead(KnowledgeCardBase, Timestamped):
    id: int
    model: str | None = None


class GenerateRequest(BaseModel):
    category: KnowledgeCategory
    topic_hint: str | None = Field(default=None, max_length=2000)
    count: int = Field(default=2, ge=1, le=5)
