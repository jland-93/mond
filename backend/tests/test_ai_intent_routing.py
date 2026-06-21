"""
AI multi-provider 라우팅 — intent별 model 선택 invariant.

complete_json 자체는 외부 LLM 호출이라 단위 테스트가 어려워, 라우팅 결정
함수 _pick_model을 직접 검증한다.
"""

from app.ai.client import ProviderRuntime, _pick_model


def _rt() -> ProviderRuntime:
    return ProviderRuntime(
        provider="anthropic",
        api_key="k",
        base_url=None,
        region=None,
        model_default="claude-3-5-haiku-latest",
        model_deep="claude-sonnet-4-latest",
        source="db",
    )


def test_default_when_no_intent_no_deep():
    model, tier = _pick_model(_rt(), deep=False, intent=None)
    assert tier == "default"
    assert "haiku" in model.lower()


def test_explicit_deep_flag_wins():
    model, tier = _pick_model(_rt(), deep=True, intent=None)
    assert tier == "deep"
    assert "sonnet" in model.lower()


def test_remediation_intent_uses_deep():
    model, tier = _pick_model(_rt(), deep=False, intent="remediation")
    assert tier == "deep"
    assert "sonnet" in model.lower()


def test_explain_intent_uses_deep():
    _, tier = _pick_model(_rt(), deep=False, intent="explain")
    assert tier == "deep"


def test_deep_analysis_intent_uses_deep():
    _, tier = _pick_model(_rt(), deep=False, intent="deep_analysis")
    assert tier == "deep"


def test_triage_intent_keeps_default():
    _, tier = _pick_model(_rt(), deep=False, intent="triage")
    assert tier == "default"


def test_route_intent_keeps_default():
    _, tier = _pick_model(_rt(), deep=False, intent="route")
    assert tier == "default"


def test_unknown_intent_falls_back_to_default():
    _, tier = _pick_model(_rt(), deep=False, intent="something_unknown")
    assert tier == "default"


def test_deep_flag_overrides_lightweight_intent():
    # 명시적 deep=True는 intent가 triage여도 deep으로.
    _, tier = _pick_model(_rt(), deep=True, intent="triage")
    assert tier == "deep"
