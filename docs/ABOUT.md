# Mond — 어떤 OSS인가요?

AI 기반 셀프서비스 DevSecOps 플랫폼. 자산, 스캔, 발견, 승인, 감사까지 한 흐름에서 다룹니다. 분석은 AI가, 결정은 사람이.

In English — Mond is a vendor-neutral, self-service DevSecOps platform. It folds asset inventory, scanning, AI-triaged findings, IAM access requests, policy simulation, and regulation mapping into a single flow. Bring your own scanners, your own AI provider, your own IdP. Mond stays opinionated about *flow* (auto-detect, human-decide, audit) and unopinionated about *vendors*.

---

## 한눈에 둘러보기

<div align="center">
  <a href="screenshots/01-dashboard.jpg">
    <img src="screenshots/01-dashboard.jpg" alt="Dashboard — Moon-phase 보안 점수 · 7일 trend · 활동 피드 · 주의 자산" width="100%"/>
  </a>
  <p><em>대시보드</em> — Moon-phase 보안 점수 · 7일 trend · 활동 피드 · 주의 자산 Top 5</p>
</div>

<table>
  <tr>
    <td width="50%" align="center">
      <a href="screenshots/05-login-hero.jpg"><img src="screenshots/05-login-hero.jpg" alt="Login Hero"/></a>
      <p><em>Login Hero</em> — 3D 초승달 + 3 pillars (AI Triage · Self-service · Auto-audit)</p>
    </td>
    <td width="50%" align="center">
      <a href="screenshots/03-ai-insights.jpg"><img src="screenshots/03-ai-insights.jpg" alt="AI Insights"/></a>
      <p><em>AI 인사이트</em> — 자연어로 자산·발견·정책 질의. 키 없으면 기본 규칙 모드</p>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <a href="screenshots/02-knowledge-hub.jpg"><img src="screenshots/02-knowledge-hub.jpg" alt="Knowledge Hub"/></a>
      <p><em>지식 허브</em> — DevSecOps · OWASP · K-PIPA · ISMS-P · PCI DSS · GDPR + AI 연계</p>
    </td>
    <td width="50%" align="center">
      <a href="screenshots/04-iam-explorer.jpg"><img src="screenshots/04-iam-explorer.jpg" alt="IAM Explorer"/></a>
      <p><em>IAM 탐색</em> — AWS · GCP · Azure · Kubernetes · LDAP/AD 멀티 클라우드 권한 + 위험도</p>
    </td>
  </tr>
</table>

---

## 왜 Mond를 만들었나

오늘날의 DevSecOps는 도구가 너무 많고, 발견사항이 너무 많고, 결정은 너무 느립니다.

- **5개 스캐너**가 각자 다른 UI · 다른 알림 채널 · 다른 우선순위 기준으로 발견사항을 쏟아냅니다.
- **권한 요청**은 Slack DM이나 Jira에 흩어져 있고, 누가 언제 뭘 줬는지 감사 흐름이 끊깁니다.
- **AI 도입**은 외산 SaaS에 코드를 통째로 던져야 하거나, 자체 호스팅은 너무 어렵습니다.
- **한국 규제(ISMS-P · PIPA · 전자금융감독규정)**는 글로벌 도구들이 거의 도와주지 않습니다.

Mond는 이 4가지를 한 번에 풉니다 — 단, **하나의 흐름**으로:

```
자산 등록 → 스캔 → AI 1차 트리아지 → 사람 결정 → 정책 시뮬 → 자동 감사 기록
```

화면이 따로 노는 게 아니라 같은 자산·같은 발견에 대한 다른 각도일 뿐입니다.

---

## 어떤 문제를 풉니다

### 1. 분석 노이즈를 AI가 1차 분류

Trivy 한 번 돌리면 수백 개 CVE. 다 critical로 보이지만 실제로 우리에게 critical인 건 5개. **Claude 또는 사용자가 선택한 LLM**이 자산 컨텍스트 (`production` · `customer-facing` · 사용 중인 dependency)와 함께 1차로 severity를 재평가하고, **수정 코드 스니펫**까지 제안합니다.

> "이 nginx 이미지의 CVE-2024-xxxx, 우리 LB 뒤에 있는데 진짜 critical?" → Claude가 컨텍스트 보고 high/info로 강등 + 이유 + diff.

### 2. 권한 요청 흐름이 끊기는 문제 — Self-service Access Center

직원이 직접 클라우드 권한을 요청하고, reviewer가 정책 시뮬레이션을 본 뒤 승인 / 반려. **5종 IAM 어댑터(AWS · GCP · Azure · K8s · LDAP/AD)**가 멀티 클라우드 권한을 한 화면에서 보여주고, 부여·회수 액션이 그대로 감사 로그가 됩니다.

