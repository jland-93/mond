"""
🌙 LLM provider 추상화

OSS 사용자가 자기 환경에 맞는 AI API를 끌어다 쓰게 한다:
  - anthropic : Anthropic Claude (직접 API)
  - openai    : OpenAI / Azure OpenAI / OpenAI-compatible gateway
  - bedrock   : AWS Bedrock (Claude · Llama · Titan, IAM 자격으로)
  - ollama    : 로컬 LLM (Ollama / vLLM 호환) — 폐쇄망 / 데이터 외부 유출 금지 조직

사용처 (`app/ai/insights.py`, `app/iam/ai_review.py`)는 다음만 알면 된다:
  - `is_enabled()` — True면 provider가 실제로 호출 가능
  - `get_provider()` — 'anthropic' / 'openai' / 'bedrock' / 'ollama' / None
  - `await complete_json(system, user, deep) -> CompletionResult`
        strict JSON 응답을 받아서 InsightResult/route_query에 그대로 넘긴다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompletionResult:
    """provider-agnostic 응답. 호출부가 모두 동일하게 사용한다."""

    text: str               # 모델이 생성한 raw text (JSON 문자열을 기대)
    provider: str           # 'anthropic' / 'openai' / 'bedrock' / 'ollama'
    model: str              # 실제 사용한 모델 ID
    input_tokens: int | None = None
    output_tokens: int | None = None


def get_provider() -> str | None:
    """현재 활성화된 provider 이름 반환. 키가 없으면 None."""
    p = (settings.AI_PROVIDER or "").lower().strip()
    if p == "anthropic" and settings.ANTHROPIC_API_KEY:
        return "anthropic"
    if p == "openai" and settings.OPENAI_API_KEY:
        return "openai"
    if p == "bedrock":
        # IAM role/자격증명은 boto3가 자동 감지 — 사용자가 'bedrock'을 명시했으면 활성으로 간주.
        return "bedrock"
    if p == "ollama":
        return "ollama"
    return None


def is_enabled() -> bool:
    return get_provider() is not None


def _resolve_model(deep: bool) -> str:
    provider = get_provider()
    if provider == "openai":
        return settings.OPENAI_MODEL_DEEP if deep else settings.OPENAI_MODEL_DEFAULT
    if provider == "bedrock":
        return settings.BEDROCK_MODEL_DEEP if deep else settings.BEDROCK_MODEL_DEFAULT
    if provider == "ollama":
        return settings.OLLAMA_MODEL_DEEP if deep else settings.OLLAMA_MODEL_DEFAULT
    return settings.AI_MODEL_DEEP if deep else settings.AI_MODEL_DEFAULT


async def complete_json(
    system: str,
    user: str,
    *,
    deep: bool = False,
    max_tokens: int | None = None,
) -> CompletionResult | None:
    """provider별 LLM 호출. JSON 문자열을 text로 반환. 실패하면 None."""
    provider = get_provider()
    if provider is None:
        return None
    model = _resolve_model(deep)
    max_tokens = max_tokens or settings.AI_MAX_TOKENS

    try:
        if provider == "anthropic":
            return await _call_anthropic(system, user, model, max_tokens)
        if provider == "openai":
            return await _call_openai(system, user, model, max_tokens)
        if provider == "bedrock":
            return await _call_bedrock(system, user, model, max_tokens)
        if provider == "ollama":
            return await _call_ollama(system, user, model, max_tokens)
    except Exception as exc:
        logger.warning("ai_complete_failed", provider=provider, model=model, error=str(exc))
        return None
    return None


# ── Anthropic ───────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _anthropic_client():
    from anthropic import AsyncAnthropic
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def _call_anthropic(system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    client = _anthropic_client()
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return CompletionResult(
        text=text,
        provider="anthropic",
        model=model,
        input_tokens=getattr(response.usage, "input_tokens", None),
        output_tokens=getattr(response.usage, "output_tokens", None),
    )


# ── OpenAI (OpenAI / Azure / 호환 게이트웨이) ────────────────────
@lru_cache(maxsize=1)
def _openai_client():
    from openai import AsyncOpenAI
    kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return AsyncOpenAI(**kwargs)


async def _call_openai(system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    client = _openai_client()
    response = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    usage = response.usage
    return CompletionResult(
        text=text,
        provider="openai",
        model=model,
        input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
    )


# ── AWS Bedrock ─────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _bedrock_client():
    import boto3
    return boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)


async def _call_bedrock(system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    """Bedrock 모델은 model id에 따라 invoke body 포맷이 다르다 (Anthropic 계열 vs Llama 등).

    여기서는 Anthropic on Bedrock(`anthropic.claude-*`)만 지원한다 — 한국에서 가장 흔한 조합.
    """
    if not model.startswith("anthropic."):
        raise ValueError(f"unsupported bedrock model (only anthropic.* supported): {model}")

    import asyncio
    client = _bedrock_client()
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
    )
    # boto3는 동기. asyncio.to_thread로 비동기화.
    raw = await asyncio.to_thread(
        client.invoke_model,
        modelId=model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    payload = json.loads(raw["body"].read())
    text_parts = payload.get("content", [])
    text = "".join(p.get("text", "") for p in text_parts if isinstance(p, dict))
    usage = payload.get("usage") or {}
    return CompletionResult(
        text=text,
        provider="bedrock",
        model=model,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


# ── Ollama (로컬) ──────────────────────────────────────────────
async def _call_ollama(system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    """Ollama는 OpenAI 호환 chat API + JSON format 모드를 지원한다."""
    import httpx

    base = settings.OLLAMA_BASE_URL.rstrip("/")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_predict": max_tokens},
    }
    async with httpx.AsyncClient(timeout=60.0) as http:
        r = await http.post(f"{base}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
    text = (data.get("message", {}) or {}).get("content", "") or ""
    return CompletionResult(
        text=text,
        provider="ollama",
        model=model,
        input_tokens=data.get("prompt_eval_count"),
        output_tokens=data.get("eval_count"),
    )


# ── 하위 호환: 기존 코드가 get_client()를 호출하던 케이스 ─────────
# iam/ai_review.py 등은 client.messages.create()를 직접 호출하므로,
# Anthropic provider일 때만 native client를 반환한다. 다른 provider는 None.
def get_client():
    """⚠️ 하위 호환용. 새 코드는 `complete_json(...)`을 사용하라."""
    if get_provider() != "anthropic":
        return None
    return _anthropic_client()
