"""
AI 토큰 사용량 로그 — provider/model/intent별 누적 입출력 토큰.

추적 목적
--------
- 외부 LLM 비용 가시화 (Anthropic/OpenAI/Bedrock)
- 사내 vLLM/Ollama 게이트웨이의 호출량 + 효율 검증
- intent별 라우팅(PR #87)이 model_default/model_deep 어디로 가는지 사후 검증

설계
----
- complete_json 직후 입력/출력 토큰을 그대로 기록 (None이면 0 fallback)
- 외부 LLM이 토큰 정보를 안 주는 경우(ollama 일부)도 0으로 행을 남겨 호출수 카운트
- failed=true는 호출이 실패한 경우(text 비어 있거나 예외) — 비용 0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False)  # 'default' | 'deep'
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