> Slack DM "S3 권한 좀" → 흔적 없음 / Mond → 요청·승인·만료·회수가 한 자산에 시계열로 박힘.

### 3. 한국 규제 매핑 부재 — Regulations Guide와 정책 템플릿

K-PIPA · ISMS-P · 전자금융감독규정 · CSAP를 1급 시민으로. 글로벌 규제 (GDPR · HIPAA · PCI-DSS · SOC2 · ISO-27001 · COPPA · EU AI Act)도 함께. 정책마다 **어느 규제 조항에 매핑되는지** 자동으로 따라다닙니다.

> "ISMS-P 인증 받아야 하는데 우리 어디까지 했지?" → Mond Reports / Regulations에서 매핑 미충족 항목이 자동 리스트.

### 4. AI 도입 장벽 — Provider 추상화와 폐쇄망 옵션

`AI_PROVIDER` 한 줄로 Anthropic / OpenAI / AWS Bedrock / Ollama (로컬 LLM) 전환. **데이터 외부 유출 금지** 조직 (금융 · 공공 · 병원)도 Ollama 또는 사내 vLLM으로 똑같이 작동합니다. 키가 비면 휴리스틱(기본 규칙)으로 UI가 정상 동작 — 진입장벽 zero.

> 응답에는 `{provider}:{model}` 라벨이 항상 함께 박혀 출처 추적 가능.

---

## 무엇을 제공하나요

| 도메인 | 기능 |
|---|---|
| **자산 인벤토리** | repository · container_image · host · url · cloud_resource · application 6종. 라벨링, 환경(prod/staging/dev), 소유자, open findings count |
| **스캔** | Trivy(CVE/IaC/SBOM) · Semgrep(SAST) · Nuclei(DAST) 어댑터. 바이너리 없으면 stub 모드로 UI 데모. GitHub Webhook 자동 스캔 |
| **발견사항(Findings)** | severity 5종, 상태 6종(new/triaged/in_progress/resolved/suppressed/false_positive), fingerprint 기반 중복 제거 |
| **AI Insights** | Claude/GPT/Bedrock/Ollama로 1차 트리아지, 수정 코드 제안, 자연어 질의. 응답에 provider/모델 라벨 |
| **정책 + 시뮬레이션** | Policy 정의 → PR diff 미리보기. 정책마다 `compliance_refs` 자동 매핑 |
| **IAM 셀프서비스** | AWS · GCP · Azure · K8s · LDAP/AD 5종. Access Center에서 요청·승인·만료·회수. 위험도 라벨 |
| **지식 허브** | DevSecOps 기초 · OWASP Top 10 · 국내/해외 규제 핵심 · 베스트 프랙티스 · 사고 대응. 각 카드에서 "AI에 더 묻기" 원클릭 |
| **규제 가이드** | K-PIPA · ISMS-P · K-EFSA · CSAP · GDPR · HIPAA · PCI-DSS · SOC2 · ISO-27001 · COPPA · EU AI Act |
| **리포트** | SBOM(CycloneDX-lite) · Compliance 리포트 (JSON · Markdown) |
| **MCP** | stdio + HTTP/SSE 서버. Claude Desktop / Claude Code에서 Mond 데이터 자연어 조회 |
| **알림** | Slack Webhook · Generic Webhook (severity threshold 설정 가능) |
| **인증** | OIDC SSO (Keycloak · Okta · Google) + MFA (패스키 / TOTP / 백업코드) + RBAC 4-tier (viewer/employee/reviewer/admin) |

---

## 어떻게 더 확장하고 싶은가 (Roadmap)

### 단기 (v0.2)

- **SBOM 실 의존성 추출** — `package.json` · `go.mod` · `Dockerfile` 파싱. 현재는 stub
- **AI Insights RAG** — 조직 문서·정책을 벡터DB로 인덱싱해 응답 근거화. hallucination 위험 ↓
- **비동기 스캔 큐(Celery)** — 인라인 실행 대체. 대용량/장시간 스캔 지원
- **OPA Rego 정책 평가** — 정책을 코드로 작성, CI 통합
- **자산 자동 동기화** — Kubernetes / AWS Auto-scaling / GitHub org에서 자동 인벤토리
- **Webhook push 이벤트 → diff 분석 후 적절한 스캐너 선택** — push마다 전체 스캔 대신 변경분만
- **CI 통합 패키지** — GitHub Actions / GitLab CI step
- **Rate limiting · abuse protection**
- **AI 프롬프트 E2E 암호화** — 고객 코드 포함 시
- **GCP / Azure IAM grant 완성도 보강**

