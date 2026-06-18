"""
Regulations 데이터 무결성 테스트

DB 의존성 없이 정적 카탈로그가 일관성 있는지 검증.
"""

from app.data.regulations import (
    REGULATIONS,
    SCENARIOS,
    TIMING,
    regulation_dict,
    scenario_dict,
)


def test_all_regulations_have_required_fields():
    for code, reg in REGULATIONS.items():
        assert reg.code == code, f"{code}: code 일치"
        assert reg.name_ko and reg.name_en, f"{code}: 양 언어 이름 필요"
        assert reg.summary_ko and reg.summary_en, f"{code}: 양 언어 요약 필요"
        assert reg.jurisdiction in {"KR", "EU", "US", "GLOBAL"}, f"{code}: 관할 enum"
        assert reg.timings, f"{code}: 적용 시점 최소 1개"
        for t in reg.timings:
            assert t in TIMING, f"{code}: 모르는 시점 키 {t}"
        assert len(reg.obligations_ko) == len(reg.obligations_en), (
            f"{code}: 의무 항목 ko/en 개수 일치"
        )
        assert reg.references, f"{code}: 참고 링크 최소 1개"


def test_scenarios_reference_existing_regulations():
    for sid, scenario in SCENARIOS.items():
        assert scenario.id == sid
        assert scenario.applicable, f"{sid}: 적용 규제 최소 1개"
        for code in scenario.applicable:
            assert code in REGULATIONS, f"{sid}: 모르는 규제 {code}"


def test_regulation_dict_ko_en_disjoint():
    """규제 한 건의 ko/en 출력이 서로 다른 필드만 노출하는지."""
    r_ko = regulation_dict("K-PIPA", "ko")
    r_en = regulation_dict("K-PIPA", "en")
    assert r_ko and r_en
    assert "name_ko" not in r_ko and "summary_ko" not in r_ko
    assert "name_en" not in r_en and "summary_en" not in r_en
    assert r_ko["name"] != r_en["name"]


def test_scenario_dict_includes_regulations_payload():
    sc = scenario_dict("kr-personal-data", "ko")
    assert sc is not None
    assert sc["id"] == "kr-personal-data"
    assert sc["regulations"] and len(sc["regulations"]) == len(sc["applicable"])
    assert any(r["code"] == "K-PIPA" for r in sc["regulations"])


def test_unknown_codes_return_none():
    assert regulation_dict("DOES-NOT-EXIST", "ko") is None
    assert scenario_dict("unknown-scenario", "ko") is None


def test_korea_scenarios_present():
    """한국 비즈니스 시나리오가 누락 없이 들어 있는지."""
    must_have = {
        "kr-personal-data",
        "kr-payment",
        "kr-financial",
        "kr-public",
    }
    assert must_have.issubset(SCENARIOS.keys())


def test_global_regulations_present():
    must_have = {"GDPR", "HIPAA", "PCI-DSS", "SOC2", "ISO-27001"}
    assert must_have.issubset(REGULATIONS.keys())
