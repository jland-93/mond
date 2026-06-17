"""
🌙 Finding fingerprint 안정성 테스트

같은 (scanner, rule, asset, location) 조합은 항상 같은 fingerprint를 내야 하고,
다른 조합이면 달라야 한다. dedup의 코어 invariant.
"""

from app.services.finding import build_fingerprint


def test_same_input_same_fingerprint():
    a = build_fingerprint(scanner="trivy", rule_id="CVE-2024-X", asset_id=1, location="docker.io/x")
    b = build_fingerprint(scanner="trivy", rule_id="CVE-2024-X", asset_id=1, location="docker.io/x")
    assert a == b


def test_different_scanner_differs():
    a = build_fingerprint(scanner="trivy", rule_id="R", asset_id=1, location=None)
    b = build_fingerprint(scanner="semgrep", rule_id="R", asset_id=1, location=None)
    assert a != b


def test_different_rule_differs():
    a = build_fingerprint(scanner="trivy", rule_id="A", asset_id=1, location=None)
    b = build_fingerprint(scanner="trivy", rule_id="B", asset_id=1, location=None)
    assert a != b


def test_different_asset_differs():
    a = build_fingerprint(scanner="trivy", rule_id="R", asset_id=1, location=None)
    b = build_fingerprint(scanner="trivy", rule_id="R", asset_id=2, location=None)
    assert a != b


def test_location_distinguishes_within_same_asset():
    a = build_fingerprint(scanner="semgrep", rule_id="R", asset_id=1, location="a.py:10")
    b = build_fingerprint(scanner="semgrep", rule_id="R", asset_id=1, location="b.py:20")
    assert a != b


def test_none_and_empty_location_equivalent():
    """None과 빈 문자열은 같은 fingerprint를 만들어야 한다 (dedup 일관성)."""
    a = build_fingerprint(scanner="trivy", rule_id="R", asset_id=1, location=None)
    b = build_fingerprint(scanner="trivy", rule_id="R", asset_id=1, location="")
    assert a == b


def test_fingerprint_length_64():
    fp = build_fingerprint(scanner="trivy", rule_id="R", asset_id=1, location="x")
    assert len(fp) == 64
    assert set(fp).issubset(set("0123456789abcdef"))
