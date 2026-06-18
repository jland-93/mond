"""
KnowledgeCard — 지식 허브 카드 (동적)

초기에는 db_seed가 17건을 채우고, 이후 다음 두 경로로 늘어난다:
  - AI 생성: POST /knowledge/cards/generate (Claude가 새 카드 N건 제안)
  - 관리자 수동 추가: POST /knowledge/cards
"""

import enum

from sqlalchemy import JSON, Boolean, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class KnowledgeCategory(str, enum.Enum):
    DEVSECOPS_BASICS = "devsecops_basics"
    OWASP = "owasp"
    KR_REGULATIONS = "kr_regulations"
    GLOBAL_REGULATIONS = "global_regulations"
    BEST_PRACTICES = "best_practices"
    INCIDENT_RESPONSE = "incident_response"


class KnowledgeSource(str, enum.Enum):
    SEED = "seed"        # db_seed가 만든 초기 카드
    AI = "ai"            # Claude가 생성
    MANUAL = "manual"    # 관리자 수동 추가


class KnowledgeCard(Base, TimestampMixin):
    __tablename__ = "knowledge_cards"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_knowledge_card_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[KnowledgeCategory] = mapped_column(
        Enum(KnowledgeCategory, name="knowledge_category", native_enum=False),
        nullable=False,
        index=True,
    )
    title_ko: Mapped[str] = mapped_column(String(512), nullable=False)
    title_en: Mapped[str] = mapped_column(String(512), nullable=False)
    summary_ko: Mapped[str] = mapped_column(Text, nullable=False)
    summary_en: Mapped[str] = mapped_column(Text, nullable=False)
    ask_ko: Mapped[str] = mapped_column(Text, nullable=False)
    ask_en: Mapped[str] = mapped_column(Text, nullable=False)
    refs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    source: Mapped[KnowledgeSource] = mapped_column(
        Enum(KnowledgeSource, name="knowledge_source", native_enum=False),
        nullable=False,
        default=KnowledgeSource.MANUAL,
        index=True,
    )
    published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model: Mapped[str | None] = mapped_column(String(64))  # AI 생성 시 어떤 모델인지
