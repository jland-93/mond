"""
ISMS-P (정보보호 및 개인정보보호 관리체계) 핵심 통제 매핑.

한국 인증 심사 대응의 'V0.3 MVP' — 80여 개 통제 전체가 아니라 가장 자주
점검되는 10개 핵심 통제만 Mond의 실 데이터(자산·접근통제·로그·발견사항·
권한요청 흐름)에 매핑한다.

각 통제는 (code, name, kisa_ref, evidence_source) 형태. evidence_source는
audit_package 서비스가 dispatch할 수 있는 enum 문자열이다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ISMSControl:
    code: str            # 통제 ID (ISMS-P 체계 + 내부 식별자)
    name_ko: str
    summary_ko: str
    evidence_source: str  # audit_package._collectors에 등록된 키
    kisa_ref: str         # KISA 안내서 챕터/항목 참조


# 통제 순서는 '관리체계 → 보호대책'을 따른다.
ISMS_P_CONTROLS: tuple[ISMSControl, ...] = (
    ISMSControl(
        code="1.1.5",
        name_ko="정책 수립 — 정보보호 정책 및 책임자",
        summary_ko="조직의 정보보호 정책 수립, 최고책임자(CISO) 지정 증빙. 본 패키지는 운영 중인 정책 카탈로그를 자동 수집한다.",
        evidence_source="policies_catalog",
        kisa_ref="ISMS-P 인증기준 1.1.5",
    ),
    ISMSControl(
        code="1.2.1",
        name_ko="자산 식별 및 분류",
        summary_ko="보호 대상 자산의 식별 · 환경(prod/staging/dev) 분류 · 담당자(owner) 지정. Mond Asset 카탈로그가 1:1 매핑된다.",
        evidence_source="assets_inventory",
        kisa_ref="ISMS-P 인증기준 1.2.1",
    ),
    ISMSControl(
        code="1.2.3",
        name_ko="위험 평가 — open finding 위험도 집계",
        summary_ko="자산별 잔여 위험(open finding)을 심각도별로 집계. 심사 시점의 잔여 위험 수준 증빙.",
        evidence_source="risk_assessment",
        kisa_ref="ISMS-P 인증기준 1.2.3",
    ),
    ISMSControl(
        code="2.5.1",
        name_ko="사용자 접근권한 부여 절차",
        summary_ko="권한 요청 → AI 1차 검토 → 담당자 결재 → 자동 부여 → 자동 회수 흐름 전체를 audit log로 증빙.",
        evidence_source="access_request_lifecycle",
        kisa_ref="ISMS-P 인증기준 2.5.1",
    ),
    ISMSControl(
        code="2.5.5",
        name_ko="특수계정 관리 — ADMIN/Reviewer + MFA",
        summary_ko="조직 내 ADMIN · Reviewer 권한자 명단과 MFA 등록 상태. ISMS-P에서 가장 민감하게 보는 항목.",
        evidence_source="privileged_users",
        kisa_ref="ISMS-P 인증기준 2.5.5",
    ),
    ISMSControl(
        code="2.6.1",
        name_ko="접근통제 — 네트워크/응용 통제 정책",
        summary_ko="Mond에 등록된 정책(builtin/OPA) 중 접근통제 관련 항목의 가동 상태.",
        evidence_source="access_control_policies",
        kisa_ref="ISMS-P 인증기준 2.6.1",
    ),
    ISMSControl(
        code="2.9.1",
        name_ko="로그 기록 및 점검 — audit log 보존",
        summary_ko="권한 결정/부여/회수의 시계열 audit log. 최근 N일 기간 내 이벤트 수와 sample을 첨부.",
        evidence_source="audit_log_recent",
        kisa_ref="ISMS-P 인증기준 2.9.1",
    ),
    ISMSControl(
        code="2.10.2",
        name_ko="패치/취약점 관리 — CVE 처리 현황",
        summary_ko="Trivy/Semgrep/Nuclei 스캐너로 검출된 CVE의 처리 상태(triaged/fixed/wontfix). 처리율 + 잔여 critical/high.",
        evidence_source="vulnerability_handling",
        kisa_ref="ISMS-P 인증기준 2.10.2",
    ),
    ISMSControl(
        code="2.11.1",
        name_ko="사고 대응 — 비정상 행위 발견 시 처리",
        summary_ko="critical/high finding의 인지 → 분류(triaged) → 진행(in_progress) → 해결(fixed) 흐름 통계 + 평균 처리 시간.",
        evidence_source="incident_response",
        kisa_ref="ISMS-P 인증기준 2.11.1",
    ),
    ISMSControl(
        code="3.2.1",
        name_ko="개인정보 처리 시스템 식별 — production 자산",
        summary_ko="개인정보를 처리하는 production 자산 식별 (environment=production). 별도 보호 의무가 따른다.",
        evidence_source="production_assets",
        kisa_ref="ISMS-P 인증기준 3.2.1",
    ),
)


CODE_TO_CONTROL: dict[str, ISMSControl] = {c.code: c for c in ISMS_P_CONTROLS}
