# 변경 로그 (Changelog)

이 프로젝트의 주목할 만한 모든 변경사항은 이 파일에 기록됩니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### Added
- **AI provider 추상화** — Anthropic · OpenAI / Azure OpenAI · AWS Bedrock · Ollama(로컬) 4종을 `AI_PROVIDER` 한 줄로 전환. 폐쇄망/데이터 외부 유출 금지 조직도 사용 가능.
- IAM Explorer 페이지에 IAM source kind별 capability 배지(Ready / Demo only / Coming soon) 노출.
- Reports 페이지 SBOM 섹션에 "experimental" 배지 + 디스클레이머.

### Changed
- Knowledge Hub AI 카드 생성은 REVIEWER → **ADMIN** 권한으로 좁힘 (검토되지 않은 AI 콘텐츠가 사내 지식으로 노출되는 것을 막기 위함).
- 사이드바에서 `Integrations` 메뉴 항목 제거 (Admin → Connections로 통합됨, 라우트는 유지).
- README — v0.2 로드맵과 Known Limitations 섹션 정직화.

## [0.1.0] — 2025-12

첫 OSS 공개 릴리스.

### Added — 핵심 도메인
- 5개 도메인 모델 — Asset · Scan · Finding · Policy · AIInsight
- 스캐너 어댑터 — Trivy · Semgrep · Nuclei (바이너리 없으면 stub 모드로 UI 데모)
- 정책 시뮬레이션 (가상 finding이 어떤 정책 게이트를 깨는지 미리보기)
- CycloneDX-lite SBOM 리포트 + 시나리오별 컴플라이언스 리포트 (JSON · Markdown)

### Added — AI
- Claude(Anthropic) 통합 — Haiku 기본, Sonnet 심층 분석
- Finding 자동 triage + remediation 가이드 (strict JSON)
- 자연어 쿼리 라우팅
- API 키 미설정 시 기본 규칙(휴리스틱) 모드 자동 폴백
- MCP 서버 (stdio + HTTP/SSE) — Claude Desktop / Claude Code 통합

### Added — 인증 / 인가 / 보안
- 멀티유저 OIDC SSO (Keycloak · Okta · Google · Azure AD)
- 서버 세션 (opaque token + SHA-256 hash, 즉시 revoke 가능)
- 4-tier RBAC — VIEWER < EMPLOYEE < REVIEWER < ADMIN
- MFA — 패스키(WebAuthn / FIDO2) + TOTP + 일회용 백업 코드
- `MFA_REQUIRED_ROLES` ENV로 강제 대상 role 지정 (기본 `admin,reviewer`)
- 운영 부팅 가드 — 약한 SECRET_KEY / DEBUG=true / AUTH_MODE=dev / SESSION_SECURE=false 거부

### Added — IAM 셀프서비스
- IAM 어댑터 5종 — AWS · Kubernetes · LDAP/AD · GCP · Azure
- 권한 요청 흐름 — AI 1차 검토 + 담당자 2차 승인 + 자동 grant + 만료 자동 회수
- 자격증명은 DB에 저장하지 않음 (ENV 키 이름만 보관)

### Added — 정책 카탈로그
- 54개 정책 템플릿 (KISA ISMS-P · 금융위 전자금융감독규정 · KISA K-PIPA · K-CSAP · ISO/IEC 27001:2022 · OWASP Top 10 · CIS Benchmarks · PCI DSS · GDPR 매핑)
- UI에서 카탈로그 다중 선택 → 일괄 적용
- 사내 고유 통제는 UI에서 직접 작성 가능 (자유 입력 compliance_refs)

### Added — UI / UX
- React + Vite + Ant Design 다크 테마 ("달빛 무드")
- 한국어 기본 · 영어 보조 (i18n + antd locale sync)
- 관리자 전용 영역 (`/admin/*`) — 권한 검토 / 정책 관리 / 연동 관리 / 사용자·역할
- 보안 설정 페이지 — 패스키·TOTP·백업 코드 관리

### Added — 배포
- 운영용 멀티스테이지 Docker 이미지 (non-root, tini, healthcheck, multi-arch)
- Helm 차트 (`charts/mond/`) — in-cluster Postgres/Redis 또는 외부 RDS/ElastiCache 토글
- GitHub Actions release workflow — 태그 push 시 ghcr.io에 이미지 + OCI Helm chart 자동 발행

### Added — 통합
- GitHub Webhook (push 이벤트 → 매칭 자산 자동 trivy 스캔)
- Generic Webhook (사내 CI 통합용, EMPLOYEE 인증)
- Slack / Generic Webhook 알림 (임계치 이상 finding 자동 전송)

### Known Limitations
- 백엔드 테스트 커버리지는 의도적으로 낮음 (MVP) — 기여 환영
- OPA Rego 정책 평가는 미구현 (로드맵)
- CI 통합 패키지 (GitHub Actions / GitLab CI step) 미구현 (로드맵)
- Rate limiting / abuse protection 미구현 (로드맵)
- 정책 템플릿의 규제 조항 매핑은 참고용이며 법적 자문이 아닙니다.

[Unreleased]: https://github.com/jland-93/mond/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jland-93/mond/releases/tag/v0.1.0
