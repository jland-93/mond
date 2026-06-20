# 변경 로그 (Changelog)

이 프로젝트의 주목할 만한 모든 변경사항은 이 파일에 기록됩니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### Changed
- **GCP/Azure IAM grant 어댑터 완성도 보강** — GCP `attach`/`detach`는 read-modify-write etag 충돌(`aborted`/`etag`/`concurrent`/`conflict` 힌트)을 최대 3회 재시도. 이미 부여된 member는 즉시 success(idempotent). detach 시 binding이 비면 자동 제거. identity prefix(`user:`/`group:`/`serviceAccount:`) 자동 normalize. Azure `attach`는 동일 `(scope, principal, role)`이 이미 있으면 그대로 success로 흡수하고, race로 `RoleAssignmentExists`가 나도 success로 처리. unit test 6 케이스.

### Added
- **OPA Rego 정책 평가** — Policy 모델에 `engine` 컬럼 추가(`builtin`/`opa`). `engine="opa"`인 정책은 `definition.rego` (필수) + `definition.query` (선택, 기본 `data.mond.deny`)를 OPA 바이너리(subprocess, 8s timeout)로 평가하고 `deny`가 1건 이상이면 차단. backend Dockerfile에 OPA v1.17.1 정적 바이너리 번들(amd64/arm64). `GET /api/v1/integrations/opa`로 가용성 확인, Policies UI에 `engine` 배지(`opa` 청색). 시드에 `Sample OPA — Deny Trivy CVE-2024-0001` 비활성 데모 포함. lightweight migration(`ALTER TABLE policies ADD COLUMN IF NOT EXISTS engine ...`)로 기존 설치 자동 호환. OPA 다운로드 실패 시 build를 끊지 않고 graceful disable.
- **AI 프롬프트 PII redaction** — 외부 LLM provider(Anthropic/OpenAI/Bedrock/Ollama 등)로 사용자 쿼리를 보내기 전 이메일·한국 전화번호·주민등록번호·AWS access/secret key·GitHub token·일반 API token(`sk-`/`pat_`)·JWT·Luhn 통과 신용카드 번호를 자동 마스킹. 마스킹된 종류와 건수는 응답 `redactions` 필드로 노출되고 AI Insights UI에 `redacted email:N` 같은 chip으로 표시. `AI_PROMPT_REDACT_PII=false`로 끌 수 있음(기본 켜짐). RAG는 원본으로 검색하고 LLM에는 마스킹본만 전달.
- **Rate limit (abuse 보호)** — Redis 기반 fixed-window counter. `POST /auth/dev-login` 10/min/IP · `POST /ai/analyze` 20/min/user · `POST /webhooks/github` 120/min/IP · `POST /webhooks/personal` 30/min/IP · `POST /admin/github-sync/run` 5/min/user. 응답에 `X-RateLimit-Limit/Remaining/Reset` 헤더, 초과 시 429 + `Retry-After`. Redis 다운 시 fail open(가용성 우선). `RATE_LIMIT_ENABLED=false`로 전체 끄기 가능(test/CI 편의). SETUP.md에 표.
- **GitHub org 자산 자동 동기화** — Admin → Connections에 "GitHub Org Asset Sync" 카드. org 또는 user 이름 입력 → 미리보기/동기화 버튼으로 해당 org의 모든 repo를 `https://github.com/{owner}/{repo}` URI의 REPOSITORY 자산으로 일괄 등록. 동일 URI는 라벨(language/private/archived/default_branch)만 갱신하고 사용자가 수정한 owner/environment는 보존. `GITHUB_TOKEN` 있으면 private repo 포함 + rate limit 5000/h, 없으면 public 60/h. `GITHUB_ORG` 환경변수로 기본값 채울 수 있음. 백엔드 `POST /api/v1/admin/github-sync/run` 신설(Admin 전용).
- **GitHub Actions composite action** — `.github/actions/mond-scan/action.yml`. 사용자 repo의 workflow에서 `uses: jland-93/mond/.github/actions/mond-scan@main` 한 줄로 Mond 스캔 트리거. 입력: `mond_host` · `webhook_token` · `asset_id` · `scanner`. 출력: `scan_id` · `status`. backend의 기존 `POST /api/v1/webhooks/personal` 사용. README에 사용 예시 추가.
- **AI Insights RAG에 Asset 소스 추가** — 자연어 질의 시 RAG가 Asset(이름·URI·설명)도 함께 검색. "우리 nginx 자산" 같은 질문에 자산을 직접 짚어주고, citations에 kind=`asset`(녹색 chip)으로 노출. open_findings 수로 가중 정렬. 기존 Finding · Policy · Knowledge에 더해 4 소스 RAG.
- **Celery 비동기 스캔 큐** — `SCAN_QUEUE_ENABLED=true`로 켜면 인라인 동기 실행 대신 PENDING Scan 생성 + Celery 큐에 enqueue. 별도 worker(`mond.run_scan` task)가 비동기 실행하고 결과를 DB 업데이트. 대용량/장시간 스캔에서 backend 타임아웃 회피. 기본은 인라인(false)이라 OSS 첫 설치 영향 없음. `docker-compose.yml`에 `worker` 서비스 추가, Helm/Compose 모두 동일 패턴.
- **SBOM Diff on PR** — GitHub `pull_request` (opened / synchronize / reopened) webhook 이벤트에 변경된 의존성 파일을 감지해 before/after 파싱, 신규/제거/버전 변경을 정리. `GITHUB_TOKEN`이 설정되면 PR에 comment를 달고, FINDING purpose의 Slack 채널이 있으면 Slack에도 알림. 공개 repo는 토큰 없어도 raw fetch 가능.
- **SBOM 실 의존성 추출** — `package.json` / `package-lock.json` / `requirements.txt` / `go.mod` / Dockerfile 5종 파서. 백엔드 `POST /api/v1/reports/sbom/parse` (filename + content → ecosystem 감지 + 패키지 리스트). Reports 페이지에 "SBOM 파일 파싱" 카드 추가 (붙여넣기 → 추출 → 테이블). 기존 finding 기반 lightweight SBOM은 유지하되 stub Alert 톤을 정직화.
- **사용자별 Slack 알림 설정** — Security Settings의 "내 Slack 알림" 카드. 본인 DM webhook URL과 Slack user ID(@mention용)를 등록할 수 있고, 본인이 owner인 자산의 신규 finding 발생 시 organization 채널에 @mention + 본인 DM(설정 시) 발송. 별도 테이블 `user_slack_preferences`로 운영 중 환경에서도 schema migration 없이 자동 추가.
- **Slack 연동 별도 페이지** — `/admin/slack` (Admin). 워크스페이스의 Incoming Webhook URL을 5종 purpose(`default` · `digest` · `finding` · `access_request` · `role_request`) 채널에 매핑하고, 카드별로 테스트 메시지 전송. DB에 저장된 채널이 ENV(`SLACK_WEBHOOK_URL` · `DIGEST_SLACK_WEBHOOK_URL`)보다 우선. `notifications` · `digest` 둘 다 `slack.resolve_webhook(purpose)`로 라우팅 일원화.
- **권한 만료 임박 + 1-click 갱신** — My Mond (`/me`)의 "만료 임박" 카드 각 항목에 `갱신 요청` 버튼. 백엔드 `POST /api/v1/me/access-requests/{id}/renew`가 같은 identity·permission으로 새 AccessRequest를 만들어 AI 1차 검토 흐름에 태움. Daily Digest에도 3일 내 만료 권한 수가 추가됨.
- **Daily Security Digest** — 어제 일어난 일(신규 finding severity별 · 스캔 실행/실패 · 권한 요청 흐름)을 Slack 카드 한 장으로. Admin → Connections에 카드 + `지금 전송` 버튼. 자동 실행은 외부 cron(k8s CronJob 예시 포함)이 `POST /api/v1/admin/digest/send` 호출. 미리보기 `GET /api/v1/admin/digest/preview` (Reviewer+). 전용 채널 ENV `DIGEST_SLACK_WEBHOOK_URL` (없으면 `SLACK_WEBHOOK_URL` fallback).
- **My Mond** (`/me`) — 임직원 진입 페이지. 본인 자산 · 받은 발견사항 · 진행중 권한 요청 · 만료 임박(7일) 4 KPI + 4 list card. 사이드바 "한눈에" 그룹 최상단에 노출. 백엔드 `GET /api/v1/me/overview` 신설.
- **Findings 일괄 처리(Bulk Triage)** — Findings 테이블 row 체크박스 + 일괄 액션(Resolved / Suppressed / False-positive). 매주 발견사항 100개+ 처리하는 보안 담당자 시간을 1/10로. 백엔드 `PATCH /api/v1/findings/bulk/status` 신설 (REVIEWER+).
- **AI provider 추상화** — Anthropic · OpenAI / Azure OpenAI · AWS Bedrock · Ollama(로컬) 4종을 `AI_PROVIDER` 한 줄로 전환. 폐쇄망/데이터 외부 유출 금지 조직도 사용 가능.
- IAM Explorer 페이지에 IAM source kind별 capability 배지(Ready / Demo only / Coming soon) 노출.
- Reports 페이지 SBOM 섹션에 "experimental" 배지 + 디스클레이머.
- **OSS 운영 표준 도입** — `.github/CODEOWNERS` · Issue 템플릿 3종 + Discussions 동선 · Dependabot(weekly, 4 ecosystem) · CodeQL(Python + TypeScript) · Release Drafter + PR auto-label.

