"""
OPA Rego 평가 어댑터 테스트

OPA 바이너리 미설치 환경에선 skip. CI 이미지에는 Dockerfile이 OPA를
번들하므로 통과한다.
"""

import pytest

from app.services import opa as opa_service

pytestmark = pytest.mark.asyncio

REGO_BASIC = """package mond

deny contains msg if {
    some f in input.findings
    f.rule_id == "CVE-2024-0001"
    msg := sprintf("blocked %s (%s)", [f.rule_id, f.severity])
}
"""


def _skip_if_no_opa() -> None:
    if not opa_service.is_available():
        pytest.skip("OPA 바이너리 미설치 — 이 테스트는 backend 이미지/PATH의 'opa'를 요구")


async def test_opa_deny_when_matching():
    _skip_if_no_opa()
    r = await opa_service.evaluate(
        REGO_BASIC,
        {"findings": [{"rule_id": "CVE-2024-0001", "severity": "high"}]},
    )
    assert r.error is None
    assert r.blocked is True
    assert len(r.deny) == 1
    assert "CVE-2024-0001" in r.deny[0]


async def test_opa_pass_when_no_match():
    _skip_if_no_opa()
    r = await opa_service.evaluate(
        REGO_BASIC,
        {"findings": [{"rule_id": "CVE-9999", "severity": "low"}]},
    )
    assert r.error is None
    assert r.blocked is False
    assert r.deny == []


async def test_opa_syntax_error_returns_error():
    _skip_if_no_opa()
    r = await opa_service.evaluate(
        "package mond\nthis is not valid rego",
        {"findings": []},
    )
    # 컴파일 실패 → error 채워지고 blocked False
    assert r.error is not None
    assert r.blocked is False


def test_unavailable_returns_clear_message(monkeypatch):
    # opa_binary가 None이라고 가정 → 호출 즉시 error 메시지 반환
    monkeypatch.setattr(opa_service, "opa_binary", lambda: None)
    import asyncio

    r = asyncio.run(opa_service.evaluate(REGO_BASIC, {"findings": []}))
    assert r.available is False
    assert r.blocked is False
    assert "미설치" in (r.error or "")
