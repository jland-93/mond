"""
정책 템플릿 카탈로그 — 한국·글로벌 규제 통제 항목에 매핑된 자동화 가능한 정책 세트

각 템플릿은 Policy 모델로 그대로 install 가능. compliance_refs에 규제 코드를 채워
Policies 페이지에서 'ISMS-P' 같은 칩으로 필터/검색이 자연스러워진다.

규제별 통제 항목은 다음 공식 출처에서 정리되었다:
  - KISA ISMS-P 인증기준 (2.5~2.11, 3.1~3.5) — https://isms.kisa.or.kr
  - KISA 「개인정보의 안전성 확보조치 기준」 고시 (K-PIPA 1~9조)
  - 금융위 「전자금융감독규정」 (8·11·13·16·17·19·21조)
  - 「클라우드컴퓨팅서비스 보안인증(CSAP)」 통제항목
  - AWS Foundational Security Best Practices (FSBP)
  - Datadog Security · CSPM / Cloud SIEM 룰 카탈로그
  - SK쉴더스 EQST 한국 환경 보안 가이드 (망분리·침해사고 대응 시그니처)
  - ISO/IEC 27001:2022 Annex A.5~A.8
  - OWASP Top 10 2021
  - CIS Benchmarks (Docker · AWS · Kubernetes · Linux)
  - PCI DSS v4.0
  - GDPR (Art.5·30·32·33·35)
"""

from app.models.policy import PolicyType

