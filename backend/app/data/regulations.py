"""
정보보안 규제 / 사업 시나리오 데이터

"우리 사업/데이터엔 어떤 규제가 적용되고 언제 무엇을 해야 하나?"에 답하기 위한 시드.
모든 항목은 ko/en 양 언어를 제공해 UI에서 그대로 사용한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


# ── 적용 시점 (timing) 분류 ─────────────────────────────────────────
TIMING = {
    "pre_business": {
        "ko": "사업 시작 전 (사업자 등록 · 약관 고시 · 위탁 계약)",
        "en": "Before launching the business (registration · ToS · DPA contracts)",
    },
    "pre_launch": {
        "ko": "서비스 출시 전 (보안 점검 · 인증 취득 · DPIA)",
        "en": "Before service launch (security review · certification · DPIA)",
    },
    "operational": {
        "ko": "운영 중 상시 (모니터링 · 교육 · 백업 · DLP)",
        "en": "Ongoing operations (monitoring · training · backup · DLP)",
    },
    "audit": {
        "ko": "정기 감사 / 갱신 (연 1회 등)",
        "en": "Periodic audit / renewal (annual etc.)",
    },
    "incident": {
        "ko": "사고 발생 시 (신고 · 통지 · 포렌식)",
        "en": "Upon incident (notification · disclosure · forensics)",
    },
}


# ── 규제 카탈로그 ─────────────────────────────────────────────────────
@dataclass
class Regulation:
    code: str
    name_ko: str
    name_en: str
    jurisdiction: str  # KR / EU / US / GLOBAL
    summary_ko: str
    summary_en: str
    timings: list[str]      # TIMING keys
    obligations_ko: list[str]
    obligations_en: list[str]
    references: list[str]


REGULATIONS: dict[str, Regulation] = {
    "K-PIPA": Regulation(
        code="K-PIPA",
        name_ko="개인정보보호법 (PIPA)",
        name_en="Personal Information Protection Act (Korea)",
        jurisdiction="KR",
        summary_ko=(
            "한국에서 개인정보를 처리하는 모든 사업자가 따라야 하는 일반법. "
            "수집·이용·제공·파기 절차, 동의 요건, 처리방침 고시, 안전성 확보조치를 규정."
        ),
        summary_en=(
            "Korea's general law for personal data handling. Covers consent, "
            "purpose limitation, privacy policy disclosure, and safeguards."
        ),
        timings=["pre_business", "pre_launch", "operational", "incident"],
        obligations_ko=[
            "개인정보처리방침을 홈페이지에 고시",
            "수집·이용 동의 분리 및 명시",
            "위탁 시 DPA(처리위탁계약) 체결",
            "유출 시 72시간 내 신고 + 정보주체 통지",
            "내부관리계획 및 안전성 확보조치 (암호화·접근통제·접속기록)",
        ],
        obligations_en=[
            "Publish privacy policy on the public site",
            "Separate, explicit consent per processing purpose",
            "DPA contract with processors",
            "Breach notification within 72 hours to KISA + data subjects",
            "Internal mgmt plan + safeguards (encryption · ACL · access logs)",
        ],
        references=[
            "https://www.law.go.kr/법령/개인정보보호법",
            "https://www.pipc.go.kr/",
        ],
    ),
    "K-ISMS-P": Regulation(
        code="K-ISMS-P",
        name_ko="ISMS-P (정보보호 및 개인정보보호 관리체계 인증)",
        name_en="ISMS-P (Information Security & PIM System certification, Korea)",
        jurisdiction="KR",
        summary_ko=(
            "한국인터넷진흥원(KISA) 주관 통합 인증. 정보통신서비스 매출/이용자 일정 규모 이상 "
            "사업자 의무. 80여 개 통제항목과 정기 사후 심사."
        ),
        summary_en=(
            "KISA-administered integrated certification. Mandatory for large ICT service "
            "providers; ~80 controls with annual surveillance."
        ),
        timings=["pre_launch", "operational", "audit"],
        obligations_ko=[
            "정보보호 정책 수립 및 최고책임자 지정",
            "자산 분류 및 위험분석 (연 1회 이상)",
            "접근통제 / 암호화 / 로그 / 백업 / 사고대응 절차",
            "외부 위탁 보안관리",
            "정기 사후 심사 (인증 후 매년)",
        ],
        obligations_en=[
            "Establish security policy + appoint CISO",
            "Asset classification + annual risk assessment",
            "Access control · encryption · logging · backup · IR",
            "3rd-party processor management",
            "Annual surveillance audit after certification",
        ],
        references=["https://isms.kisa.or.kr/"],
    ),
    "K-EFSA": Regulation(
        code="K-EFSA",
        name_ko="전자금융감독규정",
        name_en="Electronic Financial Supervision Regulations (Korea)",
        jurisdiction="KR",
        summary_ko=(
            "전자금융업/금융회사가 따라야 하는 보안 감독 규정. 망분리, 보안 SDLC, "
            "전산자료 보호, 정보보호 인력·예산 비율 등."
        ),
        summary_en=(
            "Security supervision rules for e-finance providers in Korea: network segregation, "
            "secure SDLC, data protection, mandated security staff/budget ratios."
        ),
        timings=["pre_launch", "operational", "audit", "incident"],
        obligations_ko=[
            "내부망/외부망 망분리 (DMZ)",
            "보안 SDLC + 취약점 점검 (분기)",
            "정보보호 예산/인력 비율 (총 IT의 7%/5% 이상)",
            "전자금융사고 신고 (즉시·24시간 내 상세)",
        ],
        obligations_en=[
            "Network segregation (DMZ)",
            "Secure SDLC + quarterly vulnerability scanning",
            "Security budget/staff ratio (≥7% / ≥5% of IT)",
            "Incident reporting (immediate; detail within 24h)",
        ],
        references=["https://www.fss.or.kr/"],
    ),
    "K-CSAP": Regulation(
        code="K-CSAP",
        name_ko="CSAP (클라우드 보안인증, 공공기관)",
        name_en="CSAP (Cloud Security Assurance Program, Korean public sector)",
        jurisdiction="KR",
        summary_ko=(
            "공공기관에 클라우드 서비스를 제공하려면 필수. IaaS/SaaS/DaaS 별 등급, "
            "물리적·관리적·기술적 보호조치 평가."
        ),
        summary_en=(
            "Required to sell cloud services to Korean public agencies. IaaS/SaaS/DaaS tiers, "
            "physical/managerial/technical control assessment."
        ),
        timings=["pre_launch", "audit"],
        obligations_ko=[
            "데이터·시스템의 국내 위치 (Data residency)",
            "기관용 별도 운영 구획 (전용 환경)",
            "암호화 모듈 검증 (KCMVP)",
        ],
        obligations_en=[
            "Data and systems located in Korea",
            "Dedicated operational zone for public sector",
            "KCMVP-validated cryptographic modules",
        ],
        references=["https://isms.kisa.or.kr/"],
    ),
    "GDPR": Regulation(
        code="GDPR",
        name_ko="GDPR (EU 일반개인정보보호법)",
        name_en="GDPR (EU General Data Protection Regulation)",
        jurisdiction="EU",
        summary_ko=(
            "EU 거주자의 개인정보를 처리하면 비EU 사업자도 적용. DPIA, DPO 지정, "
            "정보주체 권리 보장, 72시간 신고."
        ),
        summary_en=(
            "Applies to anyone processing EU residents' personal data. Requires DPIA, "
            "DPO in some cases, data subject rights, 72h breach notification."
        ),
        timings=["pre_business", "pre_launch", "operational", "incident", "audit"],
        obligations_ko=[
            "법적 근거 명시 (6 lawful bases 중 하나)",
            "DPIA (고위험 처리 시)",
            "DPO 지정 (대규모/민감정보 처리)",
            "정보주체 권리 응답 (열람·삭제·이동)",
            "유출 72시간 신고 + 영향 큰 경우 통지",
        ],
        obligations_en=[
            "Document lawful basis (one of the six)",
            "DPIA for high-risk processing",
            "Appoint DPO for large-scale or sensitive processing",
            "Honor data subject rights (access · erasure · portability)",
            "Breach notification within 72h + notify subjects when high risk",
        ],
        references=["https://gdpr.eu/", "https://edpb.europa.eu/"],
    ),
    "EU-AI-ACT": Regulation(
        code="EU-AI-ACT",
        name_ko="EU AI Act (AI 규제법)",
        name_en="EU AI Act",
        jurisdiction="EU",
        summary_ko=(
            "AI 시스템을 위험 등급(금지·고위험·제한·최소)으로 구분하고 고위험에 무거운 의무 부과. "
            "2026년부터 단계 시행."
        ),
        summary_en=(
            "Risk-based classification of AI systems (prohibited · high · limited · minimal). "
            "Phased enforcement from 2026."
        ),
        timings=["pre_launch", "operational", "audit"],
        obligations_ko=[
            "위험 등급 분류 + 문서화",
            "고위험 시 데이터 거버넌스, 로깅, 인적 감독",
            "GPAI(범용 AI) 모델은 별도 요건 (트랜스파런시, 저작권 정책)",
        ],
        obligations_en=[
            "Risk-class classification + documentation",
            "High-risk: data governance · logging · human oversight",
            "GPAI models: extra obligations (transparency · copyright policy)",
        ],
        references=["https://artificialintelligenceact.eu/"],
    ),
    "HIPAA": Regulation(
        code="HIPAA",
        name_ko="HIPAA (미국 의료정보보호법)",
        name_en="HIPAA (Health Insurance Portability and Accountability Act, US)",
        jurisdiction="US",
        summary_ko=(
            "미국 의료 정보(PHI)를 처리하는 모든 주체에 적용. 행정·물리·기술적 보호조치, "
            "BAA 계약, 사고 통지."
        ),
        summary_en=(
            "Applies to anyone handling US Protected Health Information. Administrative, "
            "physical, technical safeguards + BAA contracts + breach notification."
        ),
        timings=["pre_business", "pre_launch", "operational", "incident"],
        obligations_ko=[
            "BAA(사업체 부속 계약) 체결",
            "PHI 암호화 (전송·저장)",
            "접근 통제 + 감사 로그 (6년 보관)",
            "유출 시 60일 내 통지",
        ],
        obligations_en=[
            "Sign BAA with business associates",
            "Encrypt PHI in transit and at rest",
            "Access control + audit logs (6-year retention)",
            "Breach notification within 60 days",
        ],
        references=["https://www.hhs.gov/hipaa/"],
    ),
    "PCI-DSS": Regulation(
        code="PCI-DSS",
        name_ko="PCI DSS (카드결제 정보 보호 표준)",
        name_en="PCI DSS (Payment Card Industry Data Security Standard)",
        jurisdiction="GLOBAL",
        summary_ko=(
            "카드 데이터를 저장·처리·전송하는 모든 사업자에 적용. v4.0 (2025-03 강제)."
        ),
        summary_en=(
            "Applies to any merchant/processor handling cardholder data. v4.0 fully enforced from 2025-03."
        ),
        timings=["pre_launch", "operational", "audit"],
        obligations_ko=[
            "카드번호(PAN) 저장 시 토큰화/암호화",
            "분기별 외부 ASV 스캔",
            "연간 침투 테스트",
            "보안 SDLC + 변경관리",
        ],
        obligations_en=[
            "Tokenize/encrypt PAN at rest",
            "Quarterly external ASV scans",
            "Annual penetration test",
            "Secure SDLC + change management",
        ],
        references=["https://www.pcisecuritystandards.org/"],
    ),
    "SOC2": Regulation(
        code="SOC2",
        name_ko="SOC 2 (Trust Services Criteria)",
        name_en="SOC 2 (Trust Services Criteria)",
        jurisdiction="GLOBAL",
        summary_ko=(
            "AICPA 표준. B2B SaaS가 고객 실사에 자주 요구받는 인증. "
            "Security 필수 + Availability/Confidentiality/Processing Integrity/Privacy 선택."
        ),
        summary_en=(
            "AICPA standard frequently required by B2B SaaS customers' due-diligence. "
            "Security mandatory; Availability/Confidentiality/etc. optional."
        ),
        timings=["pre_launch", "operational", "audit"],
        obligations_ko=[
            "Type I 후 12개월 운영 → Type II 보고서",
            "Control 모음 (Access · Change · Incident · Vendor)",
        ],
        obligations_en=[
            "Type I → 12-month operation → Type II report",
            "Control set (Access · Change · Incident · Vendor)",
        ],
        references=["https://www.aicpa-cima.com/"],
    ),
    "ISO-27001": Regulation(
        code="ISO-27001",
        name_ko="ISO/IEC 27001 (정보보호 관리체계 국제표준)",
        name_en="ISO/IEC 27001 (Information Security Management System)",
        jurisdiction="GLOBAL",
        summary_ko=(
            "정보보호 관리체계 국제표준. 2022 개정 (Annex A 93개 통제)."
        ),
        summary_en=(
            "International ISMS standard; 2022 revision with 93 Annex A controls."
        ),
        timings=["pre_launch", "operational", "audit"],
        obligations_ko=[
            "ISMS Scope · 위험평가 · 통제선정",
            "내부심사 + 경영진 검토",
            "3년 인증 + 매년 사후심사",
        ],
        obligations_en=[
            "Define ISMS scope · risk assessment · control selection",
            "Internal audit + management review",
            "3-year certification + annual surveillance",
        ],
        references=["https://www.iso.org/standard/27001"],
    ),
    "COPPA": Regulation(
        code="COPPA",
        name_ko="COPPA (미국 13세 미만 아동정보보호법)",
        name_en="COPPA (Children's Online Privacy Protection Act, US)",
        jurisdiction="US",
        summary_ko="미국 13세 미만 아동의 정보를 수집하면 부모 동의 등 추가 의무.",
        summary_en="Extra obligations (verifiable parental consent etc.) when collecting US children under 13.",
        timings=["pre_business", "pre_launch", "operational"],
        obligations_ko=["부모 동의(검증 가능)", "최소 수집", "별도 처리방침"],
        obligations_en=["Verifiable parental consent", "Data minimization", "Dedicated policy"],
        references=["https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa"],
    ),
}


# ── 사업 시나리오 ────────────────────────────────────────────────────
@dataclass
class Scenario:
    id: str
    name_ko: str
    name_en: str
    description_ko: str
    description_en: str
    applicable: list[str]  # Regulation.code


SCENARIOS: dict[str, Scenario] = {
    "kr-personal-data": Scenario(
        id="kr-personal-data",
        name_ko="한국 — 개인정보 처리 (B2C 일반)",
        name_en="Korea — Processing Personal Data (general B2C)",
        description_ko="국내 사용자에게 회원가입을 받고 이메일·전화번호 등을 수집하는 일반 B2C 서비스.",
        description_en="General B2C product collecting Korean users' email/phone/etc.",
        applicable=["K-PIPA", "K-ISMS-P"],
    ),
    "kr-payment": Scenario(
        id="kr-payment",
        name_ko="한국 — 결제·전자상거래 서비스",
        name_en="Korea — Payments / E-commerce",
        description_ko="신용카드/간편결제로 매출을 일으키는 한국 사업.",
        description_en="Korea-based business taking card or simplified payments.",
        applicable=["K-PIPA", "K-EFSA", "PCI-DSS"],
    ),
    "kr-financial": Scenario(
        id="kr-financial",
        name_ko="한국 — 금융 / 전자금융업",
        name_en="Korea — Financial / e-Finance providers",
        description_ko="은행·증권·전자금융업 등록 사업자.",
        description_en="Banks, brokers, registered e-finance providers.",
        applicable=["K-EFSA", "K-ISMS-P", "K-PIPA"],
    ),
    "kr-public": Scenario(
        id="kr-public",
        name_ko="한국 — 공공기관 거래",
        name_en="Korea — Selling to Public Sector",
        description_ko="공공기관(정부·지자체·공기업)에 클라우드/솔루션 납품.",
        description_en="Selling cloud/solutions to government, municipal, or state enterprises.",
        applicable=["K-CSAP", "K-ISMS-P"],
    ),
    "global-eu-users": Scenario(
        id="global-eu-users",
        name_ko="해외 — EU 사용자가 있는 모든 서비스",
        name_en="Global — Any service with EU users",
        description_ko="EU 거주자의 개인정보가 시스템에 들어오는 모든 서비스.",
        description_en="Any service that receives EU residents' personal data.",
        applicable=["GDPR"],
    ),
    "global-us-medical": Scenario(
        id="global-us-medical",
        name_ko="해외 — 미국 의료/헬스 데이터 처리",
        name_en="Global — Handling US healthcare data",
        description_ko="미국 보건 데이터(PHI)를 다루는 의료·헬스케어 서비스.",
        description_en="Healthcare service handling US PHI.",
        applicable=["HIPAA"],
    ),
    "global-saas-b2b": Scenario(
        id="global-saas-b2b",
        name_ko="해외 — 글로벌 B2B SaaS",
        name_en="Global — B2B SaaS",
        description_ko="기업 고객 실사 단계에서 SOC 2/ISO 27001을 요구받는 SaaS.",
        description_en="SaaS facing enterprise due-diligence requesting SOC 2 / ISO 27001.",
        applicable=["SOC2", "ISO-27001"],
    ),
    "ai-products": Scenario(
        id="ai-products",
        name_ko="AI 제품 (EU 시장)",
        name_en="AI Products (EU market)",
        description_ko="EU에 AI 서비스를 제공하거나 GPAI 모델을 배포.",
        description_en="Providing AI services in the EU or deploying a GPAI model.",
        applicable=["EU-AI-ACT", "GDPR"],
    ),
    "children-products": Scenario(
        id="children-products",
        name_ko="13세 미만 아동 대상 (미국 노출)",
        name_en="Targeting under-13 (US exposure)",
        description_ko="미국 어린이 사용자가 있는 서비스.",
        description_en="Service exposed to US children users.",
        applicable=["COPPA", "K-PIPA"],
    ),
}


def regulation_dict(code: str, lang: str = "ko") -> dict | None:
    r = REGULATIONS.get(code)
    if not r:
        return None
    d = asdict(r)
    d["name"] = d.pop("name_ko") if lang == "ko" else d.pop("name_en")
    d.pop("name_en" if lang == "ko" else "name_ko")
    d["summary"] = d.pop("summary_ko") if lang == "ko" else d.pop("summary_en")
    d.pop("summary_en" if lang == "ko" else "summary_ko")
    d["obligations"] = d.pop("obligations_ko") if lang == "ko" else d.pop("obligations_en")
    d.pop("obligations_en" if lang == "ko" else "obligations_ko")
    d["timings_detail"] = [
        {"key": k, "label": TIMING[k]["ko" if lang == "ko" else "en"]} for k in r.timings
    ]
    return d


def scenario_dict(scenario_id: str, lang: str = "ko") -> dict | None:
    s = SCENARIOS.get(scenario_id)
    if not s:
        return None
    return {
        "id": s.id,
        "name": s.name_ko if lang == "ko" else s.name_en,
        "description": s.description_ko if lang == "ko" else s.description_en,
        "applicable": s.applicable,
        "regulations": [regulation_dict(c, lang) for c in s.applicable],
    }
