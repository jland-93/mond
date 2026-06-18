"""
🌙 정책 템플릿 카탈로그 — 한국·글로벌 규제 통제 항목에 매핑된 자동화 가능한 정책 세트

각 템플릿은 Policy 모델로 그대로 install 가능. compliance_refs에 규제 코드를 채워
Policies 페이지에서 'ISMS-P' 같은 칩으로 필터/검색이 자연스러워진다.

규제 매핑 출처(요약):
  - ISMS-P (KISA, 정보보호 및 개인정보보호 관리체계 인증) — 2.5 ~ 2.11
  - K-EFSA (전자금융감독규정)
  - K-CSAP (공공 클라우드 보안인증)
  - K-PIPA (개인정보보호법)
  - ISO/IEC 27001:2022 (Annex A.5 ~ A.8)
  - OWASP Top 10 2021
  - CIS Benchmarks
  - NIST 800-53 / PCI DSS / GDPR (참조)
"""

from app.models.policy import PolicyType

# 각 템플릿: (slug, name, policy_type, description, severity_threshold, definition, compliance_refs, frameworks)
# frameworks: 카탈로그 필터링용 (한 템플릿이 여러 규제에 매핑될 수 있다)
TEMPLATES: list[dict] = [
    # ─── SCA · 의존성 취약점 ─────────────────────────────────────
    {
        "name": "Block Critical CVE in Dependencies",
        "policy_type": PolicyType.SCA,
        "description": "의존성에서 CRITICAL 등급 CVE가 발견되면 파이프라인 차단. ISMS-P 2.8.6 / ISO 27001 A.8.8 / OWASP A06 충족.",
        "severity_threshold": "critical",
        "definition": {"block_above": "critical", "scope": "dependencies"},
        "compliance_refs": ["ISMS-P-2.8.6", "ISO-27001-A.8.8", "OWASP-A06", "PCI-DSS-6.3"],
        "frameworks": ["ISMS-P", "ISO-27001", "OWASP", "PCI-DSS"],
    },
    {
        "name": "Reject EOL / Unsupported Libraries",
        "policy_type": PolicyType.SCA,
        "description": "Maintenance가 종료된 라이브러리(EOL) 사용 금지. ISMS-P 2.8.2 / ISO 27001 A.8.30.",
        "severity_threshold": "high",
        "definition": {"reject": "eol", "min_release_age_days": 365 * 3},
        "compliance_refs": ["ISMS-P-2.8.2", "ISO-27001-A.8.30"],
        "frameworks": ["ISMS-P", "ISO-27001"],
    },

    # ─── SAST · 시큐어 코딩 ─────────────────────────────────────
    {
        "name": "Secure SDLC — SAST Required",
        "policy_type": PolicyType.SAST,
        "description": "모든 코드 변경에 정적분석(SAST) 통과 필수. ISMS-P 2.8.1(보안 SDLC) / K-EFSA 8조 / ISO 27001 A.8.25.",
        "severity_threshold": "high",
        "definition": {"require_pass": True, "scanners": ["semgrep"]},
        "compliance_refs": ["ISMS-P-2.8.1", "K-EFSA-8", "ISO-27001-A.8.25"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001"],
    },
    {
        "name": "Block OWASP Top 10 in Code",
        "policy_type": PolicyType.SAST,
        "description": "OWASP Top 10 룰 위반은 모두 차단. ISMS-P 2.8.1 / OWASP / ISO 27001 A.8.28.",
        "severity_threshold": "medium",
        "definition": {"rulesets": ["owasp-top-10"]},
        "compliance_refs": ["ISMS-P-2.8.1", "OWASP-A01-A10", "ISO-27001-A.8.28"],
        "frameworks": ["ISMS-P", "OWASP", "ISO-27001"],
    },

    # ─── IaC / 컨테이너 / 클라우드 설정 ───────────────────────────
    {
        "name": "Container Hardening Baseline (CIS Docker)",
        "policy_type": PolicyType.CONTAINER,
        "description": "이미지에 HIGH 이상 취약점 누적 금지 + 비루트 사용자. ISMS-P 2.9.3 / ISO 27001 A.8.9 / CIS Docker 4.1.",
        "severity_threshold": "high",
        "definition": {"block_above": "high", "deny_root_user": True},
        "compliance_refs": ["ISMS-P-2.9.3", "ISO-27001-A.8.9", "CIS-Docker-4.1"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },
    {
        "name": "IaC — Encryption at Rest 강제",
        "policy_type": PolicyType.IAC,
        "description": "Terraform/CloudFormation으로 만드는 모든 데이터 스토어는 저장 암호화 필수. ISMS-P 2.7.1 / K-PIPA 안전조치 / ISO 27001 A.8.24.",
        "severity_threshold": "high",
        "definition": {"require": "encryption_at_rest", "scope": ["s3", "rds", "ebs", "gcs"]},
        "compliance_refs": ["ISMS-P-2.7.1", "K-PIPA-29", "ISO-27001-A.8.24"],
        "frameworks": ["ISMS-P", "K-PIPA", "ISO-27001"],
    },
    {
        "name": "IaC — Public S3/Storage 금지",
        "policy_type": PolicyType.IAC,
        "description": "공개 버킷·공개 ACL 차단. ISMS-P 2.6.1(접근통제) / ISO 27001 A.8.3 / CIS AWS 2.1.5.",
        "severity_threshold": "critical",
        "definition": {"deny": "public_access", "scope": ["s3", "gcs", "azure_blob"]},
        "compliance_refs": ["ISMS-P-2.6.1", "ISO-27001-A.8.3", "CIS-AWS-2.1.5"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },

    # ─── 시크릿 / 키 관리 ───────────────────────────────────────
    {
        "name": "Secrets in Code 차단",
        "policy_type": PolicyType.SECRETS,
        "description": "리포지토리 내 평문 시크릿(AKIA, BEGIN PRIVATE KEY, JWT 등) 차단. ISMS-P 2.7.2 / K-EFSA 11조 / ISO 27001 A.8.10.",
        "severity_threshold": "high",
        "definition": {"rules": ["AKIA[0-9A-Z]{16}", "-----BEGIN.*PRIVATE KEY-----", "ghp_[A-Za-z0-9]{36}"]},
        "compliance_refs": ["ISMS-P-2.7.2", "K-EFSA-11", "ISO-27001-A.8.10", "OWASP-A02"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001", "OWASP"],
    },
    {
        "name": "Key Rotation 강제 (90일)",
        "policy_type": PolicyType.CUSTOM,
        "description": "장기 자격증명은 90일 이내 회전. ISMS-P 2.5.4 / ISO 27001 A.8.24 / CIS AWS 1.14.",
        "severity_threshold": "high",
        "definition": {"max_key_age_days": 90},
        "compliance_refs": ["ISMS-P-2.5.4", "ISO-27001-A.8.24", "CIS-AWS-1.14"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },

    # ─── 접근 통제 / 인증 ───────────────────────────────────────
    {
        "name": "관리자 계정 MFA 강제",
        "policy_type": PolicyType.CUSTOM,
        "description": "Admin/Root 권한 계정은 MFA 필수. ISMS-P 2.5.3 / K-EFSA 13조 / ISO 27001 A.5.16.",
        "severity_threshold": "critical",
        "definition": {"require_mfa_for": ["admin", "root"]},
        "compliance_refs": ["ISMS-P-2.5.3", "K-EFSA-13", "ISO-27001-A.5.16"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001"],
    },
    {
        "name": "최소권한 — Wildcard IAM 금지",
        "policy_type": PolicyType.IAC,
        "description": "IAM 정책에 Action='*' 또는 Resource='*' 금지. ISMS-P 2.5.6 / ISO 27001 A.5.18.",
        "severity_threshold": "high",
        "definition": {"deny": ["Action:*", "Resource:*"]},
        "compliance_refs": ["ISMS-P-2.5.6", "ISO-27001-A.5.18"],
        "frameworks": ["ISMS-P", "ISO-27001"],
    },

    # ─── 암호화 · 전송 보안 ────────────────────────────────────
    {
        "name": "TLS 1.2+ 강제",
        "policy_type": PolicyType.IAC,
        "description": "모든 외부 엔드포인트는 TLS 1.2 이상. ISMS-P 2.7.1 / K-PIPA 안전조치 / ISO 27001 A.8.24.",
        "severity_threshold": "high",
        "definition": {"min_tls_version": "1.2", "disallow": ["TLSv1.0", "TLSv1.1", "SSLv3"]},
        "compliance_refs": ["ISMS-P-2.7.1", "K-PIPA-29", "ISO-27001-A.8.24"],
        "frameworks": ["ISMS-P", "K-PIPA", "ISO-27001"],
    },

    # ─── 로그 · 감사 ────────────────────────────────────────────
    {
        "name": "접근 로그 보존 (1년 이상)",
        "policy_type": PolicyType.CUSTOM,
        "description": "관리자/특권 접근 로그는 최소 1년 보존. ISMS-P 2.9.4 / K-EFSA 16조 / ISO 27001 A.8.15.",
        "severity_threshold": "high",
        "definition": {"retention_days_min": 365, "scope": "privileged_access"},
        "compliance_refs": ["ISMS-P-2.9.4", "K-EFSA-16", "ISO-27001-A.8.15"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001"],
    },

    # ─── DAST / 웹 보안 ────────────────────────────────────────
    {
        "name": "Web Security Headers 적용",
        "policy_type": PolicyType.DAST,
        "description": "HSTS · X-Content-Type-Options · CSP · X-Frame-Options 필수. ISMS-P 2.8.5 / OWASP A05 / ISO 27001 A.8.26.",
        "severity_threshold": "medium",
        "definition": {"require_headers": ["Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options"]},
        "compliance_refs": ["ISMS-P-2.8.5", "OWASP-A05", "ISO-27001-A.8.26"],
        "frameworks": ["ISMS-P", "OWASP", "ISO-27001"],
    },

    # ─── 개인정보 / 데이터 ──────────────────────────────────────
    {
        "name": "PII 마스킹 — 로그/응답 검사",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "주민번호·카드번호·이메일 등 PII가 로그·응답에 평문으로 노출되지 않도록. K-PIPA 안전조치 / GDPR Art.32 / ISMS-P 3.3.",
        "severity_threshold": "high",
        "definition": {"patterns": ["[0-9]{6}-[1-4][0-9]{6}", "[0-9]{13,19}", "([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)"]},
        "compliance_refs": ["K-PIPA-29", "GDPR-Art-32", "ISMS-P-3.3"],
        "frameworks": ["K-PIPA", "GDPR", "ISMS-P"],
    },

    # ─── 공공 클라우드 (CSAP) ───────────────────────────────────
    {
        "name": "데이터 국내 위치 강제 (CSAP)",
        "policy_type": PolicyType.IAC,
        "description": "공공기관용 시스템의 모든 데이터는 국내 리전에 위치. K-CSAP / ISMS-P 2.10.",
        "severity_threshold": "critical",
        "definition": {"allowed_regions": ["ap-northeast-2", "kr-central-1", "ap-northeast-3"]},
        "compliance_refs": ["K-CSAP", "ISMS-P-2.10"],
        "frameworks": ["K-CSAP", "ISMS-P"],
    },
]


# 빠른 카탈로그 필터링용 프레임워크 정의 (UI 칩으로 노출)
FRAMEWORKS: list[dict] = [
    {"id": "ISMS-P", "name_ko": "ISMS-P (정보보호 관리체계, 국내)", "name_en": "ISMS-P (KISA, KR)"},
    {"id": "K-EFSA", "name_ko": "전자금융감독규정 (국내)", "name_en": "Korean E-Finance Supervision"},
    {"id": "K-CSAP", "name_ko": "CSAP — 공공 클라우드 (국내)", "name_en": "Korean CSAP (public cloud)"},
    {"id": "K-PIPA", "name_ko": "개인정보보호법 (국내)", "name_en": "Korean PIPA"},
    {"id": "ISO-27001", "name_ko": "ISO/IEC 27001:2022 (글로벌)", "name_en": "ISO/IEC 27001:2022"},
    {"id": "OWASP", "name_ko": "OWASP Top 10 (글로벌)", "name_en": "OWASP Top 10"},
    {"id": "CIS", "name_ko": "CIS Benchmarks (글로벌)", "name_en": "CIS Benchmarks"},
    {"id": "PCI-DSS", "name_ko": "PCI DSS (글로벌 결제)", "name_en": "PCI DSS"},
    {"id": "GDPR", "name_ko": "GDPR (EU)", "name_en": "GDPR (EU)"},
]


def list_templates(framework: str | None = None) -> list[dict]:
    if not framework:
        return list(TEMPLATES)
    return [t for t in TEMPLATES if framework in t.get("frameworks", [])]