### 중장기 비전

1. **"보안팀이 1명 늘어난 효과"** — AI가 명확하게 일하는 영역(분류 · 1차 답변 · 정형화된 리포트)에서 인력 1명 분량을 안정적으로 대체
2. **한국 규제 1급 지원** — 인증 심사 대응 자료가 Mond에서 자동 생성
3. **폐쇄망 옵션** — Ollama / 사내 vLLM 게이트웨이만으로도 풀 스택. 금융·공공·의료 즉시 도입
4. **MCP 표준 적극 활용** — Claude Code 등 외부 에이전트가 Mond를 자연스럽게 다루는 도구로
5. **벤더 비종속 유지** — 어댑터 한 클래스로 새 스캐너·새 IdP·새 LLM 추가. AWS/특정 SaaS에 절대 못 묶임

### 비목표 (Non-goals)

- ❌ **에이전트 자체** (EDR/XDR 같은 endpoint 보안 도구)
- ❌ **WAF / 런타임 보호** — 다른 OSS에 위임
- ❌ **컴플라이언스 자문 그 자체** — 정책 매핑은 출발점일 뿐 법적 자문 아님

---

## 정직한 현재 한계 (v0.1)

신뢰성을 위해 명시합니다:

- **SBOM**: CycloneDX-lite stub (UI에 experimental 배지). 실 의존성 추출은 v0.2
- **스캐너 실행**: 동기 인라인. 대용량/장시간 스캔은 타임아웃 위험. 큐 도입 v0.2
- **AI Insights**: RAG 미적용. **hallucination 위험 인지 + 인간 검토 필수**. AI 생성 카드는 ADMIN 전용
- **IAM 어댑터**: AWS · K8s · LDAP/AD는 grant/revoke 완성. GCP · Azure는 capability API에서 `ready`/`coming_soon`/`demo`를 정직하게 노출
- **테스트 커버리지**: 의도적으로 낮음 (MVP). 기여 환영
- **규제 매핑**: 참고용 출발점. 법적 자문 아님

---

## 기여하기

[CONTRIBUTING.md](../CONTRIBUTING.md) 참고. 다음 기여를 환영합니다:

- 새 스캐너 어댑터 (`backend/app/scanners/`에 한 클래스 추가)
- 새 AI provider (`backend/app/ai/providers/`)
- 새 IdP / IAM 어댑터
- 한국 규제 정책 템플릿
- 지식 허브 카드
- 한국어 외 i18n

---

## 다음 단계

- 설치하기 — [docs/SETUP.md](SETUP.md) (Helm / Docker / AI / 로그인 / 관리자 초기 세팅)
- 개발하기 — [docs/development/architecture.md](development/architecture.md)
- 보안 정책 — [SECURITY.md](../SECURITY.md)
- 라이선스 — MIT

---

## 🧭 문서 한눈에 · Doc Map

| 문서 | 위치 | 무엇 |
|---|---|---|
| 🏠 **메인 README** | [`/README.md`](../README.md) | 프로젝트 소개 · 스크린샷 · 빠른 시작 |
| 🌙 **About** (이 문서) | [`docs/ABOUT.md`](ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ **Setup** | [`docs/SETUP.md`](SETUP.md) | 설치 · 운영 · 시나리오 가이드 |
| 🏗️ **Architecture** | [`docs/development/architecture.md`](development/architecture.md) | 시스템 구조 · 모듈 · 데이터 흐름 |
| 🎨 **Brand Guidelines** | [`docs/assets/brand-guidelines.md`](assets/brand-guidelines.md) | 로고 · 컬러 · 타이포 |
| 🤝 **Contributing** | [`/CONTRIBUTING.md`](../CONTRIBUTING.md) | 기여 가이드 · PR 규칙 |
| 🔐 **Security Policy** | [`/SECURITY.md`](../SECURITY.md) | 취약점 신고 절차 |
| 📜 **Code of Conduct** | [`/CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | 커뮤니티 규범 |
| 📋 **Changelog** | [`/CHANGELOG.md`](../CHANGELOG.md) | 버전별 변경 내역 |
| ✅ **Pre-release Checklist** | [`/PRE_RELEASE_CHECKLIST.md`](../PRE_RELEASE_CHECKLIST.md) | 릴리즈 전 점검 항목 |
| 📦 **Helm Chart** | [`/charts/mond/`](../charts/mond) | `values.yaml` · `values-prod.yaml` |
| 🐳 **Docker Compose** | [`/docker-compose.yml`](../docker-compose.yml) | 로컬 데모용 |
| ⚙️ **환경 변수 예시** | [`/.env.example`](../.env.example) | 모든 ENV 키 + 주석 |
