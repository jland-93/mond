"""
vLLM provider — env-based runtime 인식 + credentials 분기.

토큰 사용량 record/summary는 DB 의존이라 통합 테스트가 필요해 이 파일에선
순수 분기 로직만 검증한다.
"""

from app.ai.client import ProviderRuntime, _has_credentials, _runtime_from_env
from app.core.config import settings


def test_vllm_runtime_when_base_url_set(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "vllm")
    monkeypatch.setattr(settings, "VLLM_BASE_URL", "http://gpu-01:8000/v1")
    monkeypatch.setattr(settings, "VLLM_API_KEY", "EMPTY")
    monkeypatch.setattr(settings, "VLLM_MODEL_DEFAULT", "meta-llama/Meta-Llama-3.1-8B-Instruct")
    monkeypatch.setattr(settings, "VLLM_MODEL_DEEP", "meta-llama/Meta-Llama-3.1-70B-Instruct")
    rt = _runtime_from_env()
    assert rt is not None
    assert rt.provider == "vllm"
    assert rt.base_url == "http://gpu-01:8000/v1"
    assert rt.model_default.endswith("-8B-Instruct")
    assert rt.model_deep.endswith("-70B-Instruct")


def test_vllm_runtime_returns_none_without_base_url(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "vllm")
    monkeypatch.setattr(settings, "VLLM_BASE_URL", None)
    # 다른 provider 키도 없음
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    assert _runtime_from_env() is None


def test_has_credentials_vllm_needs_base_url():
    rt = ProviderRuntime(
        provider="vllm",
        api_key="EMPTY",
        base_url="http://gpu-01:8000/v1",
        region=None,
        model_default="m",
        model_deep="m",
        source="env",
    )
    assert _has_credentials(rt) is True


def test_has_credentials_vllm_missing_base_url_fails():
    rt = ProviderRuntime(
        provider="vllm",
        api_key="EMPTY",
        base_url=None,
        region=None,
        model_default="m",
        model_deep="m",
        source="env",
    )
    assert _has_credentials(rt) is False