# 각 템플릿: name / policy_type / description / severity_threshold /
#           definition / compliance_refs / frameworks
TEMPLATES: list[dict] = [
    # ════════════════════════════════════════════════════════════════
    # 1. SCA · 의존성 취약점 (소프트웨어 공급망)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "Block Critical CVE in Dependencies",
        "policy_type": PolicyType.SCA,
        "description": "의존성에서 CRITICAL 등급 CVE 발견 시 파이프라인 차단. ISMS-P 2.8.6 / ISO 27001 A.8.8 / OWASP A06 / PCI DSS 6.3.3.",
        "severity_threshold": "critical",
        "definition": {"block_above": "critical", "scope": "dependencies"},
        "compliance_refs": ["ISMS-P-2.8.6", "ISO-27001-A.8.8", "OWASP-A06", "PCI-DSS-6.3.3"],
        "frameworks": ["ISMS-P", "ISO-27001", "OWASP", "PCI-DSS"],
    },
    {
        "name": "SBOM 생성 의무화",
        "policy_type": PolicyType.SCA,
        "description": "모든 배포 산출물은 CycloneDX/SPDX SBOM을 함께 발행 (공급망 투명성). ISMS-P 2.8.2 / ISO 27001 A.5.21 / NIST SSDF PO.1.2.",
        "severity_threshold": "medium",
        "definition": {"require": "sbom", "format": ["cyclonedx", "spdx"]},
        "compliance_refs": ["ISMS-P-2.8.2", "ISO-27001-A.5.21"],
        "frameworks": ["ISMS-P", "ISO-27001"],
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

    # ════════════════════════════════════════════════════════════════
    # 2. SAST · 시큐어 코딩
    # ════════════════════════════════════════════════════════════════
    {
        "name": "Secure SDLC — SAST Required",
        "policy_type": PolicyType.SAST,
        "description": "모든 코드 변경에 정적분석(SAST) 통과 필수. ISMS-P 2.8.1(보안 SDLC) / 전자금융감독규정 8조 / ISO 27001 A.8.25.",
        "severity_threshold": "high",
        "definition": {"require_pass": True, "scanners": ["semgrep"]},
        "compliance_refs": ["ISMS-P-2.8.1", "K-EFSA-8", "ISO-27001-A.8.25"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001"],
    },
    {
        "name": "Block OWASP Top 10 in Code",
        "policy_type": PolicyType.SAST,
        "description": "OWASP Top 10 룰 위반은 모두 차단(인젝션·XSS·SSRF 포함). ISMS-P 2.8.1 / OWASP / ISO 27001 A.8.28 / PCI DSS 6.2.4.",
        "severity_threshold": "medium",
        "definition": {"rulesets": ["owasp-top-10"]},
        "compliance_refs": ["ISMS-P-2.8.1", "OWASP-A01-A10", "ISO-27001-A.8.28", "PCI-DSS-6.2.4"],
        "frameworks": ["ISMS-P", "OWASP", "ISO-27001", "PCI-DSS"],
    },
    {
        "name": "OWASP A03 — Injection 차단",
        "policy_type": PolicyType.SAST,
        "description": "SQLi/Command Injection 패턴 (raw concat) 발견 시 빌드 실패. OWASP A03 / ISMS-P 2.8.1 / PCI DSS 6.2.4.",
        "severity_threshold": "high",
        "definition": {"rulesets": ["owasp-a03-injection"], "fail_on": "any"},
        "compliance_refs": ["OWASP-A03", "ISMS-P-2.8.1", "PCI-DSS-6.2.4"],
        "frameworks": ["OWASP", "ISMS-P", "PCI-DSS"],
    },
    {
        "name": "OWASP A10 — SSRF 차단",
        "policy_type": PolicyType.SAST,
        "description": "외부 URL 호출에 대한 입력 검증 없음 패턴 검출. OWASP A10 / ISMS-P 2.8.5.",
        "severity_threshold": "high",
        "definition": {"rulesets": ["owasp-a10-ssrf"]},
        "compliance_refs": ["OWASP-A10", "ISMS-P-2.8.5"],
        "frameworks": ["OWASP", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 3. IaC / 컨테이너 / 클라우드 설정 (AWS FSBP · CIS · Datadog CSPM)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "Container Hardening Baseline (CIS Docker)",
        "policy_type": PolicyType.CONTAINER,
        "description": "이미지에 HIGH 이상 취약점 누적 금지 + 비루트 사용자 강제. ISMS-P 2.9.3 / ISO 27001 A.8.9 / CIS Docker 4.1·4.5.",
        "severity_threshold": "high",
        "definition": {"block_above": "high", "deny_root_user": True},
        "compliance_refs": ["ISMS-P-2.9.3", "ISO-27001-A.8.9", "CIS-Docker-4.1", "CIS-Docker-4.5"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },
    {
        "name": "Kubernetes Pod Security — privileged 차단",
        "policy_type": PolicyType.CONTAINER,
        "description": "privileged·hostNetwork·hostPID Pod 배포 차단. CIS Kubernetes 5.2 / ISMS-P 2.9.3.",
        "severity_threshold": "high",
        "definition": {"deny": ["privileged", "hostNetwork", "hostPID"]},
        "compliance_refs": ["CIS-K8s-5.2", "ISMS-P-2.9.3"],
        "frameworks": ["CIS", "ISMS-P"],
    },
    {
        "name": "IaC — Encryption at Rest 강제",
        "policy_type": PolicyType.IAC,
        "description": "Terraform/CloudFormation으로 만드는 모든 데이터 스토어는 저장 암호화 필수. ISMS-P 2.7.1 / K-PIPA 7조(개인정보 암호화) / ISO 27001 A.8.24 / AWS FSBP S3.4·RDS.2.",
        "severity_threshold": "high",
        "definition": {"require": "encryption_at_rest", "scope": ["s3", "rds", "ebs", "gcs", "azure_disk"]},
        "compliance_refs": ["ISMS-P-2.7.1", "K-PIPA-7", "ISO-27001-A.8.24", "AWS-FSBP-S3.4", "AWS-FSBP-RDS.2"],
        "frameworks": ["ISMS-P", "K-PIPA", "ISO-27001"],
    },
    {
        "name": "IaC — Public S3/Storage 금지",
        "policy_type": PolicyType.IAC,
        "description": "공개 버킷·공개 ACL 차단 (Block Public Access). ISMS-P 2.6.1(접근통제) / ISO 27001 A.8.3 / CIS AWS 2.1.5 / AWS FSBP S3.1·S3.8.",
        "severity_threshold": "critical",
        "definition": {"deny": "public_access", "scope": ["s3", "gcs", "azure_blob"]},
        "compliance_refs": ["ISMS-P-2.6.1", "ISO-27001-A.8.3", "CIS-AWS-2.1.5", "AWS-FSBP-S3.1", "AWS-FSBP-S3.8"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },
    {
        "name": "Security Group — 0.0.0.0/0 차단",
        "policy_type": PolicyType.IAC,
        "description": "관리 포트(22, 3389, 5432, 3306, 6379, 27017)에 0.0.0.0/0 inbound 금지. AWS FSBP EC2.13·EC2.14 / CIS AWS 5.2 / Datadog CSPM aws-ec2-security-group-ingress.",
        "severity_threshold": "critical",
        "definition": {"deny": "0.0.0.0/0", "ports": [22, 3389, 5432, 3306, 6379, 27017]},
        "compliance_refs": ["AWS-FSBP-EC2.13", "AWS-FSBP-EC2.14", "CIS-AWS-5.2", "ISMS-P-2.6.1"],
        "frameworks": ["CIS", "ISMS-P"],
    },
    {
        "name": "VPC Flow Logs 활성화",
        "policy_type": PolicyType.IAC,
        "description": "모든 VPC에 Flow Logs 활성화 — 침해 분석 시간 단축. ISMS-P 2.11.2 / 전자금융감독규정 16조 / AWS FSBP EC2.6 / Datadog Cloud SIEM.",
        "severity_threshold": "high",
        "definition": {"require": "vpc_flow_logs", "destination": ["cloudwatch", "s3"]},
        "compliance_refs": ["ISMS-P-2.11.2", "K-EFSA-16", "AWS-FSBP-EC2.6"],
        "frameworks": ["ISMS-P", "K-EFSA"],
    },
    {
        "name": "CloudTrail / 감사로그 — 전체 리전 활성화",
        "policy_type": PolicyType.IAC,
        "description": "AWS CloudTrail은 모든 리전에서 활성화 + 로그 무결성 검증. AWS FSBP CloudTrail.1·CloudTrail.4 / CIS AWS 3.1 / ISMS-P 2.9.4 / 전자금융감독규정 16조 / Datadog Cloud SIEM 필수 신호.",
        "severity_threshold": "critical",
        "definition": {"require": "cloudtrail_all_regions", "validate_logfile": True},
        "compliance_refs": ["AWS-FSBP-CloudTrail.1", "AWS-FSBP-CloudTrail.4", "CIS-AWS-3.1", "ISMS-P-2.9.4", "K-EFSA-16"],
        "frameworks": ["ISMS-P", "K-EFSA", "CIS"],
    },
    {
        "name": "GuardDuty / 위협탐지 활성화",
        "policy_type": PolicyType.IAC,
        "description": "GuardDuty(또는 동급 탐지 서비스) 전체 리전 활성화. AWS FSBP GuardDuty.1 / ISMS-P 2.11.3(침해사고 대응) / Datadog Cloud SIEM.",
        "severity_threshold": "high",
        "definition": {"require": "threat_detection", "scope": "all_regions"},
        "compliance_refs": ["AWS-FSBP-GuardDuty.1", "ISMS-P-2.11.3"],
        "frameworks": ["ISMS-P"],
    },
    {
        "name": "IMDSv2 강제 (EC2 메타데이터)",
        "policy_type": PolicyType.IAC,
        "description": "EC2 인스턴스는 IMDSv2(토큰 기반)만 허용 — SSRF 자격증명 탈취 방지. AWS FSBP EC2.8 / OWASP A10 / Datadog CSPM aws-ec2-imdsv1.",
        "severity_threshold": "high",
        "definition": {"require": "imdsv2", "http_tokens": "required"},
        "compliance_refs": ["AWS-FSBP-EC2.8", "OWASP-A10", "ISMS-P-2.6.7"],
        "frameworks": ["OWASP", "ISMS-P"],
    },
    {
        "name": "RDS — 퍼블릭 접근 금지 + 다중 AZ",
        "policy_type": PolicyType.IAC,
        "description": "RDS publicly_accessible=false + MultiAZ=true. AWS FSBP RDS.2·RDS.5 / ISMS-P 2.6.1·2.11.2 / 전자금융감독규정 21조(비상대응).",
        "severity_threshold": "high",
        "definition": {"deny": "publicly_accessible", "require": "multi_az"},
        "compliance_refs": ["AWS-FSBP-RDS.2", "AWS-FSBP-RDS.5", "ISMS-P-2.6.1", "K-EFSA-21"],
        "frameworks": ["ISMS-P", "K-EFSA"],
    },

    # ════════════════════════════════════════════════════════════════
    # 4. 시크릿 / 키 관리
    # ════════════════════════════════════════════════════════════════
    {
        "name": "Secrets in Code 차단",
        "policy_type": PolicyType.SECRETS,
        "description": "리포지토리 내 평문 시크릿(AKIA, BEGIN PRIVATE KEY, JWT, GitHub PAT 등) 차단. ISMS-P 2.7.2 / 전자금융감독규정 11조 / ISO 27001 A.8.10 / OWASP A02 / Datadog Secret Scanning.",
        "severity_threshold": "high",
        "definition": {"rules": ["AKIA[0-9A-Z]{16}", "-----BEGIN.*PRIVATE KEY-----", "ghp_[A-Za-z0-9]{36}", "xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+"]},
        "compliance_refs": ["ISMS-P-2.7.2", "K-EFSA-11", "ISO-27001-A.8.10", "OWASP-A02"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001", "OWASP"],
    },
    {
        "name": "Key Rotation 강제 (90일)",
        "policy_type": PolicyType.CUSTOM,
        "description": "장기 자격증명은 90일 이내 회전. ISMS-P 2.5.4 / ISO 27001 A.8.24 / CIS AWS 1.14 / AWS FSBP IAM.3.",
        "severity_threshold": "high",
        "definition": {"max_key_age_days": 90},
        "compliance_refs": ["ISMS-P-2.5.4", "ISO-27001-A.8.24", "CIS-AWS-1.14", "AWS-FSBP-IAM.3"],
        "frameworks": ["ISMS-P", "ISO-27001", "CIS"],
    },
    {
        "name": "KMS 키 회전 자동화",
        "policy_type": PolicyType.IAC,
        "description": "KMS Customer Managed Key는 자동 회전 활성화. AWS FSBP KMS.4 / CIS AWS 3.8 / ISMS-P 2.7.3.",
        "severity_threshold": "medium",
        "definition": {"require": "kms_key_rotation"},
        "compliance_refs": ["AWS-FSBP-KMS.4", "CIS-AWS-3.8", "ISMS-P-2.7.3"],
        "frameworks": ["CIS", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 5. 접근 통제 / 인증 (ISMS-P 2.5 · K-PIPA 1·2조 · K-EFSA 13조)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "관리자 계정 MFA 강제",
        "policy_type": PolicyType.CUSTOM,
        "description": "Admin/Root 권한 계정은 MFA 필수. ISMS-P 2.5.3 / 전자금융감독규정 13조 / K-PIPA 1조 / ISO 27001 A.5.16 / AWS FSBP IAM.6.",
        "severity_threshold": "critical",
        "definition": {"require_mfa_for": ["admin", "root"]},
        "compliance_refs": ["ISMS-P-2.5.3", "K-EFSA-13", "K-PIPA-1", "ISO-27001-A.5.16", "AWS-FSBP-IAM.6"],
        "frameworks": ["ISMS-P", "K-EFSA", "K-PIPA", "ISO-27001"],
    },
    {
        "name": "Root 계정 무사용 (90일)",
        "policy_type": PolicyType.CUSTOM,
        "description": "AWS/GCP Root/Owner 계정은 일상 운영에 사용 금지. 90일간 마지막 로그인 검증. AWS FSBP IAM.7 / CIS AWS 1.7 / Datadog CSPM.",
        "severity_threshold": "high",
        "definition": {"deny": "root_console_access_days", "threshold": 90},
        "compliance_refs": ["AWS-FSBP-IAM.7", "CIS-AWS-1.7", "ISMS-P-2.5.5"],
        "frameworks": ["CIS", "ISMS-P"],
    },
    {
        "name": "최소권한 — Wildcard IAM 금지",
        "policy_type": PolicyType.IAC,
        "description": "IAM 정책에 Action='*' 또는 Resource='*' 금지. ISMS-P 2.5.6 / ISO 27001 A.5.18 / AWS FSBP IAM.21.",
        "severity_threshold": "high",
        "definition": {"deny": ["Action:*", "Resource:*"]},
        "compliance_refs": ["ISMS-P-2.5.6", "ISO-27001-A.5.18", "AWS-FSBP-IAM.21"],
        "frameworks": ["ISMS-P", "ISO-27001"],
    },
    {
        "name": "접근권한 정기 검토 (분기)",
        "policy_type": PolicyType.CUSTOM,
        "description": "사용자/시스템 접근권한을 분기마다 자동 검토 이슈로 등록. ISMS-P 2.5.6 / K-PIPA 1조 / 전자금융감독규정 13조 / ISO 27001 A.5.18.",
        "severity_threshold": "medium",
        "definition": {"review_interval_days": 90},
        "compliance_refs": ["ISMS-P-2.5.6", "K-PIPA-1", "K-EFSA-13", "ISO-27001-A.5.18"],
        "frameworks": ["ISMS-P", "K-PIPA", "K-EFSA", "ISO-27001"],
    },
    {
        "name": "비밀번호 정책 — 12자 + 복잡도",
        "policy_type": PolicyType.IAC,
        "description": "최소 12자, 대·소문자·숫자·특수 혼합. ISMS-P 2.5.4 / K-PIPA 1조 / CIS AWS 1.5~1.11 / PCI DSS 8.3.6.",
        "severity_threshold": "high",
        "definition": {"min_length": 12, "complexity": True, "max_age_days": 90},
        "compliance_refs": ["ISMS-P-2.5.4", "K-PIPA-1", "CIS-AWS-1.5", "PCI-DSS-8.3.6"],
        "frameworks": ["ISMS-P", "K-PIPA", "CIS", "PCI-DSS"],
    },

    # ════════════════════════════════════════════════════════════════
    # 6. 암호화 · 전송 보안
    # ════════════════════════════════════════════════════════════════
    {
        "name": "TLS 1.2+ 강제",
        "policy_type": PolicyType.IAC,
        "description": "모든 외부 엔드포인트는 TLS 1.2 이상. ISMS-P 2.7.1 / K-PIPA 7조(개인정보 암호화) / ISO 27001 A.8.24 / PCI DSS 4.2.1.",
        "severity_threshold": "high",
        "definition": {"min_tls_version": "1.2", "disallow": ["TLSv1.0", "TLSv1.1", "SSLv3"]},
        "compliance_refs": ["ISMS-P-2.7.1", "K-PIPA-7", "ISO-27001-A.8.24", "PCI-DSS-4.2.1"],
        "frameworks": ["ISMS-P", "K-PIPA", "ISO-27001", "PCI-DSS"],
    },
    {
        "name": "개인정보 전송 암호화 (고유식별정보)",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "주민등록번호·여권번호·운전면허·외국인등록 등 고유식별정보는 송수신 시 암호화 필수. K-PIPA 7조 / ISMS-P 2.7.1·3.3.",
        "severity_threshold": "critical",
        "definition": {"require_encryption": "in_transit", "scope": "unique_identifiers"},
        "compliance_refs": ["K-PIPA-7", "ISMS-P-2.7.1", "ISMS-P-3.3"],
        "frameworks": ["K-PIPA", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 7. 로그 · 감사 (K-PIPA 8조 · ISMS-P 2.9.4 · K-EFSA 16조)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "접근 로그 보존 — 개인정보처리시스템 2년",
        "policy_type": PolicyType.CUSTOM,
        "description": "개인정보처리시스템 접속기록은 최소 2년 보관(5만명 이상 또는 고유식별정보 처리 시). K-PIPA 8조 / ISMS-P 3.3 / 전자금융감독규정 16조.",
        "severity_threshold": "high",
        "definition": {"retention_days_min": 730, "scope": "pii_access"},
        "compliance_refs": ["K-PIPA-8", "ISMS-P-3.3", "K-EFSA-16"],
        "frameworks": ["K-PIPA", "ISMS-P", "K-EFSA"],
    },
    {
        "name": "접근 로그 보존 (1년 이상)",
        "policy_type": PolicyType.CUSTOM,
        "description": "관리자/특권 접근 로그는 최소 1년 보존. ISMS-P 2.9.4 / 전자금융감독규정 16조 / ISO 27001 A.8.15 / PCI DSS 10.5.1.",
        "severity_threshold": "high",
        "definition": {"retention_days_min": 365, "scope": "privileged_access"},
        "compliance_refs": ["ISMS-P-2.9.4", "K-EFSA-16", "ISO-27001-A.8.15", "PCI-DSS-10.5.1"],
        "frameworks": ["ISMS-P", "K-EFSA", "ISO-27001", "PCI-DSS"],
    },
    {
        "name": "로그 무결성 보호",
        "policy_type": PolicyType.CUSTOM,
        "description": "감사 로그는 위변조 방지(append-only, hash chain, S3 Object Lock 등). PCI DSS 10.3.2 / ISMS-P 2.9.4 / 전자금융감독규정 16조.",
        "severity_threshold": "high",
        "definition": {"require": "immutable_log_storage"},
        "compliance_refs": ["PCI-DSS-10.3.2", "ISMS-P-2.9.4", "K-EFSA-16"],
        "frameworks": ["PCI-DSS", "ISMS-P", "K-EFSA"],
    },

    # ════════════════════════════════════════════════════════════════
    # 8. DAST / 웹 보안
    # ════════════════════════════════════════════════════════════════
    {
        "name": "Web Security Headers 적용",
        "policy_type": PolicyType.DAST,
        "description": "HSTS · X-Content-Type-Options · CSP · X-Frame-Options · Referrer-Policy 필수. ISMS-P 2.8.5 / OWASP A05 / ISO 27001 A.8.26.",
        "severity_threshold": "medium",
        "definition": {"require_headers": ["Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"]},
        "compliance_refs": ["ISMS-P-2.8.5", "OWASP-A05", "ISO-27001-A.8.26"],
        "frameworks": ["ISMS-P", "OWASP", "ISO-27001"],
    },
    {
        "name": "OWASP A07 — 인증 실패 모니터링",
        "policy_type": PolicyType.DAST,
        "description": "로그인 실패율·계정 잠금·MFA 우회 시도를 실시간 알림. OWASP A07 / ISMS-P 2.5.3·2.11.3 / PCI DSS 8.3.4.",
        "severity_threshold": "high",
        "definition": {"alert_on": ["auth_failure_rate", "lockout", "mfa_bypass"]},
        "compliance_refs": ["OWASP-A07", "ISMS-P-2.5.3", "ISMS-P-2.11.3", "PCI-DSS-8.3.4"],
        "frameworks": ["OWASP", "ISMS-P", "PCI-DSS"],
    },

    # ════════════════════════════════════════════════════════════════
    # 9. 개인정보 / 데이터 (K-PIPA · GDPR · ISMS-P 3.x)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "PII 마스킹 — 로그/응답 검사",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "주민번호·카드번호·이메일 등 PII가 로그·응답에 평문으로 노출되지 않도록. K-PIPA 7조 / GDPR Art.32 / ISMS-P 3.3 / PCI DSS 3.5.",
        "severity_threshold": "high",
        "definition": {"patterns": ["[0-9]{6}-[1-4][0-9]{6}", "[0-9]{13,19}", "([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)"]},
        "compliance_refs": ["K-PIPA-7", "GDPR-Art-32", "ISMS-P-3.3", "PCI-DSS-3.5"],
        "frameworks": ["K-PIPA", "GDPR", "ISMS-P", "PCI-DSS"],
    },
    {
        "name": "개인정보 파기 — 보유기간 만료 자동화",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "수집 목적 달성 또는 보유기간 만료 시 자동 파기 잡 구성. K-PIPA 21조(파기) / GDPR Art.5(보관 최소화) / ISMS-P 3.4.",
        "severity_threshold": "high",
        "definition": {"require": "retention_expiry_job"},
        "compliance_refs": ["K-PIPA-21", "GDPR-Art-5", "ISMS-P-3.4"],
        "frameworks": ["K-PIPA", "GDPR", "ISMS-P"],
    },
    {
        "name": "개인정보 처리위탁 — 수탁자 점검",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "수탁자 보안 점검(연1회 이상) 결과 미보유 시 위탁 차단. K-PIPA 26조 / ISMS-P 1.3.3 / GDPR Art.28.",
        "severity_threshold": "medium",
        "definition": {"require": "processor_audit_yearly"},
        "compliance_refs": ["K-PIPA-26", "ISMS-P-1.3.3", "GDPR-Art-28"],
        "frameworks": ["K-PIPA", "ISMS-P", "GDPR"],
    },
    {
        "name": "개인정보 영향평가 (PIA) 트리거",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "5만명 이상 민감정보·고유식별정보 처리 시스템은 PIA 결과 첨부 없이 배포 불가. K-PIPA 33조 / GDPR Art.35(DPIA) / ISMS-P 1.2.4.",
        "severity_threshold": "high",
        "definition": {"trigger_when": {"data_subjects_min": 50000, "sensitive": True}},
        "compliance_refs": ["K-PIPA-33", "GDPR-Art-35", "ISMS-P-1.2.4"],
        "frameworks": ["K-PIPA", "GDPR", "ISMS-P"],
    },
    {
        "name": "개인정보 침해사고 — 72시간 통지",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "유출 인지 후 72시간 내 정보주체·KISA 신고 자동화. K-PIPA 34조 / GDPR Art.33 / ISMS-P 2.11.5.",
        "severity_threshold": "critical",
        "definition": {"notify_within_hours": 72, "targets": ["data_subjects", "kisa", "supervisor"]},
        "compliance_refs": ["K-PIPA-34", "GDPR-Art-33", "ISMS-P-2.11.5"],
        "frameworks": ["K-PIPA", "GDPR", "ISMS-P"],
    },
    {
        "name": "개인정보 처리기록 (Record of Processing)",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "처리목적·항목·보유기간·수탁자 등 처리현황을 시스템적으로 기록·공개. GDPR Art.30 / K-PIPA 31조 / ISMS-P 3.5.",
        "severity_threshold": "medium",
        "definition": {"require": "processing_record"},
        "compliance_refs": ["GDPR-Art-30", "K-PIPA-31", "ISMS-P-3.5"],
        "frameworks": ["GDPR", "K-PIPA", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 10. 공공 클라우드 (K-CSAP)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "데이터 국내 위치 강제 (CSAP)",
        "policy_type": PolicyType.IAC,
        "description": "공공기관용 시스템의 모든 데이터는 국내 리전에 위치. K-CSAP 2.1 / ISMS-P 2.10 / K-PIPA 28조(국외이전).",
        "severity_threshold": "critical",
        "definition": {"allowed_regions": ["ap-northeast-2", "kr-central-1", "ap-northeast-3"]},
        "compliance_refs": ["K-CSAP-2.1", "ISMS-P-2.10", "K-PIPA-28"],
        "frameworks": ["K-CSAP", "ISMS-P", "K-PIPA"],
    },
    {
        "name": "CSAP — 망분리 (DMZ · Internal · 운영)",
        "policy_type": PolicyType.IAC,
        "description": "DMZ / 내부망 / 운영망 3-tier 분리, 운영망은 인터넷 직접 통신 금지. K-CSAP 3.2 / SK쉴더스 EQST 망분리 가이드 / ISMS-P 2.6.2.",
        "severity_threshold": "critical",
        "definition": {"network_zones": ["dmz", "internal", "operation"], "deny_internet_egress": ["operation"]},
        "compliance_refs": ["K-CSAP-3.2", "ISMS-P-2.6.2"],
        "frameworks": ["K-CSAP", "ISMS-P"],
    },
    {
        "name": "CSAP — 백업 및 복구 검증",
        "policy_type": PolicyType.IAC,
        "description": "정기 백업(일1회) + 분기별 복구 테스트 결과 기록. K-CSAP 4.1 / ISMS-P 2.9.6 / 전자금융감독규정 21조.",
        "severity_threshold": "high",
        "definition": {"backup_interval_hours": 24, "restore_test_interval_days": 90},
        "compliance_refs": ["K-CSAP-4.1", "ISMS-P-2.9.6", "K-EFSA-21"],
        "frameworks": ["K-CSAP", "ISMS-P", "K-EFSA"],
    },
    {
        "name": "CSAP — 보안검증된 이미지만 배포",
        "policy_type": PolicyType.CONTAINER,
        "description": "공공 클라우드는 보안 검증을 통과한 골든 이미지만 사용. K-CSAP 5.2 / ISMS-P 2.9.3.",
        "severity_threshold": "high",
        "definition": {"require": "approved_image_registry"},
        "compliance_refs": ["K-CSAP-5.2", "ISMS-P-2.9.3"],
        "frameworks": ["K-CSAP", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 11. 전자금융감독규정 추가 (망분리·침해사고·DR)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "전자금융 — 망분리 (개발·운영·인터넷)",
        "policy_type": PolicyType.IAC,
        "description": "금융회사 정보처리시스템은 개발망·운영망·인터넷망 물리/논리 분리. 전자금융감독규정 17조 / ISMS-P 2.6.2 / SK쉴더스 EQST 가이드.",
        "severity_threshold": "critical",
        "definition": {"require_network_segregation": ["dev", "ops", "internet"]},
        "compliance_refs": ["K-EFSA-17", "ISMS-P-2.6.2"],
        "frameworks": ["K-EFSA", "ISMS-P"],
    },
    {
        "name": "전자금융 — 침해사고 24시간 신고",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "침해사고 인지 후 24시간 내 금감원·KISA 신고 절차 자동화. 전자금융감독규정 19조 / ISMS-P 2.11.5.",
        "severity_threshold": "critical",
        "definition": {"notify_within_hours": 24, "targets": ["fss", "kisa"]},
        "compliance_refs": ["K-EFSA-19", "ISMS-P-2.11.5"],
        "frameworks": ["K-EFSA", "ISMS-P"],
    },
    {
        "name": "전자금융 — DR 복구목표 (RTO 3h · RPO 1h)",
        "policy_type": PolicyType.IAC,
        "description": "중요 정보처리시스템 RTO ≤ 3시간, RPO ≤ 1시간. 전자금융감독규정 21조 / ISMS-P 2.9.6.",
        "severity_threshold": "high",
        "definition": {"rto_hours_max": 3, "rpo_hours_max": 1},
        "compliance_refs": ["K-EFSA-21", "ISMS-P-2.9.6"],
        "frameworks": ["K-EFSA", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 12. PCI DSS 추가 (카드 데이터 환경)
    # ════════════════════════════════════════════════════════════════
    {
        "name": "PCI DSS — PAN 마스킹 (앞6/뒤4)",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "Primary Account Number(PAN)는 표시 시 앞6·뒤4 외 마스킹. PCI DSS 3.4.1 / ISMS-P 3.3.",
        "severity_threshold": "critical",
        "definition": {"mask_pan": True, "preserve": {"prefix": 6, "suffix": 4}},
        "compliance_refs": ["PCI-DSS-3.4.1", "ISMS-P-3.3"],
        "frameworks": ["PCI-DSS", "ISMS-P"],
    },
    {
        "name": "PCI DSS — 분기별 외부 ASV 스캔",
        "policy_type": PolicyType.DAST,
        "description": "외부 노출된 PCI 자산은 분기마다 ASV(Approved Scanning Vendor) 스캔 통과. PCI DSS 11.3.2 / ISMS-P 2.11.1.",
        "severity_threshold": "high",
        "definition": {"scan_interval_days": 90, "scope": "external_pci_assets"},
        "compliance_refs": ["PCI-DSS-11.3.2", "ISMS-P-2.11.1"],
        "frameworks": ["PCI-DSS", "ISMS-P"],
    },
    {
        "name": "PCI DSS — 카드 데이터 24개월 보관 한도",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "카드 데이터(PAN·CVV·SAD) 보유기간 정책 문서화 + 자동 파기. PCI DSS 3.2 / K-PIPA 21조.",
        "severity_threshold": "high",
        "definition": {"retention_policy_required": True, "auto_purge": True},
        "compliance_refs": ["PCI-DSS-3.2", "K-PIPA-21"],
        "frameworks": ["PCI-DSS", "K-PIPA"],
    },

    # ════════════════════════════════════════════════════════════════
    # 13. GDPR 추가
    # ════════════════════════════════════════════════════════════════
    {
        "name": "GDPR — 국외이전 적정성/SCC 검증",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "EU→비적정국 개인정보 이전 시 SCC(표준계약조항) 또는 적정성 결정 보유 검증. GDPR Art.45·46 / K-PIPA 28조.",
        "severity_threshold": "high",
        "definition": {"require": "sccs_or_adequacy", "scope": "eu_data_export"},
        "compliance_refs": ["GDPR-Art-45", "GDPR-Art-46", "K-PIPA-28"],
        "frameworks": ["GDPR", "K-PIPA"],
    },
    {
        "name": "GDPR — 데이터 최소화 (수집 최소)",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "처리 목적에 비례한 최소 항목만 수집. 수집 폼/스키마 검토. GDPR Art.5(c) / K-PIPA 3조 / ISMS-P 3.1.",
        "severity_threshold": "medium",
        "definition": {"require": "purpose_field_review"},
        "compliance_refs": ["GDPR-Art-5", "K-PIPA-3", "ISMS-P-3.1"],
        "frameworks": ["GDPR", "K-PIPA", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 14. CIS Benchmarks 추가
    # ════════════════════════════════════════════════════════════════
    {
        "name": "CIS Linux — SSH 패스워드 인증 금지",
        "policy_type": PolicyType.IAC,
        "description": "SSH는 키 기반 인증만 허용 (PasswordAuthentication no, PermitRootLogin no). CIS Linux 5.2 / ISMS-P 2.5.3.",
        "severity_threshold": "high",
        "definition": {"sshd": {"PasswordAuthentication": False, "PermitRootLogin": False}},
        "compliance_refs": ["CIS-Linux-5.2", "ISMS-P-2.5.3"],
        "frameworks": ["CIS", "ISMS-P"],
    },
    {
        "name": "CIS AWS — S3 Block Public Access 계정 수준",
        "policy_type": PolicyType.IAC,
        "description": "계정 단위 Block Public Access 4종 모두 ON. CIS AWS 2.1.5 / AWS FSBP S3.1 / ISMS-P 2.6.1.",
        "severity_threshold": "critical",
        "definition": {"require": "account_level_block_public_access"},
        "compliance_refs": ["CIS-AWS-2.1.5", "AWS-FSBP-S3.1", "ISMS-P-2.6.1"],
        "frameworks": ["CIS", "ISMS-P"],
    },

    # ════════════════════════════════════════════════════════════════
    # 15. ISMS-P 추가 — 물리/인적 보안 영역
    # ════════════════════════════════════════════════════════════════
    {
        "name": "ISMS-P — 외주 직원 보안서약 / 입퇴직 점검",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "외주·파견 직원 보안서약서 + 입퇴직 시 계정·자산 회수 체크리스트. ISMS-P 1.5.1·1.5.2 / K-PIPA 1조.",
        "severity_threshold": "medium",
        "definition": {"require": ["nda", "onboarding_checklist", "offboarding_checklist"]},
        "compliance_refs": ["ISMS-P-1.5.1", "ISMS-P-1.5.2", "K-PIPA-1"],
        "frameworks": ["ISMS-P", "K-PIPA"],
    },
    {
        "name": "ISMS-P — 정보자산 위험평가 (연1회)",
        "policy_type": PolicyType.COMPLIANCE,
        "description": "전사 정보자산 식별·위험평가(연1회) 결과 첨부. ISMS-P 1.2.1·1.2.2 / ISO 27001 A.5.9.",
        "severity_threshold": "medium",
        "definition": {"interval_days": 365, "require": "risk_assessment_report"},
        "compliance_refs": ["ISMS-P-1.2.1", "ISMS-P-1.2.2", "ISO-27001-A.5.9"],
        "frameworks": ["ISMS-P", "ISO-27001"],
    },
]


# 빠른 카탈로그 필터링용 프레임워크 정의 (UI 칩으로 노출)
# short_name은 좁은 탭에서도 잘리지 않게 짧은 한글/약어 사용.
FRAMEWORKS: list[dict] = [
    {"id": "ISMS-P",    "short_name": "ISMS-P",  "name_ko": "ISMS-P (정보보호 관리체계, 국내)",        "name_en": "ISMS-P (KISA, KR)"},
    {"id": "K-EFSA",    "short_name": "전자금융", "name_ko": "전자금융감독규정 (국내)",                 "name_en": "Korean E-Finance Supervision"},
    {"id": "K-CSAP",    "short_name": "CSAP",    "name_ko": "CSAP — 공공 클라우드 (국내)",            "name_en": "Korean CSAP (public cloud)"},
    {"id": "K-PIPA",    "short_name": "PIPA",    "name_ko": "개인정보보호법 (국내)",                   "name_en": "Korean PIPA"},
    {"id": "ISO-27001", "short_name": "ISO 27001","name_ko": "ISO/IEC 27001:2022 (글로벌)",          "name_en": "ISO/IEC 27001:2022"},
    {"id": "OWASP",     "short_name": "OWASP",   "name_ko": "OWASP Top 10 (글로벌)",                  "name_en": "OWASP Top 10"},
    {"id": "CIS",       "short_name": "CIS",     "name_ko": "CIS Benchmarks (글로벌)",                "name_en": "CIS Benchmarks"},
    {"id": "PCI-DSS",   "short_name": "PCI DSS", "name_ko": "PCI DSS (글로벌 결제)",                  "name_en": "PCI DSS"},
    {"id": "GDPR",      "short_name": "GDPR",    "name_ko": "GDPR (EU)",                             "name_en": "GDPR (EU)"},
]


def list_templates(framework: str | None = None) -> list[dict]:
    if not framework:
        return list(TEMPLATES)
    return [t for t in TEMPLATES if framework in t.get("frameworks", [])]