### Changed
- Knowledge Hub AI 카드 생성은 REVIEWER → **ADMIN** 권한으로 좁힘 (검토되지 않은 AI 콘텐츠가 사내 지식으로 노출되는 것을 막기 위함).
- 사이드바에서 `Integrations` 메뉴 항목 제거 (Admin → Connections로 통합됨, 라우트는 유지).
- README — v0.2 로드맵과 Known Limitations 섹션 정직화.
- **Policy Simulator** — `EXPERIMENTAL` 배지 + 실제 변경 안 일어남을 명시. 메뉴 노출 권한을 employee → **reviewer** 이상으로 격하.
- **MCP HTTP/SSE 기본값 변경** — `MCP_HTTP_ENABLED` 기본 `true` → `false`. Claude Desktop / Code 등 외부 에이전트에서 도구로 쓸 때만 켜기. `.env.example` · `docker-compose.yml` · `charts/mond/values.yaml` 모두 정렬.

### Removed
- `/integrations` 라우트와 `Integrations.tsx` 페이지 제거. Admin → Connections로 일원화된 뒤 dead code였음. 외부 링크가 있던 경우 `/admin/connections`로 이동.

### Fixed
- `frontend/Dockerfile`: nginx-unprivileged 1.27이 `/etc/nginx/conf.d`를 read-only로 만들어 발생한 envsubst 실패를 표준 `templates/` 패턴으로 해결. `docker-compose` 포트 매핑도 `3000:8080`으로 정렬.
- `backend/app/services/me.py`: unused `sqlalchemy.func` / `or_` import 제거 (ruff F401).

