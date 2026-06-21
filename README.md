# Mond

<div align="center">
  <img src="docs/assets/images/mond-logo.png" alt="Mond Logo" width="280"/>

  <h3>AI-Powered Self-Service DevSecOps Platform<br/>AI 기반 셀프서비스 DevSecOps 플랫폼</h3>

  <p>
    <em>분석은 AI가, 결정은 사람이.</em><br/>
    <em>AI does triage. You decide what matters.</em>
  </p>

  <p>
    자산, 스캔, 발견, 승인, 감사까지 한 흐름에서.<br/>
    Inventory, scan, triage, approve, audit in one flow.
  </p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
  [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
  [![Claude](https://img.shields.io/badge/AI-Claude-7c8cff.svg)](https://www.anthropic.com/)
  [![Helm](https://img.shields.io/badge/Helm-OCI-0F1689.svg)](https://github.com/jland-93/mond/pkgs/container/charts%2Fmond)
</div>

<br/>

<div align="center">
  <a href="docs/screenshots/01-dashboard.jpg">
    <img src="docs/screenshots/01-dashboard.jpg" alt="Mond Dashboard — Moon-phase 보안 점수 · 7일 trend · 활동 피드 · 주의 자산" width="100%"/>
  </a>
  <p>
    <sub>
      <a href="docs/SETUP.md#part-5-관리자-초기-세팅-체크리스트">관리자 초기 세팅</a> ·
      <a href="docs/ABOUT.md#무엇을-제공하나요">무엇을 제공?</a> ·
      <a href="docs/SETUP.md#part-0-어느-시나리오인가요">내 시나리오 고르기</a>
    </sub>
  </p>
</div>

---

## 더 많은 화면 · More previews

<table>
  <tr>
    <td width="50%">
      <a href="docs/screenshots/05-login-hero.jpg"><img src="docs/screenshots/05-login-hero.jpg" alt="Login Hero — 3D Moon + AI Triage / Self-service / Auto-audit"/></a>
      <p align="center">
        <strong>Login Hero</strong> · 3D 초승달 · 3 pillars (AI Triage · Self-service · Auto-audit)<br/>
        <sub><a href="docs/SETUP.md#part-4-로그인--dev--sso--mfa">로그인 · SSO · MFA 설정</a></sub>
      </p>
    </td>
    <td width="50%">
      <a href="docs/screenshots/03-ai-insights.jpg"><img src="docs/screenshots/03-ai-insights.jpg" alt="AI Insights — Claude 자연어 질의"/></a>
      <p align="center">
        <strong>AI 인사이트</strong> · 자연어로 자산·발견·정책 질의. 키 없으면 기본 규칙 모드<br/>
        <sub><a href="docs/SETUP.md#part-3-ai-provider-세팅">AI provider 세팅 (Anthropic / OpenAI / Bedrock / Ollama)</a></sub>
      </p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <a href="docs/screenshots/02-knowledge-hub.jpg"><img src="docs/screenshots/02-knowledge-hub.jpg" alt="Knowledge Hub — DevSecOps + 규제 카드 + AI 연계"/></a>
      <p align="center">
        <strong>지식 허브</strong> · DevSecOps · OWASP · K-PIPA · ISMS-P · PCI DSS · GDPR — AI에 바로 이어 묻기<br/>
        <sub><a href="docs/ABOUT.md#3-한국-규제-매핑-부재--regulations-guide와-정책-템플릿">한국 규제 매핑</a></sub>
      </p>
    </td>
    <td width="50%">
      <a href="docs/screenshots/04-iam-explorer.jpg"><img src="docs/screenshots/04-iam-explorer.jpg" alt="IAM Explorer — AWS / GCP / Azure / K8s / LDAP 통합 권한 탐색"/></a>
      <p align="center">
        <strong>IAM 탐색</strong> · AWS · GCP · Azure · Kubernetes · LDAP/AD 멀티 클라우드 권한 + 위험도<br/>
        <sub><a href="docs/SETUP.md#4-iam-source-연동-admin--connections">IAM Source 연동</a></sub>
      </p>
    </td>
  </tr>
</table>

---

## 📚 어떤 OSS인가요? · What is Mond?

- **무엇을 푸는가** — DevSecOps 도구가 너무 흩어져 있고, 발견사항이 너무 많고, 의사결정은 너무 느립니다. Mond는 **AI가 1차 분석**해서 **사람이 결정만** 하면 되는 흐름을 만듭니다.
- **어떻게 다른가** — 클라우드 / 스캐너 / AI provider / IdP — 어디에도 묶이지 않습니다. 어댑터로 갈아끼우고, 한국어가 1급 시민입니다.
- **어디로 가는가** — v0.2(Unreleased): 자산 자동 동기화 · RAG 기반 AI Insights · OPA Rego 평가 · CI 패키지 · SBOM diff · 스캐너 자동 라우팅 등 11개 항목 완료. v0.3: 멀티 클러스터 K8s 자동 동기화, AWS Auto-scaling, 한국 규제 1급 지원.

> 📖 **자세한 이야기는 → [docs/ABOUT.md](docs/ABOUT.md)**
> 🛠️ **설치·운영 가이드 → [docs/SETUP.md](docs/SETUP.md)**

In English: a vendor-neutral, self-service DevSecOps platform that consolidates asset inventory, scanning, AI-triaged findings, IAM access requests, policy simulation, and regulation mapping into a single flow. Bring your own scanners (Trivy/Semgrep/Nuclei/...), your own AI provider (Anthropic/OpenAI/Bedrock/Ollama), your own IdP (Keycloak/Okta/Google). See [docs/ABOUT.md](docs/ABOUT.md) and [docs/SETUP.md](docs/SETUP.md).

---

## ⚡ 시작하기 · Get started

### 🐳 Docker Compose — 30초 데모 (로컬·평가용)

```bash
git clone https://github.com/jland-93/mond.git && cd mond
cp .env.example .env
# (선택) ANTHROPIC_API_KEY를 .env에 넣으면 실제 Claude 분석이 동작합니다.
docker compose up -d
```

- 프론트 → <http://localhost:3000>
- 백엔드 docs → <http://localhost:8000/docs>
- 첫 가입자가 자동 `ADMIN`. MFA(패스키 or TOTP) 1회 등록 후 진입.

### ⛵ Helm chart — 운영 배포 (Kubernetes)

OCI 레지스트리에 자동 배포되는 차트로 한 줄 설치:

```bash
helm install mond oci://ghcr.io/jland-93/charts/mond \
  --version 0.1.0 \
  -n mond --create-namespace \
  -f charts/mond/values-prod.yaml \
  --set ingress.hosts[0].host=mond.your-corp.com \
  --set secrets.existingSecret=mond-secrets
```

- 차트 소스 → [`charts/mond/`](charts/mond) (`values.yaml` · `values-prod.yaml`)
- 자동 배포 → 태그 push 시 [`.github/workflows/release.yml`](.github/workflows/release.yml) helm job
- 컨테이너 이미지 → `ghcr.io/jland-93/mond-backend:<ver>` · `…-frontend:<ver>` (multi-arch amd64/arm64)
- EKS / GKE / AKS 권장 설정 · 시크릿 관리(External-Secrets) → **[docs/SETUP.md Part 2](docs/SETUP.md#part-2-helm-chart로-kubernetes-운영-배포)**

> 🛠️ SSO · MFA · AI provider 전환 · 관리자 초기 세팅 → **[docs/SETUP.md](docs/SETUP.md)**

### 🤖 GitHub Actions — 한 줄 통합

CI/CD에서 push 또는 PR마다 Mond 스캔을 자동 트리거. Security Settings에서 webhook 토큰 발급 → repo secrets에 등록 → workflow에 다음 step 한 줄.

```yaml
- name: Mond scan
  uses: jland-93/mond/.github/actions/mond-scan@main
  with:
    mond_host: mond.your-corp.com
    webhook_token: ${{ secrets.MOND_WEBHOOK_TOKEN }}
    asset_id: 42          # Mond UI Assets 페이지에서 ID 확인
    scanner: trivy        # trivy | semgrep | nuclei
```

자동 생성된 YAML은 Mond `Security Settings → Personal Webhook Tokens → CI 스니펫 생성`에서도 받을 수 있습니다.

---

## 📋 Overview

**Mond** (독일어로 "달")은 어떤 클라우드든 어떤 스캐너든 상관없이 동작하는, **AI 기반 셀프서비스 DevSecOps 플랫폼**입니다. 자산 / 스캔 / 발견사항 / 정책을 단일 모델로 다루고, Claude를 활용해 발견된 이슈를 **자동 트리아지** 하고 **수정 가이드**까지 제시합니다.

### 🎯 Why Mond?

- **벤더 비종속** — Trivy / Semgrep / Nuclei를 어댑터로 통합. AWS / 특정 클라우드에 묶이지 않음.
- **AI 셀프서비스** — Claude가 발견사항을 분석해 severity 재평가, 수정 코드 제안, 자연어 쿼리 응답.
- **즉시 사용** — `docker compose up` 한 줄. 스캐너 바이너리가 없으면 stub 모드로 UI 데모.
- **모듈식** — 새 스캐너는 `ScannerAdapter` 한 클래스로 추가.
- **Mond 다크 테마** — 가독성 높은 달빛 무드 (다크 네이비 + 보라 글로우).

---

## ✨ 핵심 기능

| 메뉴 | 기능 |
|---|---|
| **Dashboard** | 보안 점수, 자산/발견 통계, 최근 스캔 |
| **Assets** | 자산 인벤토리 (repo / image / host / URL / cloud / app) |
| **Scans** | 스캔 트리거 + 어댑터별 실행 이력 |
| **Findings** | 발견사항 조회/상태 변경 + AI 분석 드로어 |
| **Policies** | SAST / SCA / IaC / DAST / Container / Secrets / Compliance 룰셋 |
| **Policy Simulation** | "이번 PR에 이 finding이 들어가면 어떤 정책이 깨질까" 미리보기 |
| **AI Insights** | 자연어 쿼리, intent 분류, Claude 답변 |
| **Regulations Guide** | 사업 시나리오 → 적용 규제(K-PIPA·GDPR·HIPAA·PCI-DSS·…) + 시점·의무 |
| **Reports** | 자산별 SBOM(CycloneDX 1.5 표준 — components purl + vulnerabilities) + 시나리오별 컴플라이언스 리포트 (JSON / Markdown) |
| **Integrations** | 스캐너 / AI / **MCP (stdio+HTTP)** / 알림 채널 / GitHub Webhook 안내 |
| **Settings** | 헬스 / 버전 / 환경 / 언어 |

### 한국어 기본 · 영어 보조 (i18n)

UI는 한국어를 기본으로 표시하며, 우측 상단 토글로 영어로 전환할 수 있습니다.
`DEFAULT_LOCALE=ko|en`로 초기값을 바꿀 수 있고, 선택은 브라우저 localStorage에 지속됩니다.

### 셀프서비스 자동화

| 기능 | 방식 |
|---|---|
| **자동 스캔 (GitHub push)** | `POST /api/v1/webhooks/github` → 매칭 레포 자산 자동 trivy 스캔 |
| **알림 다채널** | 임계치 이상 finding을 Slack/Discord/Teams/Generic webhook으로 자동 전송 (채널별 형식 변환) |
| **MCP — Claude Desktop/Code** | stdio: `python -m mcp_server`. HTTP+SSE: `/mcp` 마운트 |

---

## 🏗️ 아키텍처

```mermaid
graph LR
    UI[Web UI<br/>React + Vite + Ant Design]
    API[REST API<br/>FastAPI + asyncpg]
    AI[AI Engine<br/>Anthropic Claude]
    SCAN[Scanner Adapters<br/>Trivy · Semgrep · Nuclei]
    DB[(PostgreSQL)]
    R[(Redis)]

    UI -->|/api/v1| API
    API --> DB
    API --> R
    API --> AI
    API --> SCAN
```

5개 핵심 도메인: **Asset · Scan · Finding · Policy · AIInsight**

- `Asset` — 보호 대상 (URI + 라벨 + 환경)
- `Scan` — 어댑터 1회 실행 결과
- `Finding` — fingerprint 기반 dedup된 보안 이슈
- `Policy` — 룰셋 + 컴플라이언스 매핑
- `AIInsight` — Claude가 만든 triage / remediation / explain

---

## 🚀 Quick Start

### 사전 요구사항

- Docker & Docker Compose
- (선택) `ANTHROPIC_API_KEY` — 없어도 기본 규칙 모드로 모든 화면이 동작합니다.

### 실행

```bash
git clone https://github.com/jland-93/mond.git
cd mond
cp .env.example .env
# .env에 ANTHROPIC_API_KEY를 넣으면 실제 Claude 분석이 작동합니다.
docker compose up -d
```

- 백엔드 API: <http://localhost:8000/docs>
- 프론트엔드: <http://localhost:3000>

첫 부팅 시 데모 자산 3개(레포 / 컨테이너 이미지 / URL)와 정책 3개가 자동 시드됩니다.

### 첫 ADMIN 로그인 — 막힘 방지 가이드

`/login` 화면에 이메일을 입력해 첫 로그인하는 사용자가 자동으로 **ADMIN**으로 가입됩니다.
ADMIN은 기본 `MFA_REQUIRED_ROLES=admin,reviewer` 정책에 따라 즉시 `/mfa`로 이동하며,
**패스키 또는 TOTP 중 하나를 인라인으로 등록**해야 합니다.

| 환경 | 등록 가능 수단 |
|---|---|
| **`http://localhost:3000`** | 패스키(브라우저 생체인증) + TOTP 모두 가능 |
| **사내 IP / HTTP 도메인** (예: `http://192.168.1.10:3000`) | 패스키는 브라우저 정책상 **차단** — **TOTP**를 사용하세요 (Google Authenticator · 1Password · Authy) |
| **HTTPS 운영 도메인** | 둘 다 정상 |

#### 만약 잠겼다면 — 운영자 복구 CLI

비밀번호 매니저 분실 등으로 모든 MFA factor에 접근할 수 없게 됐을 때:

```bash
docker compose exec backend python -m scripts.admin_unlock admin@example.com
# 또는 확인 프롬프트 없이:
docker compose exec backend python -m scripts.admin_unlock admin@example.com --yes
```

해당 사용자의 모든 MFA factor (패스키·TOTP·백업코드)가 삭제되고, 다음 화면에서
**첫 등록 화면**이 다시 보입니다. 사용자 데이터·자산·정책은 그대로 유지됩니다.

#### MFA 강제 완화 (개발/데모 환경)

데모 환경에서 MFA 강제를 끄고 싶다면 `.env`에:

```bash
# 아무도 강제 안 함 (옵션으로만)
MFA_REQUIRED_ROLES=
# 또는 ADMIN만 빼기
MFA_REQUIRED_ROLES=reviewer
```

운영에서는 **반드시 `admin,reviewer` 이상** 유지를 권장합니다.

### 로컬 개발 (도커 없이)

```bash
# 백엔드
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://mond:mond@localhost:5432/mond \
  uvicorn main:app --reload

# 프론트엔드
cd frontend
npm install
npm run dev
```

### 운영 배포 — Kubernetes (Helm)

태그가 푸시되면 `ghcr.io`에 `mond-backend`/`mond-frontend` 이미지와 OCI Helm 차트가 자동 배포됩니다.

```bash
# 1) 시크릿 미리 생성 (External-Secrets/Sealed-Secrets로 대체 가능)
kubectl create ns mond
kubectl -n mond create secret generic mond-secrets \
  --from-literal=SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  --from-literal=SSO_PROVIDERS="keycloak" \
  --from-literal=SSO_KEYCLOAK_ISSUER="https://keycloak.your-corp.com/realms/mond" \
  --from-literal=SSO_KEYCLOAK_CLIENT_ID="mond" \
  --from-literal=SSO_KEYCLOAK_CLIENT_SECRET="..." \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:pwd@rds.../mond" \
  --from-literal=REDIS_URL="redis://elasticache.../0"

# 2) Helm 설치 (OCI 레지스트리)
helm install mond oci://ghcr.io/jland-93/charts/mond \
  --version 0.1.0 \
  -n mond \
  -f charts/mond/values-prod.yaml \
  --set ingress.hosts[0].host=mond.your-corp.com
```

자세한 옵션: [`charts/mond/values.yaml`](charts/mond/values.yaml) · [`charts/mond/values-prod.yaml`](charts/mond/values-prod.yaml)

#### EKS 가이드

| 항목 | 권장 |
|---|---|
| 이미지 | `ghcr.io/jland-93/mond-backend:<ver>` · `…-frontend:<ver>` (multi-arch amd64/arm64) |
| DB / 캐시 | RDS Postgres 16 + ElastiCache Redis (subchart `postgresql.enabled=false`) |
| Ingress | AWS Load Balancer Controller (`ingressClassName: alb` + ACM) |
| 시크릿 | External-Secrets Operator → AWS Secrets Manager / Parameter Store |
| 컴퓨트 | IRSA로 `serviceAccount.annotations`에 IAM Role ARN 부여 |
| 관측 | Prometheus 스크레이프 — backend 컨테이너 8000/metrics |

운영 환경(`ENVIRONMENT=production`)에서는 약한 `SECRET_KEY`/`DEBUG=true`/`AUTH_MODE=dev`/`SESSION_SECURE=false` 조합을 **부팅 단계에서 거부**합니다 ([backend/app/core/config.py](backend/app/core/config.py)).

---

## 🤖 AI 동작 방식

**자기 환경의 AI API를 직접 끌어다 씁니다.** 모든 provider가 같은 추상화 layer를 통해 호출되며, `.env`에서 한 줄로 전환됩니다.

| Provider | ENV | 모델 예시 | 한국에서 의미 |
|---|---|---|---|
| **Anthropic** (직접) | `AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` | 기본값 |
| **OpenAI / Azure OpenAI** | `AI_PROVIDER=openai` + `OPENAI_API_KEY` (+ `OPENAI_BASE_URL` for Azure) | `gpt-4o-mini` / `gpt-4o` | GPT 라이선스가 있는 조직 |
| **AWS Bedrock** | `AI_PROVIDER=bedrock` + IAM 자격 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | AWS 비용·정책 통합 |
| **Ollama / vLLM (로컬)** | `AI_PROVIDER=ollama` + `OLLAMA_BASE_URL` | `llama3.1:8b` / `llama3.1:70b` | 폐쇄망·금융·공공·병원 — **데이터 외부 유출 금지** 조직 |

키를 설정하지 않으면 **기본 규칙 fallback**으로 모든 UI가 작동합니다. 응답에는 항상 `{provider}:{model}` 라벨이 함께 기록되어 출처 추적이 가능합니다.

```bash
# 예) GPT를 쓰는 조직
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL_DEFAULT=gpt-4o-mini

# 예) 사내 폐쇄망에서 Ollama로
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama.internal:11434
OLLAMA_MODEL_DEFAULT=llama3.1:8b
```

---

## 🧩 스캐너 어댑터

`backend/app/scanners/`에서 새 어댑터를 만들 수 있습니다.

```python
class MyAdapter(ScannerAdapter):
    name = "my-tool"
    supported_asset_types = (AssetType.REPOSITORY.value,)

    async def scan(self, asset: Asset) -> ScanResult:
        ...
        return ScanResult(findings=[...], raw_output={...})
```

`registry.py`에 한 줄 등록하면 UI 메뉴(Integrations) + 스캔 트리거(Scans)에 즉시 노출됩니다. 바이너리가 없을 때는 stub 결과를 반환하도록 구현해 사용자가 빈 화면을 보지 않도록 하는 것을 권장합니다.

기본 동봉 어댑터:
- **Trivy** — 컨테이너 이미지 / IaC / SBOM
- **Semgrep** — 정적 코드 분석 (SAST)
- **Nuclei** — 템플릿 기반 동적 스캔 (DAST)

---

## 🗺️ 로드맵

- [x] 5도메인 + AI 트리아지 MVP
- [x] Trivy / Semgrep / Nuclei stub 어댑터
- [x] 한국어/영어 i18n (ko 기본 · en 보조)
- [x] Regulations Guide (K-PIPA · ISMS-P · K-EFSA · CSAP · GDPR · HIPAA · PCI-DSS · SOC2 · ISO-27001 · COPPA · EU AI Act)
- [x] Policy Simulation (PR diff 미리보기)
- [x] SBOM / Compliance 리포트 (JSON · Markdown)
- [x] GitHub Webhook 자동 스캔
- [x] Slack / Discord / MS Teams / Generic Webhook 알림 (채널별 포맷 변환)
- [x] MCP 서버 (stdio + HTTP/SSE)
- [x] 멀티유저 + RBAC + OIDC SSO (Keycloak · Okta · Google)
- [x] MFA — 패스키(WebAuthn/FIDO2) + TOTP + 백업 코드
- [x] IAM 셀프서비스 — AWS · Kubernetes · LDAP/AD · GCP · Azure (5종 어댑터)
- [x] Helm 차트 (charts/mond) + 운영용 멀티스테이지 Docker 이미지
- [x] AI provider 추상화 — Anthropic · OpenAI · AWS Bedrock · Ollama(로컬)

### v0.2 로드맵 — 완료 (Unreleased)

핵심 기능:
- [x] SBOM 실 의존성 추출 — `package.json` · `package-lock.json` · `requirements.txt` · `go.mod` · `Dockerfile` 5종 파서 + Reports UI
- [x] SBOM Diff on PR — `pull_request` 이벤트에 신규/제거/버전 변경 추출 + PR comment + Slack
- [x] AI Insights RAG — Asset · Finding · Policy · Knowledge 4 소스 검색 + `[N]` 인용
- [x] 비동기 스캔 큐 (Celery) — `SCAN_QUEUE_ENABLED=true`로 enqueue, 별도 worker
- [x] OPA Rego 정책 평가 — backend Dockerfile에 OPA v1.x 번들 + `Policy.engine="opa"`로 Rego 평가
- [x] 자산 자동 동기화 — GitHub org (Kubernetes / AWS Auto-scaling은 v0.3)
- [x] Webhook push 이벤트 → diff 분석 후 적절한 스캐너 선택 (semgrep · trivy · nuclei 자동 라우팅)
- [x] CI 통합 패키지 — `.github/actions/mond-scan` composite action 한 줄 통합
- [x] Rate limiting / abuse protection — login · AI · webhook · github-sync (Redis 기반)
- [x] AI 프롬프트 PII redaction — 외부 LLM 호출 전 이메일/전화/RRN/AWS키/토큰 자동 마스킹
- [x] GCP / Azure IAM 어댑터 권한 부여(grant) 완성도 보강 — 멱등성 + etag 충돌 재시도

UX·가시화 보강:
- [x] IAM Explorer 가시화 — ARN/UUID/LDAP DN을 사람이 읽는 이름으로(`displayName`/email/ARN tail/RDN/UUID 단축). Source segmented 필터 + 통합 검색 + Permission inline `권한 요청` CTA
- [x] AWS IAM Identity Center 지원 — `IdentityType.SSO_USER`/`SSO_GROUP` 분리 + 자홍색 `SSO` 태그
- [x] Access Center 폼 친화화 — 질문형 라벨('어떤 권한이 필요한가요?'·'얼마나 오래 쓸 건가요?'·'왜 필요한가요?') + 실제 인시던트 예시 placeholder
- [x] Access Review 위험도 색띠 — `critical`/`high` 행 좌측 색띠, AI 결정(verdict + risk + reason) 카드 형식
- [x] MyMond 빈 상태 카드 친화화 — 신규 임직원이 첫 진입 시 '담당 자산이 없습니다 → 자산 보기', '아직 요청한 권한이 없습니다 → 권한 요청 시작' CTA
- [x] 위험도·상태 라벨 한국어 통일 — `risk: high` → `위험도: 높음`, `granted` → `권한 부여 완료` 등
- [x] 라우트별 코드 스플릿 — 첫 로드 1834KB → **684KB** (63% 감소). three.js 873KB는 Moon3D hero 화면에서만 lazy 로드
- [x] Scans 페이지 가시화 — 자산 ID → 이름, webhook smart-router 자동 선택 결과(이유·카테고리 카운트) row expand
- [x] Findings drawer 가시화 — 발견 자산 카드 + AI 인사이트(severity 재평가 화살표·confidence Progress bar·remediation references)
- [x] Assets owner inline edit — '내 자산으로' 1클릭 + Popover 편집
- [x] Knowledge Hub 출처 명료화 — `📖 기본 카드` / `🤖 AI 생성` / `📖 직접 작성` + AI 카드 보라 테두리
- [x] Regulations Guide 카드 그리드 + 시각 위계 — 시나리오 카드 그리드, 규제 카드 2열(관할 색·시점·의무·참고)
- [x] Dashboard '다음 단계' 가이드 배너 — admin 5단계 / employee 3단계, 완료 시 자동 hide
- [x] AI Insights citation deep-link — `?focus=N`으로 자산/finding/정책에서 자동 drawer/highlight
- [x] Admin Policies — engine 컬럼 + 임계치 색 dot
- [x] Settings — 4 KPI 카드(backend·DB·AI·OPA) + 스캐너 어댑터 + 환경
- [x] AI Insights '이어서 묻기' follow-up chip — intent별 표준 후보 + Claude `suggested_actions`
- [x] PolicySimulator — engine + OPA deny 메시지 expand + 위험도 색
- [x] Admin Users — MFA 등록 상태 + SSO 출처 + 최근 로그인 상대 표기

### v0.3 후보 로드맵
- [ ] **자산 자동 동기화 확장** — Kubernetes 클러스터 namespace/pod 자동 발견, AWS Auto-scaling group, GitLab/Bitbucket org sync
- [x] **AI 멀티 프로바이더 라우팅** — 의도(`intent`)별 model 자동 라우팅 (`remediation`/`explain`/`deep_analysis`는 `model_deep`, 그 외 `model_default`)
- [x] **SBOM CycloneDX 정식 출력** — CycloneDX 1.5 표준 (`bomFormat: "CycloneDX"`, `serialNumber: urn:uuid:…`, `metadata.tools`, REPOSITORY 자산은 default branch에서 `components[]` 자동 추출, findings → 표준 `vulnerabilities[]`)
- [ ] **MCP HTTP 마운트 안정화** — Claude Desktop/Code 외부 에이전트가 Mond를 도구로 자연스럽게 사용
- [ ] **다중 워크스페이스/조직 분리** — 사내 여러 팀이 한 인스턴스를 공유할 때 자산/정책 scope
- [x] **감사 로그 검색 UI** — `Admin → 감사 로그`에서 기간/actor/event/request_id 필터 + 시계열 timeline
- [ ] **한국 규제 인증 심사 패키지** — ISMS-P 자동 증빙 자료 출력 (실제 심사 대응)
- [x] **알림 라우팅 다채널** — Slack 외 Discord + MS Teams webhook 추가 (severity 색상 채널별 변환)
- [x] **온프레미스 LLM 게이트웨이 + 토큰 사용량 추적** — vLLM provider (OpenAI-호환 base_url) + `ai_usage_logs` 테이블 자동 기록 + `GET /admin/ai-providers/usage` (provider/tier/intent/일별 시계열) + Admin 연동 관리에 AI 사용량 카드
- [x] **PR Bot — AI 분석 PR comment** — push 스캔 결과를 PR에 자동 코멘트 + AI triage 1-liner

## 🧪 Known Limitations

v0.1.0 시점의 한계와 v0.2(Unreleased)에서 해소된 항목을 함께 기록합니다.

- **SBOM** — ~~v0.1: CycloneDX-lite stub~~ → **v0.2**: 5종 ecosystem 실 파서 + Reports UI + PR diff → **v0.3**: 표준 CycloneDX 1.5 (REPOSITORY 자산은 default branch에서 의존성 자동 추출해 `components[]` 채움, findings → 표준 `vulnerabilities[]`)
- **스캐너** — ~~v0.1: 동기 인라인 실행~~ → **v0.2 해소**: Celery 큐 옵션 (`SCAN_QUEUE_ENABLED`)
- **AI Insights** — ~~v0.1: RAG 미적용~~ → **v0.2 해소**: 4 소스 RAG + inline citation. hallucination 위험 인지·인간 검토 권장은 유지. AI 생성 카드는 ADMIN 전용
- **IAM 어댑터** — ~~v0.1: GCP/Azure 보강 중~~ → **v0.2 해소**: 5종 모두 멱등성 + etag 재시도. capability API는 `ready`/`coming_soon`/`demo`를 그대로 노출
- **테스트 커버리지** — 의도적으로 낮음 (MVP). 기여 환영
- **정책 템플릿의 규제 매핑** — 참고용 출발점이며 법적 자문이 아닙니다

---

## 🤝 Contributing

[CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 새 스캐너 어댑터, AI 프롬프트 개선, 정책 셋 추가 PR을 환영합니다.

---

## 📄 License

MIT — [LICENSE](LICENSE)

---

## 🧭 문서 한눈에 · Doc Map

문서 어디서든 다른 곳으로 한 번에 — 처음이라면 **Setup → Part 0** 부터.

| 문서 | 위치 | 무엇 |
|---|---|---|
| 🏠 **메인 README** (이 문서) | [`/README.md`](README.md) | 프로젝트 소개 · 스크린샷 · 빠른 시작 |
| 🌙 **About** | [`docs/ABOUT.md`](docs/ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ **Setup** | [`docs/SETUP.md`](docs/SETUP.md) | 설치 · 운영 · **[Part 0 — 시나리오 선택](docs/SETUP.md#part-0--어느-시나리오인가요)** |
| 🏗️ **Architecture** | [`docs/development/architecture.md`](docs/development/architecture.md) | 시스템 구조 · 모듈 · 데이터 흐름 |
| 🎨 **Brand Guidelines** | [`docs/assets/brand-guidelines.md`](docs/assets/brand-guidelines.md) | 로고 · 컬러 · 타이포 |
| 🤝 **Contributing** | [`CONTRIBUTING.md`](CONTRIBUTING.md) | 기여 가이드 · PR 규칙 |
| 🔐 **Security Policy** | [`SECURITY.md`](SECURITY.md) | 취약점 신고 절차 |
| 📜 **Code of Conduct** | [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | 커뮤니티 규범 |
| 📋 **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) | 버전별 변경 내역 |
| ✅ **Pre-release Checklist** | [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) | 릴리즈 전 점검 항목 |
| 📦 **Helm Chart** | [`charts/mond/`](charts/mond) | `values.yaml` · `values-prod.yaml` |
| 🐳 **Docker Compose** | [`docker-compose.yml`](docker-compose.yml) | 로컬 데모용 |
| ⚙️ **환경 변수 예시** | [`.env.example`](.env.example) | 모든 ENV 키 + 주석 |

### 시나리오별 빠른 진입

- 🐳 **A. 개인·평가** → [SETUP Part 1 (Docker 30초)](docs/SETUP.md#part-1-docker-compose로-30초-데모)
- 🏢 **B. 사내 데모** → [SETUP Part 1](docs/SETUP.md#part-1-docker-compose로-30초-데모) + [Part 4 (Dev+MFA)](docs/SETUP.md#part-4-로그인--dev--sso--mfa) + [Part 5](docs/SETUP.md#part-5-관리자-초기-세팅-체크리스트)
- 🚀 **C. 운영 (스타트업)** → [SETUP Part 2 (Helm)](docs/SETUP.md#part-2-helm-chart로-kubernetes-운영-배포) + [Part 3 (Anthropic)](docs/SETUP.md#part-3-ai-provider-세팅) + [Part 4 (SSO+MFA)](docs/SETUP.md#part-4-로그인--dev--sso--mfa) + [Part 6 (운영)](docs/SETUP.md#part-6-업그레이드--백업--모니터링)
- 🔒 **D. 폐쇄망 (대기업/공공/금융)** → [Part 2-C 시크릿(Sealed)](docs/SETUP.md#2-c-시크릿-관리-선택--kubectl--external-secrets--sealed-secrets) + [Part 3 (Ollama)](docs/SETUP.md#part-3-ai-provider-세팅) + [Part 4 (Keycloak+MFA)](docs/SETUP.md#part-4-로그인--dev--sso--mfa) + [Part 6 (백업)](docs/SETUP.md#part-6-업그레이드--백업--모니터링)

---

<div align="center">

**🌙 Illuminating the path to secure DevOps**

</div>
