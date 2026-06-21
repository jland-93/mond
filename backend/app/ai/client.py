"""
LLM provider 추상화 — DB 우선 + ENV fallback

런타임 동작
---------
1) 관리자가 UI에서 등록한 `AIProviderConfig` 중 `is_default=True, enabled=True` 행이 있으면 그것을 사용.
2) 없으면 .env의 `AI_PROVIDER` + 해당 키를 사용 (하위 호환).
3) 둘 다 없으면 기본 규칙(heuristic) 모드.

지원 provider
-------------
- anthropic : Anthropic Claude (직접 API)
- openai    : OpenAI / Azure OpenAI / OpenAI-compatible gateway
- bedrock   : AWS Bedrock (Anthropic on Bedrock, IAM 자격으로)
- ollama    : 로컬 LLM (Ollama / vLLM 호환)

사용처는 다음만 알면 된다:
- `await is_enabled(db)` — True면 provider가 실제로 호출 가능
- `await get_provider(db)` — 'anthropic' / 'openai' / 'bedrock' / 'ollama' / None
- `await complete_json(db, system, user, deep=False) -> CompletionResult | None`
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.secrets import decrypt
from app.core.config import settings
from app.core.logging import get_logger
from app.models.ai_provider import AIProviderConfig

logger = get_logger(__name__)


@dataclass
class ProviderRuntime:
    """런타임 시점에 합성된 provider 설정 — DB 또는 ENV 출처."""

    provider: str          # 'anthropic' / 'openai' / 'bedrock' / 'ollama'
    api_key: str | None
    base_url: str | None
    region: str | None
    model_default: str
    model_deep: str
    source: str            # 'db' / 'env' — UI 디버그용


@dataclass
class CompletionResult:
    """provider-agnostic 응답."""

    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


# ── 런타임 조회 ─────────────────────────────────────────────────
async def get_runtime(db: AsyncSession) -> ProviderRuntime | None:
    """DB의 default provider → 없으면 ENV → 둘 다 없으면 None."""
    # 1) DB 우선
    row = (
        await db.execute(
            select(AIProviderConfig)
            .where(AIProviderConfig.enabled.is_(True))
            .where(AIProviderConfig.is_default.is_(True))
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is not None:
        rt = _runtime_from_db(row)
        if _has_credentials(rt):
            return rt
        logger.warning("ai_default_provider_missing_credentials", provider=row.provider)

    # 2) ENV fallback
    return _runtime_from_env()


def _runtime_from_db(row: AIProviderConfig) -> ProviderRuntime:
    api_key = decrypt(row.api_key_encrypted)
    provider = row.provider
    return ProviderRuntime(
        provider=provider,
        api_key=api_key,
        base_url=row.base_url,
        region=row.region or (settings.BEDROCK_REGION if provider == "bedrock" else None),
        model_default=row.model_default or _env_model_default(provider),
        model_deep=row.model_deep or _env_model_deep(provider),
        source="db",
    )


def _runtime_from_env() -> ProviderRuntime | None:
    provider = (settings.AI_PROVIDER or "").lower().strip()
    if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        return ProviderRuntime(
            provider="anthropic",
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=None,
            region=None,
            model_default=settings.AI_MODEL_DEFAULT,
            model_deep=settings.AI_MODEL_DEEP,
            source="env",
        )
    if provider == "openai" and settings.OPENAI_API_KEY:
        return ProviderRuntime(
            provider="openai",
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            region=None,
            model_default=settings.OPENAI_MODEL_DEFAULT,
            model_deep=settings.OPENAI_MODEL_DEEP,
            source="env",
        )
    if provider == "bedrock":
        return ProviderRuntime(
            provider="bedrock",
            api_key=None,  # boto3 자격 자동 감지
            base_url=None,
            region=settings.BEDROCK_REGION,
            model_default=settings.BEDROCK_MODEL_DEFAULT,
            model_deep=settings.BEDROCK_MODEL_DEEP,
            source="env",
        )
    if provider == "ollama":
        return ProviderRuntime(
            provider="ollama",
            api_key=None,
            base_url=settings.OLLAMA_BASE_URL,
            region=None,
            model_default=settings.OLLAMA_MODEL_DEFAULT,
            model_deep=settings.OLLAMA_MODEL_DEEP,
            source="env",
        )
    if provider == "vllm" and settings.VLLM_BASE_URL:
        # vLLM은 OpenAI-호환 server이므로 _call_openai 흐름을 그대로 탄다.
        # provider 라벨은 'vllm'으로 유지해 usage log/대시보드 구분 가능.
        return ProviderRuntime(
            provider="vllm",
            api_key=settings.VLLM_API_KEY or "EMPTY",
            base_url=settings.VLLM_BASE_URL,
            region=None,
            model_default=settings.VLLM_MODEL_DEFAULT,
            model_deep=settings.VLLM_MODEL_DEEP,
            source="env",
        )
    return None


def _has_credentials(rt: ProviderRuntime) -> bool:
    if rt.provider in {"anthropic", "openai"}:
        return bool(rt.api_key)
    if rt.provider == "bedrock":
        # boto3가 IAM 자격을 자동 감지 — region만 있으면 OK
        return bool(rt.region)
    if rt.provider in {"ollama", "vllm"}:
        return bool(rt.base_url)
    return False


def _env_model_default(provider: str) -> str:
    return {
        "anthropic": settings.AI_MODEL_DEFAULT,
        "openai": settings.OPENAI_MODEL_DEFAULT,
        "bedrock": settings.BEDROCK_MODEL_DEFAULT,
        "ollama": settings.OLLAMA_MODEL_DEFAULT,
    }.get(provider, "")


def _env_model_deep(provider: str) -> str:
    return {
        "anthropic": settings.AI_MODEL_DEEP,
        "openai": settings.OPENAI_MODEL_DEEP,
        "bedrock": settings.BEDROCK_MODEL_DEEP,
        "ollama": settings.OLLAMA_MODEL_DEEP,
    }.get(provider, "")


# ── 호출부에 노출되는 4개 API ────────────────────────────────────
async def is_enabled(db: AsyncSession) -> bool:
    return await get_runtime(db) is not None


async def get_provider(db: AsyncSession) -> str | None:
    rt = await get_runtime(db)
    return rt.provider if rt else None


async def current_model_label(db: AsyncSession) -> str:
    rt = await get_runtime(db)
    if rt is None:
        return "rule-based"
    return f"{rt.provider}:{rt.model_default}"


# intent별 라우팅 규칙 — model_default(빠르고 저비용) vs model_deep(추론 정확도).
# remediation/explain/deep_analysis 같은 '깊이가 필요한' intent는 자동으로 deep 모델로.
# 그 외(triage/route/list_findings/scan)는 default 모델로 비용/지연 최소화.
_DEEP_INTENTS = {"remediation", "explain", "deep_analysis"}


def _pick_model(rt: ProviderRuntime, *, deep: bool, intent: str | None) -> tuple[str, str]:
    """라우팅 결정. (model, tier='default'|'deep') 반환."""
    if deep:
        return rt.model_deep, "deep"
    if intent and intent in _DEEP_INTENTS:
        return rt.model_deep, "deep"
    return rt.model_default, "default"


async def complete_json(
    db: AsyncSession,
    system: str,
    user: str,
    *,
    deep: bool = False,
    max_tokens: int | None = None,
    intent: str | None = None,
) -> CompletionResult | None:
    """provider별 LLM 호출. 실패하면 None — 호출부는 fallback 처리.

    intent별 라우팅:
      - 'remediation' / 'explain' / 'deep_analysis' → model_deep (느리지만 정확)
      - 그 외(triage/route 등) → model_default (빠르고 저비용)
      - `deep=True`는 intent와 무관하게 deep 강제 (하위 호환)
    """
    rt = await get_runtime(db)
    if rt is None:
        return None
    model, tier = _pick_model(rt, deep=deep, intent=intent)
    if intent:
        logger.info("ai_intent_routed", provider=rt.provider, intent=intent, tier=tier, model=model)
    max_tokens = max_tokens or settings.AI_MAX_TOKENS

    result: CompletionResult | None = None
    failed = False
    try:
        if rt.provider == "anthropic":
            result = await _call_anthropic(rt, system, user, model, max_tokens)
        elif rt.provider == "openai":
            result = await _call_openai(rt, system, user, model, max_tokens)
        elif rt.provider == "bedrock":
            result = await _call_bedrock(rt, system, user, model, max_tokens)
        elif rt.provider == "ollama":
            result = await _call_ollama(rt, system, user, model, max_tokens)
        elif rt.provider == "vllm":
            # vLLM은 OpenAI-호환 API. 같은 호출 흐름 재사용, provider 라벨만 vllm.
            r = await _call_openai(rt, system, user, model, max_tokens)
            result = CompletionResult(
                text=r.text,
                provider="vllm",
                model=r.model,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
            )
    except Exception as exc:
        logger.warning("ai_complete_failed", provider=rt.provider, model=model, error=str(exc))
        failed = True

    # 사용량 기록 — 실패해도 행 1건 남겨 호출수가 비용 0로 카운트되게.
    try:
        from app.services import ai_usage as ai_usage_service
        await ai_usage_service.record(
            db,
            provider=rt.provider,
            model=model,
            tier=tier,
            intent=intent,
            input_tokens=result.input_tokens if result else 0,
            output_tokens=result.output_tokens if result else 0,
            failed=failed or result is None,
        )
    except Exception as exc:  # usage 기록 실패가 호출을 막지 않게
        logger.warning("ai_usage_record_failed", error=str(exc))

    return result


# ── Anthropic ───────────────────────────────────────────────────
async def _call_anthropic(rt: ProviderRuntime, system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=rt.api_key)
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


# ── OpenAI / Azure / 호환 게이트웨이 ───────────────────────────
async def _call_openai(rt: ProviderRuntime, system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    from openai import AsyncOpenAI

    kwargs: dict = {"api_key": rt.api_key}
    if rt.base_url:
        kwargs["base_url"] = rt.base_url
    client = AsyncOpenAI(**kwargs)
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


# ── AWS Bedrock (Anthropic on Bedrock) ─────────────────────────
async def _call_bedrock(rt: ProviderRuntime, system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    if not model.startswith("anthropic."):
        raise ValueError(f"unsupported bedrock model (only anthropic.* supported): {model}")

    import asyncio

    import boto3

    client = boto3.client("bedrock-runtime", region_name=rt.region or "us-east-1")
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
    )
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


# ── Ollama / vLLM (로컬) ───────────────────────────────────────
async def _call_ollama(rt: ProviderRuntime, system: str, user: str, model: str, max_tokens: int) -> CompletionResult:
    import httpx

    base = (rt.base_url or settings.OLLAMA_BASE_URL).rstrip("/")
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