### Refactored
- `backend/app/iam/providers.py` 1,154줄을 패키지로 분해 — `base.py` + provider별 5 파일(`aws/k8s/ldap/gcp/azure`) + `registry.py`. 공개 import path는 그대로.
- `frontend/src/pages/admin/AdminConnections.tsx` 797줄 → 44줄 orchestrator + 6 sub-component (`connections/`).
- `frontend/src/pages/SecuritySettings.tsx` 773줄 → 47줄 orchestrator + 6 sub-component (`security/`).

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

---

## 🧭 문서 한눈에 · Doc Map

| 문서 | 무엇 |
|---|---|
| 🏠 [`README.md`](README.md) | 프로젝트 소개 · 스크린샷 |
| 🌙 [`docs/ABOUT.md`](docs/ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ [`docs/SETUP.md`](docs/SETUP.md) | 설치 · 운영 · 시나리오 가이드 |
| 🏗️ [`docs/development/architecture.md`](docs/development/architecture.md) | 시스템 구조 |
| 🤝 [`CONTRIBUTING.md`](CONTRIBUTING.md) | 기여 가이드 |
| 🔐 [`SECURITY.md`](SECURITY.md) | 취약점 신고 |
| 📜 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | 커뮤니티 규범 |
| 📋 [`CHANGELOG.md`](CHANGELOG.md) (이 문서) | 변경 내역 |
| ✅ [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) | 릴리즈 점검 |
