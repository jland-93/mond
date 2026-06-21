"""
PR Bot 코멘트 포맷 — 외부 호출 없는 순수 함수만.
"""

from app.models.finding import Finding, FindingStatus, Severity
from app.models.scan import Scan, ScanStatus, ScanTrigger
from app.services.pr_bot import _severity_summary, format_pr_comment


def _f(severity: Severity, rule_id: str, title: str) -> Finding:
    return Finding(
        asset_id=1,
        rule_id=rule_id,
        title=title,
        severity=severity,
        status=FindingStatus.NEW,
        scanner="trivy",
        references=[],
        extra={},
        fingerprint="fp",
    )


def _scan() -> Scan:
    return Scan(
        asset_id=1,
        scanner="trivy",
        trigger=ScanTrigger.WEBHOOK,
        status=ScanStatus.COMPLETED,
        duration_ms=42,
    )


def test_severity_summary_ranks_critical_first():
    fs = [
        _f(Severity.LOW, "L1", "low one"),
        _f(Severity.CRITICAL, "C1", "crit one"),
        _f(Severity.HIGH, "H1", "high one"),
    ]
    counter, top = _severity_summary(fs)
    assert counter["critical"] == 1
    assert counter["high"] == 1
    assert top[0].severity == Severity.CRITICAL
    assert top[1].severity == Severity.HIGH


def test_comment_no_findings():
    body = format_pr_comment(
        scan=_scan(),
        asset_name="my-repo",
        findings=[],
        ai_oneliner=None,
    )
    assert "No findings" in body
    assert "my-repo" in body


def test_comment_top_findings_table():
    fs = [
        _f(Severity.CRITICAL, "CVE-2024-0001", "critical pkg"),
        _f(Severity.HIGH, "CVE-2024-0002", "high pkg"),
        _f(Severity.MEDIUM, "RULE-3", "medium issue"),
    ]
    body = format_pr_comment(
        scan=_scan(),
        asset_name="my-repo",
        findings=fs,
        ai_oneliner=None,
    )
    assert "**3** finding" in body
    assert "Top findings" in body
    assert "CVE-2024-0001" in body
    # severity 표시
    assert "critical" in body
    assert "high" in body


def test_comment_includes_ai_oneliner_when_provided():
    fs = [_f(Severity.CRITICAL, "X", "critical pkg")]
    body = format_pr_comment(
        scan=_scan(),
        asset_name="my-repo",
        findings=fs,
        ai_oneliner="실제 호출이 lb 뒤에 있어 severity high로 강등 가능",
    )
    assert "🤖" in body
    assert "lb 뒤" in body


def test_comment_pipe_escaped_in_title():
    fs = [_f(Severity.HIGH, "rule|x", "title|with|pipes")]
    body = format_pr_comment(
        scan=_scan(),
        asset_name="my-repo",
        findings=fs,
        ai_oneliner=None,
    )
    # 마크다운 표를 깨지 않도록 escape
    assert "\\|" in body
