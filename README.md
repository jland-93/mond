# 🌙 Mond

<div align="center">
  <img src="docs/assets/images/mond-logo.png" alt="Mond Logo" width="280"/>
</div>

> **AI-Powered Self-Service DevSecOps Platform** — 자산 인벤토리부터 스캔, 트리아지까지 한 곳에서.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Claude](https://img.shields.io/badge/AI-Claude-7c8cff.svg)](https://www.anthropic.com/)

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
| **Findings** | 발견사항 조회/상태 변경 + AI Triage 드로어 |
| **Policies** | SAST / SCA / IaC / DAST / Container / Secrets / Compliance 룰셋 |
| **Policy Simulation** | "이번 PR에 이 finding이 들어가면 어떤 정책이 깨질까" 미리보기 |
| **AI Insights** | 자연어 쿼리, intent 분류, Claude 답변 |
| **Regulations Guide** | 사업 시나리오 → 적용 규제(K-PIPA·GDPR·HIPAA·PCI-DSS·…) + 시점·의무 |
| **Reports** | 자산별 SBOM(CycloneDX-lite) + 시나리오별 컴플라이언스 리포트 (JSON / Markdown) |
| **Integrations** | 스캐너 / AI / **MCP (stdio+HTTP)** / 알림 채널 / GitHub Webhook 안내 |
| **Settings** | 헬스 / 버전 / 환경 / 언어 |

### 한국어 기본 · 영어 보조 (i18n)

UI는 한국어를 기본으로 표시하며, 우측 상단 토글로 영어로 전환할 수 있습니다.
`DEFAULT_LOCALE=ko|en`로 초기값을 바꿀 수 있고, 선택은 브라우저 localStorage에 지속됩니다.

### 셀프서비스 자동화

| 기능 | 방식 |
|---|---|
| **자동 스캔 (GitHub push)** | `POST /api/v1/webhooks/github` → 매칭 레포 자산 자동 trivy 스캔 |
| **Slack/Generic 알림** | 임계치 이상 finding을 ENV의 Webhook URL로 자동 전송 |
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
- (선택) `ANTHROPIC_API_KEY` — 없어도 휴리스틱 모드로 모든 화면이 동작합니다.

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

---

## 🤖 AI 동작 방식

API 키가 없으면 **휴리스틱 fallback**이 동작하므로 OSS 사용자가 처음부터 UI를 둘러볼 수 있습니다. 키를 설정하면:

| 동작 | 모델 | 트리거 |
|---|---|---|
| **Finding 트리아지** | `claude-haiku-4-5-20251001` (기본) | UI에서 "Run AI Triage" 클릭 |
| **심층 분석** | `claude-sonnet-4-6` | `?deep=true` 쿼리 |
| **자연어 쿼리** | `claude-haiku-4-5-20251001` | `/ai/analyze` 호출 |

Claude는 항상 strict JSON으로만 응답하며, 응답 토큰 사용량이 DB에 기록됩니다.

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
- [x] Slack / Generic Webhook 알림
- [x] MCP 서버 (stdio + HTTP/SSE)
- [ ] OPA Rego 정책 평가
- [ ] CI 통합 패키지 (GitHub Actions / GitLab CI)
- [ ] 멀티유저 + RBAC + SSO

---

## 🤝 Contributing

[CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 새 스캐너 어댑터, AI 프롬프트 개선, 정책 셋 추가 PR을 환영합니다.

---

## 📄 License

MIT — [LICENSE](LICENSE)

---

<div align="center">

**🌙 Illuminating the path to secure DevOps**

</div>
