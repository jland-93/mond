"""
AI Provider 동적 설정 — 관리자가 UI에서 추가/변경하는 LLM provider 자격증명.

저장 방식
---------
- provider 1:1 unique (anthropic / openai / bedrock / ollama)
- api_key는 SECRET_KEY 유래 Fernet으로 **암호화 후 저장**. raw는 디스크에 없음.
- is_default=True인 행이 활성 provider. 응답 시 api_key는 마스킹("sk-...***").

ENV fallback
------------
DB 행이 없거나 비어 있으면 기존 .env의 ANTHROPIC_API_KEY/OPENAI_API_KEY 등이
그대로 사용된다 (하위 호환). 즉 OSS 첫 부팅 시 .env만으로도 동작한다.
"""

from __future__ import annotations

from sqlalchemy import Boolean, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AIProviderConfig(Base, TimestampMixin):
    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 'anthropic' / 'openai' / 'bedrock' / 'ollama'
    provider: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    # 활성(default) provider — DB 안에서 정확히 0개 또는 1개만 True (앱 로직으로 강제)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    # Fernet 암호문 (None이면 ENV fallback)
    api_key_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    # OpenAI base_url (Azure/사내 게이트웨이) 또는 Ollama base_url
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # AWS Bedrock region
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_default: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_deep: Mapped[str | None] = mapped_column(String(128), nullable=True)
