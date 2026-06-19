"""
AI 프롬프트 PII redaction 테스트

외부 LLM provider 호출 전 마스킹의 invariant — 패턴이 매칭되면 항상 같은
placeholder가 들어가고, 매칭이 없으면 원문이 그대로 유지된다.
"""

from app.ai.redaction import redact_prompt


def test_email_redacted():
    r = redact_prompt("contact me at kim@example.com please")
    assert "[REDACTED_EMAIL]" in r.text
    assert "kim@example.com" not in r.text
    assert r.counts["email"] == 1


def test_korean_phone_redacted():
    r = redact_prompt("내 번호 010-1234-5678 입니다")
    assert "[REDACTED_PHONE]" in r.text
    assert r.counts["phone"] == 1


def test_rrn_redacted():
    r = redact_prompt("주민번호 900101-1234567")
    assert "[REDACTED_RRN]" in r.text
    assert r.counts["rrn"] == 1


def test_aws_access_key_redacted():
    r = redact_prompt("AKIAIOSFODNN7EXAMPLE")
    assert "[REDACTED_AWS_KEY]" in r.text


def test_github_token_redacted():
    r = redact_prompt("ghp_abcdefghijklmnopqrstuvwxyz1234567890")
    assert "[REDACTED_TOKEN]" in r.text


def test_jwt_redacted():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    r = redact_prompt(f"token={jwt}")
    assert "[REDACTED_JWT]" in r.text
    assert jwt not in r.text


def test_luhn_valid_cc_redacted():
    # Visa test card — Luhn 통과
    r = redact_prompt("card 4111 1111 1111 1111 ok")
    assert "[REDACTED_CC]" in r.text


def test_random_digits_not_redacted_as_cc():
    # Luhn 통과 못하는 16자리는 카드로 오인하지 않음
    r = redact_prompt("rule 1234567890123456 fired")
    assert "[REDACTED_CC]" not in r.text


def test_no_pii_passes_through():
    text = "scan nginx asset for CVEs in last 7 days"
    r = redact_prompt(text)
    assert r.text == text
    assert r.counts == {}


def test_multiple_kinds_counted():
    r = redact_prompt("a@b.com and 010-1111-2222 and ghp_abcdefghijklmnopqrstuvwxyz12345")
    assert r.counts.get("email") == 1
    assert r.counts.get("phone") == 1
    assert r.counts.get("github_token") == 1
    assert r.total == 3


def test_empty_input():
    r = redact_prompt("")
    assert r.text == ""
    assert r.counts == {}
