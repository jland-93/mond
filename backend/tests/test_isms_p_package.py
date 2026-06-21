"""
ISMS-P 인증 심사 패키지 — 통제 매핑 + markdown 직렬화 invariant.

build_package 자체는 DB 의존 통합 테스트라 여기선 통제 카탈로그가 안정적인지와
render_markdown이 빈 records · missing_* 보조 필드를 정상 처리하는지만 검증.
"""

from app.data.isms_p_controls import CODE_TO_CONTROL, ISMS_P_CONTROLS
from app.services.audit_package import _COLLECTORS, render_markdown


def test_controls_have_unique_codes():
    codes = [c.code for c in ISMS_P_CONTROLS]
    assert len(codes) == len(set(codes))


def test_controls_cover_10_core_areas():
    # v0.3 MVP는 10개 핵심 통제 — 줄거나 늘면 의도적 변경
    assert len(ISMS_P_CONTROLS) == 10


def test_every_control_has_registered_collector():
    """evidence_source가 모두 _COLLECTORS에 매핑되어 있어야 한다."""
    for c in ISMS_P_CONTROLS:
        assert c.evidence_source in _COLLECTORS, f"missing collector: {c.code} → {c.evidence_source}"


def test_code_to_control_lookup_works():
    assert CODE_TO_CONTROL["2.5.5"].name_ko.startswith("특수계정")


def test_render_markdown_with_minimal_sections():
    pkg = {
        "framework": "ISMS-P",
        "version": "v0.3",
        "generated_at": "2026-06-21T00:00:00+00:00",
        "period_days": 90,
        "since": "2026-03-23T00:00:00+00:00",
        "sections": [
            {
                "control": {
                    "code": "1.2.1",
                    "name_ko": "자산 식별 및 분류",
                    "summary_ko": "test summary",
                    "kisa_ref": "ISMS-P 1.2.1",
                    "evidence_source": "assets_inventory",
                },
                "evidence": {
                    "summary": "총 자산 3 · 환경 {'prod': 2, 'dev': 1}",
                    "records": [
                        {"id": 1, "name": "api", "type": "repository", "environment": "prod"},
                    ],
                },
            }
        ],
    }
    md = render_markdown(pkg)
    assert "# ISMS-P 인증 심사 증빙 패키지" in md
    assert "## 1.2.1" in md
    assert "자산 식별" in md
    assert "ISMS-P 1.2.1" in md
    assert "| id | name | type | environment |" in md  # 표 헤더
    # summary가 집계 요약 라인에 포함
    assert "**집계 요약**: 총 자산 3" in md


def test_render_markdown_handles_missing_mfa_list():
    pkg = {
        "framework": "ISMS-P",
        "version": "v0.3",
        "generated_at": "2026-06-21T00:00:00+00:00",
        "period_days": 30,
        "since": "2026-05-22T00:00:00+00:00",
        "sections": [
            {
                "control": {
                    "code": "2.5.5",
                    "name_ko": "특수계정",
                    "summary_ko": "...",
                    "kisa_ref": "x",
                    "evidence_source": "privileged_users",
                },
                "evidence": {
                    "summary": "권한자 2 · MFA 미등록 1",
                    "records": [],
                    "missing_mfa": ["alice@example.com"],
                },
            }
        ],
    }
    md = render_markdown(pkg)
    assert "시정 권고 — missing_mfa" in md
    assert "alice@example.com" in md


def test_render_markdown_escapes_pipe_in_record_values():
    pkg = {
        "framework": "ISMS-P",
        "version": "v0.3",
        "generated_at": "2026-06-21T00:00:00+00:00",
        "period_days": 30,
        "since": "2026-05-22T00:00:00+00:00",
        "sections": [
            {
                "control": {
                    "code": "1.2.1",
                    "name_ko": "자산",
                    "summary_ko": "x",
                    "kisa_ref": "x",
                    "evidence_source": "assets_inventory",
                },
                "evidence": {
                    "summary": "1",
                    "records": [{"name": "weird|name|with|pipes"}],
                },
            }
        ],
    }
    md = render_markdown(pkg)
    assert "weird\\|name\\|with\\|pipes" in md
