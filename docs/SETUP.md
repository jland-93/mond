# Mond — 설치 · 운영 가이드

데모부터 사내 운영까지. Docker Compose, Helm chart, AI 세팅, SSO + MFA, 관리자 초기 세팅을 한 곳에 모았습니다. 처음 본다면 먼저 [Part 0. 어느 시나리오인가요?](#part-0-어느-시나리오인가요)에서 본인 환경을 고르고, 해당 시나리오 경로만 따라가면 됩니다.

In English — everything you need to go from `docker compose up` to a Helm-deployed production instance with SSO, MFA, your-own-AI-provider, and a clean admin bootstrap. Start at Part 0 to pick your scenario (Demo / Team / Startup / Closed-network), then follow only the steps that apply to you. English snippets in each section.

---

## 📑 목차

- [Part 0. 어느 시나리오인가요?](#part-0-어느-시나리오인가요) — 4가지 페르소나 + 추천 옵션 매트릭스
- [Part 1. Docker Compose로 30초 데모](#part-1-docker-compose로-30초-데모)
- [Part 2. Helm chart로 Kubernetes 운영 배포](#part-2-helm-chart로-kubernetes-운영-배포)
  - 2-A. DB / Redis 선택 — in-cluster vs 외부 매니지드
  - 2-B. Ingress 선택 — ALB / Nginx / Cloudflare / 사내 GW
  - 2-C. 시크릿 관리 선택 — kubectl / External-Secrets / Sealed-Secrets
- [Part 3. AI provider 세팅 (Anthropic · OpenAI · Bedrock · Ollama · vLLM)](#part-3-ai-provider-세팅) — 5종 선택 기준 + 한국어 성능 비고 + 토큰 사용량 추적
- [Part 4. 로그인 — Dev / SSO / MFA](#part-4-로그인--dev--sso--mfa) — SSO IdP 선택 기준 + MFA 환경별 권장
- [Part 5. 관리자 초기 세팅 10단계 체크리스트](#part-5-관리자-초기-세팅-체크리스트) — 각 단계 "옵션 A/B/Skip" 명시
- [Part 6. 업그레이드 · 백업 · 모니터링](#part-6-업그레이드--백업--모니터링)
- [Part 7. 트러블슈팅](#part-7-트러블슈팅)

---

## Part 0. 어느 시나리오인가요?

EN — Pick your scenario first; only the matching column applies. Don't read every option; read the one that matches your environment.

본인 환경에 가까운 컬럼만 보세요. 다른 컬럼의 설정은 무시해도 됩니다.

| 항목 | **A. 개인·평가** | **B. 사내 소규모 데모** | **C. 운영 (스타트업)** | **D. 운영 (대기업/공공/금융 · 폐쇄망)** |
|---|---|---|---|---|
| 사용자 수 | 1 | 5–20 | 20–200 | 100+ |
| 배포 | 노트북 Docker | 단일 VM Docker | EKS/GKE/AKS Helm | 사내 K8s + 폐쇄망 |
| 데이터 | 시드 사용 | 시드 + 일부 실 자산 | 실 자산만 (`SEED_ON_STARTUP=false`) | 실 자산만 + DB 암호화 |
| DB / Redis | in-cluster | in-cluster | **외부 RDS / ElastiCache** | 사내 PG / Redis 클러스터 |
| AI provider | **없음 → 휴리스틱** | Anthropic 직접 | Anthropic / Bedrock | **Ollama 로컬 LLM** — 외부 호출 금지 |
| 인증 | Dev login | Dev login + MFA | Google SSO + MFA | Keycloak SSO + MFA(패스키 필수) |
| HTTPS | 불필요 | 선택 | **필수** | **필수** (사내 CA) |
| 시크릿 | `.env` 파일 | `.env` + chmod 600 | **External-Secrets + AWS SM** | Sealed-Secrets / Vault |
| 스캐너 | stub 모드 | Trivy만 | Trivy + Semgrep | Trivy + Semgrep + Nuclei (offline DB) |
| Ingress | 불필요 | reverse proxy (caddy/nginx) | ALB / GKE Ingress / AGIC | 사내 L7 GW (nginx/HAProxy) |
| 백업 | 불필요 | DB 수동 `pg_dump` | RDS 자동 백업 | 사내 백업 정책 |
| 모니터링 | docker logs | `docker compose logs` | Prometheus + Grafana | 사내 관측 스택 (LGTM 등) |
| **읽어야 할 파트** | **Part 1 → Part 4 (Dev) → Part 5 (1~2단계만)** | **Part 1 → Part 4 (Dev+MFA) → Part 5** | **Part 2 → Part 3(Anthropic) → Part 4(SSO+MFA) → Part 5 → Part 6** | **Part 2 → Part 3(Ollama) → Part 4(Keycloak+MFA) → Part 5 → Part 6** |

> 참고 — **시나리오를 모르겠으면** → 일단 **A**로 시작. `docker compose up` 한 줄로 띄워보고 화면을 만져본 뒤, 사내 도입 결정이 나면 B → C/D로 이동하면 됩니다. 데이터는 ENV만 바꾸면 흐름 유지.

---

---

## Part 1. Docker Compose로 30초 데모

> **EN**: Fastest way to try Mond. Spins up Postgres + Redis + backend + frontend with seeded demo assets.

### 1-1. 사전 요구사항

- Docker Engine 24+ / Docker Compose v2
- 8GB+ RAM 권장
- (선택) `ANTHROPIC_API_KEY` — 없어도 모든 화면이 **기본 규칙 모드**로 동작합니다

### 1-2. 띄우기

```bash
git clone https://github.com/jland-93/mond.git
cd mond
cp .env.example .env

# (선택) AI 키 넣기 — 비우면 휴리스틱 모드
# echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

docker compose up -d
```

| 서비스 | URL | 비고 |
|---|---|---|
| 프론트엔드 | <http://localhost:3000> | React + Vite |
| 백엔드 API | <http://localhost:8000> | FastAPI |
| API docs (Swagger) | <http://localhost:8000/docs> | OpenAPI 3.1 |
| Redoc | <http://localhost:8000/redoc> | |
| MCP HTTP (stdio도 가능) | <http://localhost:8000/mcp> | Claude Desktop/Code 연결용 |

첫 부팅 시 **데모 자산 3개 + 정책 3개**가 자동 시드됩니다 (`SEED_ON_STARTUP=true` 기본).

### 1-3. 멈추기 / 정리

```bash
docker compose down                  # 컨테이너만 정리
docker compose down -v               # 볼륨까지 (DB 초기화)
```

---

## Part 2. Helm chart로 Kubernetes 운영 배포

> **EN**: For production: deploy via the OCI Helm chart at `oci://ghcr.io/jland-93/charts/mond`. The chart is provider-neutral — works on EKS, GKE, AKS, on-prem.

### 2-1. 차트 구조

`charts/mond/`:

- `Chart.yaml` — `appVersion=0.1.0`, dependencies는 Bitnami postgresql / redis (조건부)
- `values.yaml` — 기본 dev 프로파일 (in-cluster Postgres/Redis)
- `values-prod.yaml` — 운영 프로파일 (외부 RDS/ElastiCache + Ingress)

### 2-2. 운영 배포 단계 (EKS 예시)

#### Step 1 — 네임스페이스 + 시크릿

```bash
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
```

운영에서는 **External-Secrets Operator + AWS Secrets Manager**(또는 GCP Secret Manager / Azure Key Vault)로 동기화하는 것을 권장합니다.

#### Step 2 — Helm 설치

```bash
helm install mond oci://ghcr.io/jland-93/charts/mond \
  --version 0.1.0 \
  -n mond \
  -f charts/mond/values-prod.yaml \
  --set ingress.hosts[0].host=mond.your-corp.com \
  --set secrets.existingSecret=mond-secrets
```

#### Step 3 — 검증

```bash
kubectl -n mond get pods
kubectl -n mond logs deploy/mond-backend --tail 50 | grep "Started"
kubectl -n mond port-forward svc/mond-frontend 3000:80
```

### 2-3. 클라우드별 권장 설정

| 항목 | EKS (AWS) | GKE (GCP) | AKS (Azure) |
|---|---|---|---|
| 이미지 | `ghcr.io/jland-93/mond-backend:<ver>` (multi-arch) | 동일 | 동일 |
| DB | RDS Postgres 16 | Cloud SQL Postgres 16 | Azure DB for Postgres |
| 캐시 | ElastiCache Redis | Memorystore Redis | Azure Cache for Redis |
| Ingress | AWS Load Balancer Controller (`ingressClassName: alb` + ACM) | GCE Ingress + ManagedCertificate | Application Gateway Ingress |
| 시크릿 | External-Secrets → AWS Secrets Manager | External-Secrets → GCP Secret Manager | External-Secrets → Key Vault |
| 권한 | IRSA — `serviceAccount.annotations`에 IAM Role ARN | Workload Identity | Pod Identity |
| 관측 | Prometheus scrape — backend `:8000/metrics` | 동일 | 동일 |

### 2-A. DB / Redis 선택 — in-cluster vs 외부 매니지드

| 선택지 | 언제 쓰나 | 장점 | 단점 | 시나리오 |
|---|---|---|---|---|
| **in-cluster** (`postgresql.enabled=true`, `redis.enabled=true`) | 데모·평가·소규모 사내 | 한 줄 설치, 추가 비용 없음 | **백업/HA는 본인이 알아서**, PVC 분실 위험 | A · B |
| **외부 매니지드** (RDS/Cloud SQL/Azure DB + ElastiCache/Memorystore) | 운영 — 사용자 5명 이상 | 자동 백업, HA, PIT recovery, 별도 SLA | 월 비용 (Postgres 16 + Redis 7 합쳐 $30~) | C |
| **사내 PG/Redis 클러스터** | 폐쇄망·금융·공공 | 데이터 외부 미반출 | 운영 책임 본인 | D |

#### 외부 매니지드 사용 예시 (`values-prod.yaml`)

```yaml
postgresql:
  enabled: false  # in-cluster 끄기

redis:
  enabled: false

secrets:
  databaseUrl: postgresql+asyncpg://user:pwd@rds.../mond
  redisUrl: redis://elasticache.../0
```

> 주의 — in-cluster Postgres의 PVC는 **노드 사라지면 데이터도 사라질 수 있음**. 운영 전엔 반드시 외부 매니지드 또는 PV backup 정책 적용. 백업 가이드 → [Part 6-B 백업 전략](#part-6-업그레이드--백업--모니터링)

### 2-B. Ingress 선택 — ALB / Nginx / Cloudflare / 사내 GW

| 선택지 | 언제 쓰나 | 설정 | 비고 |
|---|---|---|---|
| **AWS ALB** | EKS | `ingressClassName: alb` + ACM cert ARN annotation | TLS 자동, IRSA로 권한 부여 |
| **GCE Ingress** | GKE | `kubernetes.io/ingress.class: gce` + ManagedCertificate | Google 관리 cert |
| **AGIC** | AKS | `kubernetes.io/ingress.class: azure/application-gateway` | Application Gateway |
| **Nginx Ingress** | 어디서나 | `ingressClassName: nginx` | Helm chart 별도 설치 필요 |
| **Cloudflare Tunnel** | 외부 IP 없을 때 | Tunnel + Origin Rule + WAF 무료 | Cloudflare 계정 필요 |
| **사내 GW (nginx/HAProxy/F5)** | 폐쇄망 | Service `type: ClusterIP` + 사내 L7에서 reverse proxy | TLS는 GW에서 |
| **Ingress 없음** | 단일 노드 데모 | `kubectl port-forward` | 임시용만 |

#### Ingress + TLS 예시 (`values-prod.yaml`)

```yaml
ingress:
  enabled: true
  className: "alb"          # 또는 nginx / "" (기본)
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
  hosts:
    - host: mond.your-corp.com
      paths:
        - { path: /,    pathType: Prefix, service: frontend }
        - { path: /api, pathType: Prefix, service: backend  }
        - { path: /mcp, pathType: Prefix, service: backend  }
  tls:
    - hosts: ["mond.your-corp.com"]
      secretName: mond-tls  # cert-manager 또는 별도 import
```

> 운영 도메인은 **반드시 HTTPS** — `SESSION_SECURE=true`와 `SameSite=Lax` 쿠키가 정상 작동하려면 TLS 필수. HTTP면 패스키도 막힙니다.

### 2-C. 시크릿 관리 선택 — kubectl / External-Secrets / Sealed-Secrets

| 선택지 | 보안 등급 | 운영 비용 | 언제 쓰나 |
|---|---|---|---|
| **`kubectl create secret`** (직접) | 낮음 | 0 | 데모 · 1회성 |
| **External-Secrets Operator + AWS Secrets Manager / GCP SM / Vault** (권장) | 높음 | ESO 설치 비용 | 운영 권장 (C) |
| **Sealed-Secrets (bitnami-labs)** | 중간 | controller 1개 | 폐쇄망 GitOps (D) |
| **External-Secrets + HashiCorp Vault** | 높음 | Vault 클러스터 | 다중 클라우드 |
| **SOPS + age + Helm secrets** | 중간 | git-crypt 워크플로 | GitOps + 소규모 |

#### A안 — kubectl 직접 (데모)

```bash
kubectl -n mond create secret generic mond-secrets \
  --from-literal=SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:pwd@rds.../mond" \
  --from-literal=REDIS_URL="redis://elasticache.../0"
```

#### B안 — External-Secrets + AWS Secrets Manager (운영 권장 (권장))

```yaml
# 1) AWS Secrets Manager에 secret 생성
#    aws secretsmanager create-secret --name prod/mond \
#      --secret-string file://secrets.json

# 2) ClusterSecretStore (1회)
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata: { name: aws-sm }
spec:
  provider:
    aws:
      service: SecretsManager
      region: ap-northeast-2
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets

# 3) ExternalSecret — Mond용
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: mond-secrets, namespace: mond }
spec:
  secretStoreRef: { name: aws-sm, kind: ClusterSecretStore }
  target: { name: mond-secrets }
  data:
    - { secretKey: SECRET_KEY,        remoteRef: { key: prod/mond, property: SECRET_KEY } }
    - { secretKey: ANTHROPIC_API_KEY, remoteRef: { key: prod/mond, property: ANTHROPIC_API_KEY } }
    - { secretKey: DATABASE_URL,      remoteRef: { key: prod/mond, property: DATABASE_URL } }
    # ... 나머지 키
```

#### C안 — Sealed-Secrets (폐쇄망 GitOps)

```bash
# 1) controller 설치 (1회)
helm install sealed-secrets sealed-secrets-controller/sealed-secrets -n kube-system

# 2) 평문 secret 생성 후 봉인
kubectl -n mond create secret generic mond-secrets \
  --from-literal=SECRET_KEY=... --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-mond-secrets.yaml

# 3) git push — 평문이 아니므로 안전
git add sealed-mond-secrets.yaml && git commit -m "secrets: mond v0.1.0"
```

### 2-D. 운영 부팅 가드

`ENVIRONMENT=production`일 때 백엔드는 **약한 설정 조합을 부팅 단계에서 거부**합니다:

- `SECRET_KEY` 가 32자 미만이거나 기본값
- `DEBUG=true`
- `AUTH_MODE=dev`
- `SESSION_SECURE=false`

→ 운영에선 다음 조합 필수:

```bash
ENVIRONMENT=production
SECRET_KEY=<48+ random>
DEBUG=false
AUTH_MODE=sso
SESSION_SECURE=true
```

---

## Part 3. AI provider 세팅

> **EN**: Mond abstracts AI providers. Switch with one ENV. No key → heuristic mode → UI still works. Pick the row that matches your environment.

### 3-0. 어떤 provider를 골라야 하나요? — 선택 기준

본인 환경에 가까운 항목만 보면 됩니다.

| 본인 환경 | 추천 provider | 이유 |
|---|---|---|
| 평가 / 데모 / 키 없음 | **(없음 → 휴리스틱)** | UI는 정상 동작, AI는 규칙 기반 fallback |
| 가장 빠르게 좋은 결과 | **Anthropic 직접** (권장) | 한국어 reasoning 강함, prompt 호환성 100% (Mond는 Claude로 최적화됨) |
| 회사가 OpenAI/Azure 계약 보유 | **OpenAI** | 결제·거버넌스 통합. `gpt-4o-mini`로 비용 절감 |
| AWS 단독 사용 + IAM 통합 비용 정책 | **AWS Bedrock** | IRSA로 API key 관리 불요, 결제 통합 |
| **폐쇄망 / 금융 / 공공 / 의료** — 데이터 외부 유출 금지 | **Ollama** (로컬 LLM) | 모든 추론이 사내 GPU에서. 외부 API 호출 0 |
| 다국적 — 미국·EU 데이터 거주성 강제 | Bedrock (region 선택) 또는 Azure OpenAI | 데이터 리전 명시적 |

> 참고 — **헷갈리면** → 일단 Anthropic으로 시작. 나중에 ENV 한 줄만 바꾸면 다른 provider로 즉시 전환 가능 (대화 기록·자산 데이터는 그대로).

### 3-1. provider 매트릭스 — 한눈에

| Provider | ENV | 모델 예시 | 시나리오 | 한국어 |
|---|---|---|---|---|
| **(없음)** | (env 미설정) | — | A | 휴리스틱 KO |
| **Anthropic 직접** (권장) | `AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` · `claude-sonnet-4-6` | B / C | ★★★★★ |
| **OpenAI / Azure OpenAI** | `AI_PROVIDER=openai` + `OPENAI_API_KEY` (+`OPENAI_BASE_URL` for Azure) | `gpt-4o-mini` · `gpt-4o` | C | ★★★★☆ |
| **AWS Bedrock** | `AI_PROVIDER=bedrock` + IAM 자격 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | C (AWS heavy) | ★★★★★ |
| **Ollama (로컬)** | `AI_PROVIDER=ollama` + `OLLAMA_BASE_URL` | `llama3.1:8b` · `llama3.1:70b` · `qwen2.5:32b` | **D (폐쇄망)** | ★★★☆☆ (모델 따라) |
| **vLLM (사내 GPU)** | `AI_PROVIDER=vllm` + `VLLM_BASE_URL` (OpenAI 호환) | `meta-llama/Meta-Llama-3.1-70B-Instruct` 등 vLLM 서버에 띄운 모델 | **D (폐쇄망 + 고처리량)** | 모델 따라 |

### 3-2. 설정 예시

#### Anthropic (기본)

```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
AI_MODEL_DEFAULT=claude-haiku-4-5-20251001
AI_MODEL_DEEP=claude-sonnet-4-6
AI_MAX_TOKENS=2048
```

#### OpenAI (또는 Azure OpenAI)

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
# Azure 사용 시:
# OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/<deployment>
OPENAI_MODEL_DEFAULT=gpt-4o-mini
OPENAI_MODEL_DEEP=gpt-4o
```

#### AWS Bedrock (IRSA / IAM Role)

```bash
AI_PROVIDER=bedrock
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_DEFAULT=anthropic.claude-3-5-haiku-20241022-v1:0
BEDROCK_MODEL_DEEP=anthropic.claude-3-5-sonnet-20241022-v2:0
# AWS 자격은 ENV/IAM Role 둘 다 OK
```

#### Ollama (폐쇄망 / 로컬)

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama.internal:11434
OLLAMA_MODEL_DEFAULT=llama3.1:8b
OLLAMA_MODEL_DEEP=llama3.1:70b
```

#### vLLM (사내 GPU 게이트웨이 — OpenAI 호환)

사내 GPU 서버에 vLLM을 OpenAI 호환 모드로 띄운 환경. Ollama보다 처리량/배치 효율이 높고, 같은 OpenAI SDK 호출 경로를 그대로 재사용한다.

```bash
# vllm serve meta-llama/Meta-Llama-3.1-70B-Instruct \
#   --host 0.0.0.0 --port 8000 --tensor-parallel-size 4

AI_PROVIDER=vllm
VLLM_BASE_URL=http://gpu-01.internal:8000/v1
VLLM_API_KEY=EMPTY        # vLLM은 인증 미요구. openai SDK placeholder.
VLLM_MODEL_DEFAULT=meta-llama/Meta-Llama-3.1-8B-Instruct
VLLM_MODEL_DEEP=meta-llama/Meta-Llama-3.1-70B-Instruct
```

> 폐쇄망에 vLLM/Ollama를 동시에 두는 패턴도 가능합니다. UI Admin → 연동 관리에서 default provider만 토글하세요.

### 3-3. 토큰 사용량 추적

모든 `complete_json` 호출은 `ai_usage_logs` 테이블에 provider · model tier · intent · 입출력 토큰을 기록합니다. Admin → 연동 관리에 `AI 토큰 사용량` 카드가 최근 1/7/30/90일 호출수, 입출력 토큰 합, provider/tier/intent 분포를 보여줍니다.

```http
GET /api/v1/admin/ai-providers/usage?days=7
```

응답 JSON: `total` (호출수·입·출·실패) · `by_provider` · `by_tier` (default/deep) · `by_intent` (상위 20) · `by_day` 시계열.

### 3-4. 키 없을 때 (Heuristic 모드)

- 화면 상단에 `ANTHROPIC_API_KEY 미설정 — 기본 규칙 모드` 안내
- AI Insights / Findings 트리아지는 **휴리스틱 규칙**으로 동작 (severity 매핑·키워드 기반)
- 사용감을 정확히 확인할 수 있음 → 의사결정 후 키 추가 ✅

### 3-5. 응답 출처 추적

모든 AI 응답에는 `{provider}:{model}` 라벨이 함께 저장되어 감사 가능합니다:

```json
{
  "summary": "...",
  "model": "anthropic:claude-haiku-4-5-20251001",
  "input_tokens": 532,
  "output_tokens": 248
}
```

---

## Part 4. 로그인 — Dev / SSO / MFA

> **EN**: Three layers — auth mode, SSO IdP, MFA factor. Pick one row in each table.

### 4-0. 어떤 IdP를 골라야 하나요? — 선택 기준

| 본인 환경 | 추천 IdP | 이유 |
|---|---|---|
| 평가 / 데모 / 사용자 1명 | **Dev login** | 이메일만 입력 — SSO 설정 불필요 |
| 사내 Google Workspace 사용 | **Google SSO** | 가장 빠른 SSO 도입 (3 클릭) |
| 사내 IdP 자체 호스팅 — 오픈소스 | **Keycloak** (권장) | 무료, Realm·정책 자유. 폐쇄망 가능 |
| 회사가 Okta 계약 보유 | **Okta** | 기존 user 정책·MFA 정책 그대로 |
| 다중 IdP — 임직원 Okta + 외주 Google | (혼합) `SSO_PROVIDERS=okta,google` | 두 버튼 동시 노출 |
| 폐쇄망 + AD 도메인 | **Keycloak** + LDAP federation | Keycloak이 AD bridge 역할 |

### 4-1. 인증 모드 매트릭스

| 모드 | `AUTH_MODE` | 용도 | SSO 필요 | 시나리오 |
|---|---|---|---|---|
| **Dev login** | `dev` | 데모 · 로컬 개발 · CI | ❌ — 이메일만 입력 | A · B |
| **SSO 전용** | `sso` | 운영 — OIDC 강제 | ✅ — Keycloak / Okta / Google | C · D |

> 주의 — 운영(`ENVIRONMENT=production`)에서 `AUTH_MODE=dev`는 부팅 거부됨. 이메일만 입력해서 누구나 admin 잠탈 가능하므로 운영에선 반드시 SSO.

### 4-2. Dev Login (데모용)

`.env`:

```bash
AUTH_MODE=dev
# SSO env들은 모두 비워두면 됨
```

`/login` 화면에서 이메일만 입력 → 즉시 로그인. **첫 가입자가 자동으로 ADMIN**.

### 4-3. SSO 설정 — Keycloak 예시

#### Keycloak 측

1. Realm 생성 (예: `mond`)
2. Client 생성:
   - Client ID: `mond`
   - Client Authentication: ON (confidential)
   - Valid Redirect URIs: `https://mond.your-corp.com/api/v1/auth/callback/keycloak`
3. Client → Credentials → Secret 복사

#### Mond 측 `.env`

```bash
AUTH_MODE=sso
SSO_PROVIDERS=keycloak

SSO_KEYCLOAK_ISSUER=https://keycloak.your-corp.com/realms/mond
SSO_KEYCLOAK_CLIENT_ID=mond
SSO_KEYCLOAK_CLIENT_SECRET=<from-keycloak>

SSO_REDIRECT_BASE=https://mond.your-corp.com
SSO_ADMIN_EMAILS=admin@your-corp.com,security-lead@your-corp.com
```

### 4-4. SSO — Okta · Google

복수 provider 지정 가능 (콤마):

```bash
SSO_PROVIDERS=keycloak,okta,google

SSO_OKTA_ISSUER=https://your-org.okta.com/oauth2/default
SSO_OKTA_CLIENT_ID=...
SSO_OKTA_CLIENT_SECRET=...

SSO_GOOGLE_CLIENT_ID=...apps.googleusercontent.com
SSO_GOOGLE_CLIENT_SECRET=...
```

→ `/login` 화면에 활성 provider별 버튼이 자동 노출됩니다.

### 4-5. MFA 강제 정책

기본: **ADMIN + Reviewer는 MFA 강제**. 1차 SSO/이메일 인증 직후 `/mfa`로 이동.

| 환경 | 등록 가능 수단 |
|---|---|
| `http://localhost:3000` | 패스키(WebAuthn) + TOTP 둘 다 가능 |
| 사내 IP / HTTP 도메인 (`http://192.168.x.x`) | 패스키 브라우저 정책상 **차단** — **TOTP 사용** (Google Authenticator / 1Password / Authy) |
| HTTPS 운영 도메인 | 둘 다 정상 |

MFA factor: 패스키 · TOTP · **백업 코드(10개, 1회용)**.

#### MFA 완화 (개발/데모만)

```bash
# 아무도 강제 안 함 (옵션)
MFA_REQUIRED_ROLES=

# ADMIN만 빼고 reviewer는 강제
MFA_REQUIRED_ROLES=reviewer
```

**운영에서는 반드시 `admin,reviewer` 이상 유지.**

### 4-6. 잠겼을 때 복구 CLI

비밀번호 매니저 분실 등으로 모든 MFA factor에 접근 불가 시:

```bash
# Docker Compose
docker compose exec backend python -m scripts.admin_unlock admin@your-corp.com --yes

# Kubernetes
kubectl -n mond exec deploy/mond-backend -- python -m scripts.admin_unlock admin@your-corp.com --yes
```

해당 사용자의 모든 MFA factor (패스키·TOTP·백업코드)가 삭제되고 다음 로그인에서 첫 등록 화면이 다시 보입니다. **사용자 데이터·자산·정책은 그대로 유지**.

---

## Part 5. 관리자 초기 세팅 체크리스트

> **EN**: First-time admin bootstrap. Walk through this list right after `docker compose up` or Helm install. Each step shows an **🅰️ option / 🅱️ option / ⏭️ skip** when applicable.

처음 띄운 뒤 ADMIN이 30분 안에 끝낼 수 있는 흐름. **각 단계마다 본인 시나리오에 맞춰 선택지를 골라 진행하세요.**

### 1) 첫 로그인 + MFA 등록

- `/login` 이메일 입력 → 첫 가입자 자동 ADMIN
- `/mfa` 화면에서 패스키 또는 TOTP 등록
- 백업 코드 10개를 **반드시 별도 저장** (비밀번호 매니저 등)

### 2) 추가 관리자 지정 — `SSO_ADMIN_EMAILS`

운영용 `.env` 또는 secret에:

```bash
SSO_ADMIN_EMAILS=admin1@your-corp.com,admin2@your-corp.com
```

해당 이메일로 첫 SSO 로그인 시 자동 ADMIN 부여.

### 3) 사용자 + 역할 (Admin → Users & Roles)

- 4-tier RBAC: `viewer` < `employee` < `reviewer` < `admin`
- 각 역할이 접근 가능한 메뉴:
  - **viewer**: 대시보드 / 자산 / 발견사항 / 정책 / AI 인사이트 / 지식 / 규제 / 리포트 / 보안 / 설정
  - **employee**: + 스캔 / 정책 시뮬 / IAM 탐색 / 권한 요청
  - **reviewer**: + 권한 검토 (Admin Area)
  - **admin**: + Connections / Users & Roles

### 4) IAM Source 연동 (Admin → Connections)

권한 셀프서비스를 쓰려면 클라우드 IAM source 연결:

| Source | 자격 |
|---|---|
| AWS | Access Key + Secret 또는 IRSA (운영 권장) |
| GCP | Service Account JSON |
| Azure | Service Principal (tenant/client/secret) |
| Kubernetes | in-cluster ServiceAccount 또는 kubeconfig |
| LDAP / AD | bind DN + password |

연동 후 IAM Explorer에서 자동 sync 시작.

### 5) 스캐너 바이너리 — 어떤 것부터 설치하나요?

| 스캐너 | 무엇 | 우선순위 | 설치 |
|---|---|---|---|
| **Trivy** (권장) | 컨테이너 이미지 CVE · IaC · SBOM | **1순위** | `brew install trivy` / `apt install trivy` / Docker 이미지에 사전 포함 |
| **Semgrep** | 정적 코드 분석 (SAST) | 2순위 | `pip install semgrep` / `brew install semgrep` |
| **Nuclei** | 템플릿 기반 동적 스캔 (DAST) | 3순위 | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |

****옵션 A** — Docker 이미지에 사전 설치**: backend Dockerfile에 추가 (운영 권장)
****옵션 B** — 사이드카 컨테이너**: K8s에서 별도 pod로 띄우고 `SCANNER_*_BIN` 경로 지정
****옵션 C** — Skip**: 아무 것도 설치 안 함 → stub 모드 (UI는 정상, 결과는 가짜 데이터)

```bash
# .env 경로 지정 — 없으면 stub
SCANNER_TRIVY_BIN=trivy
SCANNER_SEMGREP_BIN=semgrep
SCANNER_NUCLEI_BIN=nuclei
```

> 🔒 폐쇄망(D 시나리오): Trivy는 `--offline-scan` + DB mirror 필요. Trivy DB는 ECR / Harbor 등 사내 registry에서 미러링.

### 6) 정책 시드 — 유지 vs 초기화

| 시드된 정책 3개 | 무엇 | 보통 어떻게 |
|---|---|---|
| `block-critical-cve` | severity=critical 발견 시 빌드 차단 | 그대로 유지 권장 |
| `require-mfa-admin` | admin/reviewer는 MFA 강제 | 그대로 유지 권장 |
| `pii-data-encryption` | PII 다루는 자산은 암호화 라벨 강제 | 한국 PIPA 대응 — 조직 라벨링에 맞춰 조정 |

****옵션 A** — 그대로 시작** (대부분의 경우 권장)
****옵션 B** — 정책 삭제 후 자체 정책 작성** — Policies 화면에서 신규 작성
****옵션 C** — Skip** (`SEED_ON_STARTUP=false`) — 비어있는 상태로 시작

### 7) 알림 — Slack / Discord / Teams / Generic Webhook

| 선택지 | 언제 쓰나 | 설정 |
|---|---|---|
| **Slack Webhook** (권장) | 팀이 Slack 사용 | `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...` |
| **Discord Webhook** | 커뮤니티/스타트업/오픈소스 팀 | `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...` |
| **MS Teams Webhook** | 회사 표준이 Microsoft 365 | `TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...` |
| **Generic Webhook** | PagerDuty · Lark · 자체 incident bot | `GENERIC_WEBHOOK_URL=https://your-bot/mond` (JSON POST) |
| **여러 채널 동시** | 채널별로 다른 청중에게 알림 | 원하는 ENV를 모두 설정. 알림은 모든 채널에 fan-out |
| **알림 끄기** | 데모 · 조용한 환경 | 위 ENV를 모두 비워두기 |

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/.../...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
GENERIC_WEBHOOK_URL=https://your-incident-bot/mond
NOTIFY_MIN_SEVERITY=high   # critical / high / medium / low / info (threshold)
```

> Discord/Teams는 webhook URL만 받으면 즉시 활성화 — 별도 OAuth/앱 등록 불필요.
> severity별 색상(critical=빨강, high=주황, medium=노랑, low=파랑)은 채널별 형식으로 자동 변환.

`NOTIFY_MIN_SEVERITY` 권장:
- 운영 — `high` (default) — critical/high만 알림
- 보안팀 전담 채널 — `medium`
- 데모 — `critical`만

#### 7-0) Slack 연동 페이지 (Admin → Slack 연동)

ENV에 single webhook을 박는 대신 UI에서 purpose별 채널을 등록하고 싶을 때:

1. Slack workspace → Apps → **Incoming Webhooks** → 채널 선택 → URL 복사
2. Mond에서 `Admin → Slack 연동`(`/admin/slack`) 진입
3. 5종 purpose 카드에 webhook URL 등록
   - `default` — purpose가 더 구체적으로 잡히지 않을 때 fallback
   - `digest` — Daily Digest
   - `finding` — severity 임계 이상 신규 발견
   - `access_request` — 권한 요청 / 검토
   - `role_request` — 역할 변경 요청
4. 카드별 `테스트` 버튼으로 실제 메시지 발송 확인

DB에 등록된 채널이 ENV(`SLACK_WEBHOOK_URL` · `DIGEST_SLACK_WEBHOOK_URL`)보다 우선합니다. ENV는 그대로 fallback으로 남아 OSS 초기 설치도 매끄럽게.

<a id="daily-digest"></a>
#### 7-1) Daily Security Digest — 매일 아침 어제 일어난 일 요약

화면 5개 돌아다닐 필요 없이 Slack 카드 한 장으로 어제를 본다.

**ENV:**
```bash
# Daily Digest 전용 채널 (없으면 SLACK_WEBHOOK_URL fallback).
# 보안팀 채널을 finding 알림과 분리하고 싶을 때.
DIGEST_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/.../digest
```

**수동 발송:** Admin → Connections 페이지의 "Daily Security Digest" 카드에서 `지금 전송` 클릭.

**자동 발송 (운영):** 외부 cron이 매일 한 번 다음 endpoint를 호출.
```
POST /api/v1/admin/digest/send
```
인증은 admin webhook token 또는 admin 세션 cookie 필요.

**Kubernetes CronJob 예시 (매일 09:00 KST):**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mond-daily-digest
  namespace: mond
spec:
  schedule: "0 0 * * *"   # 00:00 UTC = 09:00 KST
  timeZone: UTC
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: caller
              image: curlimages/curl:8.10.1
              command:
                - sh
                - -c
                - |
                  curl -fsS -X POST \
                    -H "Authorization: Bearer $MOND_ADMIN_TOKEN" \
                    http://mond-backend.mond.svc.cluster.local:8000/api/v1/admin/digest/send
              env:
                - name: MOND_ADMIN_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: mond-secrets
                      key: ADMIN_DIGEST_TOKEN
```

**미리보기 (Reviewer+):** `GET /api/v1/admin/digest/preview` — 전송 없이 집계와 Slack 메시지 포맷 확인.

### 8) GitHub Webhook 자동 스캔 + SBOM Diff on PR (선택)

```bash
GITHUB_WEBHOOK_SECRET=<random-secret>
# python -c 'import secrets;print(secrets.token_urlsafe(32))'

# PR에 SBOM diff comment를 달려면 추가 (선택):
GITHUB_TOKEN=ghp_xxxx   # PR comment 작성 권한 PAT 또는 App token
```

GitHub repo Settings → Webhooks:
- **Payload URL**: `https://mond.your-corp.com/api/v1/webhooks/github`
- **Content type**: `application/json`
- **Secret**: 위 secret과 동일
- **Events**: `push` + `pull_request` 둘 다 체크

#### 동작
- `push` 이벤트 — 매칭 자산이 있으면 변경 파일 기반으로 **스캐너 자동 선택**. 응답·로그에 `scanner`와 `router_decision`(reason/counts/fallback) 포함
  - **REPOSITORY 자산**: SAST 파일(`.py`/`.go`/`.ts`/`.java`/`.rs`/`.rb`/`.php`/`.cs`/`.c`/`.cpp`...) 비중이 다른 카테고리 합보다 많으면 → **semgrep**. SCA(`package.json`/`requirements.txt`/`go.mod`/`pom.xml`/`Gemfile`/`Cargo.toml`...) · IaC(`.tf`/`.tfvars`/`.hcl`) · Container(`Dockerfile`/`*.dockerfile`) 변경 우세 또는 분류 불가 → **trivy**
  - **CONTAINER_IMAGE 자산** → 항상 trivy
  - **URL 자산** → nuclei (없으면 trivy fallback)
- `pull_request` (opened / synchronize / reopened) — 변경된 의존성 파일(`package.json` / `package-lock.json` / `requirements.txt` / `go.mod` / `Dockerfile`)에서 before/after를 파싱해 **신규 / 제거 / 버전 변경**을 추출. `GITHUB_TOKEN`이 있으면 PR에 comment를 달고, FINDING purpose의 Slack 채널이 설정되어 있으면 Slack에도 알림.

**Skip 옵션**: 수동 스캔으로 충분하면 webhook 없이도 OK.

#### GitHub org 자산 자동 동기화

수십~수백 개 repo를 손으로 자산 등록하는 대신, org 단위로 한 번에 가져온다.

```bash
GITHUB_TOKEN=ghp_xxxx       # 위와 동일하게 재사용
GITHUB_ORG=your-org         # 선택, admin UI에 기본값으로 채워짐
```

Admin → **Connections → GitHub Org Asset Sync** 카드에서:
1. org 또는 user 이름 입력 (`jland-93`, `your-corp` 등)
2. **미리보기**(dry-run)로 등록 예정 목록 확인
3. **동기화** 클릭 → 신규 자산 자동 등록 + 라벨 갱신

동일 URI(`https://github.com/{owner}/{repo}`)는 라벨만 갱신하므로 반복 실행이 안전. `owner`/`environment` 필드는 사용자가 손으로 채운 값 그대로 유지.

API 직접 호출: `POST /api/v1/admin/github-sync/run` body `{"org":"...","dry_run":false,"include_archived":false}`.

### 8-1) 스캔 큐 (Celery) — 운영 안정성

기본은 인라인 동기 실행. 대용량/장시간 스캔에서 backend 타임아웃이 문제라면 비동기 큐로 전환.

```bash
# .env 또는 compose env
SCAN_QUEUE_ENABLED=true
# broker는 REDIS_URL을 기본 사용. 분리하려면:
# CELERY_BROKER_URL=redis://redis:6379/1
```

docker compose:
```bash
docker compose up -d backend worker
# worker 로그
docker compose logs -f worker
```

scan 트리거 시 backend가 즉시 `PENDING` Scan을 반환하고, worker가 `mond.run_scan` task로 실제 스캐너를 실행합니다. 결과는 DB에 기록되고 UI는 status를 폴링.

운영 (Helm) — 별도 Deployment로 worker를 띄우고 `replicaCount`로 동시 처리량 조절. concurrency는 `command: celery -A app.celery_app:celery_app worker --concurrency=N`로 worker 인스턴스 안에서 조절.

### 8-4) OPA Rego 정책 평가

backend Docker 이미지에 OPA v1.x 정적 바이너리(`/usr/local/bin/opa`)가 번들되어 있다. Helm/Compose 둘 다 추가 설치 불필요.

가용성 확인:
```bash
curl -s http://localhost:8000/api/v1/integrations/opa
# {"available": true, "binary": "/usr/local/bin/opa"}
```

#### 정책 만들기 (REVIEWER+)

```http
POST /api/v1/policies
{
  "name": "Block known critical CVE",
  "policy_type": "custom",
  "enabled": true,
  "severity_threshold": "low",
  "engine": "opa",
  "definition": {
    "rego": "package mond\ndeny contains msg if {\n  some f in input.findings\n  f.rule_id == \"CVE-2024-0001\"\n  msg := sprintf(\"blocked %s (%s)\", [f.rule_id, f.severity])\n}\n",
    "query": "data.mond.deny"
  }
}
```

#### 시뮬레이션

`POST /api/v1/policy/simulate` 호출 시 `engine="opa"` 정책은 OPA로 평가되고, 응답 result의 `engine`/`reason`/`matched` 필드에 OPA가 반환한 deny 메시지가 들어간다.

#### 제약

- Rego v1 문법 (OPA v1.0+ 표준). 과거 `import future.keywords.if` 같은 import는 불필요/금지
- 평가 timeout 8초 — 무한 루프/큰 데이터 방지
- input 스키마는 `{"findings": [{"rule_id", "severity", "scanner"}]}` 고정

### 8-3) AI 프롬프트 PII redaction

기본 활성. 사용자 쿼리가 외부 LLM provider로 가기 직전에 PII와 시크릿을 placeholder로 치환한다.

```bash
AI_PROMPT_REDACT_PII=true     # 기본
```

마스킹 대상:

| 종류 | 예 | placeholder |
|------|----|-------------|
| 이메일 | `kim@example.com` | `[REDACTED_EMAIL]` |
| 한국 전화번호 | `010-1234-5678` | `[REDACTED_PHONE]` |
| 국제 전화 | `+82-10-...` | `[REDACTED_PHONE]` |
| 주민등록번호 | `900101-1234567` | `[REDACTED_RRN]` |
| AWS Access Key ID | `AKIA...` | `[REDACTED_AWS_KEY]` |
| AWS Secret (40-char) | base64 패턴 | `[REDACTED_AWS_SECRET]` |
| GitHub token | `ghp_...` | `[REDACTED_TOKEN]` |
| 일반 API token | `sk-...` / `pat_...` | `[REDACTED_TOKEN]` |
| JWT | `eyJ...` | `[REDACTED_JWT]` |
| 신용카드 (Luhn 통과) | `4111 1111 ...` | `[REDACTED_CC]` |

RAG retrieve는 원본 쿼리로 진행하고, LLM에 보내는 user message만 마스킹본을 사용. AI Insights 응답의 `redactions` 필드(`{kind: count}`)와 UI의 `redacted email:1` chip으로 무엇이 가려졌는지 즉시 확인.

### 8-2) Rate limit (abuse 보호)

기본 활성. Redis 기반 fixed-window counter로 OSS 공개 인스턴스의 brute-force/스크래핑을 막는다.

```bash
RATE_LIMIT_ENABLED=true     # 기본. false로 끄면 모든 버킷 통과 (test/CI 편의)
```

기본 한도(분당):

| 버킷 | 한도 | scope | 대상 |
|------|------|-------|------|
| `login` | 10 | IP | `POST /auth/dev-login` |
| `ai_analyze` | 20 | user | `POST /ai/analyze` |
| `webhook_github` | 120 | IP | `POST /webhooks/github` |
| `webhook_personal` | 30 | IP | `POST /webhooks/personal` |
| `github_sync` | 5 | user | `POST /admin/github-sync/run` |

응답 헤더 — `X-RateLimit-Limit` / `X-RateLimit-Remaining` / `X-RateLimit-Reset`. 초과 시 HTTP 429 + `Retry-After`.

Redis 다운 시 fail open(가용성 우선) — `rate_limit_redis_down` 경고 로그를 남기고 요청은 통과. 보안 critical 환경이면 monitor에서 이 로그를 알림으로 연결할 것.

### 9) 데모 시드 끄기

```bash
SEED_ON_STARTUP=true    # A · B (데모): 첫 부팅 시 자산 3 + 정책 3 자동 추가
SEED_ON_STARTUP=false   # C · D (운영 권장): 빈 상태로 시작
```

**이미 띄운 후 끄려면**: DB에서 시드 자산 (`source=seed`)을 삭제하고 ENV 변경 후 재시작.

### 10) Locale 기본값 — KO / EN

```bash
DEFAULT_LOCALE=ko   # 기본 (한국 조직)
DEFAULT_LOCALE=en   # 글로벌 팀
```

각 사용자는 우상단 언어 스위처로 개별 선택 가능 — `DEFAULT_LOCALE`은 미설정 사용자의 첫 화면 언어만 결정.

### 11) MCP 서버 활성화 (선택) — Claude Desktop / Code 연동

Mond를 외부 AI 에이전트의 도구로 노출. 두 전송 방식 중 하나 선택.

#### A) HTTP — 원격 클라이언트 (권장)

```bash
MCP_HTTP_ENABLED=true
# 운영에선 반드시 Bearer 토큰을 설정. 비어 있으면 anonymous 허용 + 경고 로그.
# python -c 'import secrets; print(secrets.token_urlsafe(32))'
MCP_HTTP_AUTH_TOKEN=<32바이트 secret>
```

상태 확인 — `GET /api/v1/integrations/mcp/health` (인증 불필요):

```json
{
  "enabled": true,
  "mounted": true,
  "transport": "streamable_http_app",
  "auth_required": true,
  "reason": null,
  "url": "/mcp"
}
```

Claude Desktop `claude_desktop_config.json` (또는 Claude Code `~/.claude/config.json`):

```json
{
  "mcpServers": {
    "mond": {
      "url": "https://mond.your-corp.com/mcp/",
      "headers": { "Authorization": "Bearer <위에서 만든 토큰>" }
    }
  }
}
```

> URL 끝에 trailing slash(`/`)를 유지하세요. `/mcp`로 보내면 307 redirect → `/mcp/`로 follow됩니다.

#### B) stdio — 로컬 단일 사용자

```jsonc
{
  "mcpServers": {
    "mond": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/mond/backend"
    }
  }
}
```

#### 노출되는 tools (v0.3 기준)

| Tool | 설명 |
|---|---|
| `list_assets` / `get_asset` | Mond 자산 검색 / 조회 |
| `list_findings` | severity · asset_id · scanner 필터 |
| `trigger_scan` | 자산에 대해 trivy/semgrep/nuclei 스캔 실행 |
| `triage_finding` | finding 1건을 Claude로 severity 재평가 + remediation 제안 |
| `list_scanners_tool` | 등록된 스캐너 어댑터 목록 |
| `ask` | 자연어를 의도(scan/list_findings/explain/unknown)로 분류 |
| `regulations_for` / `regulation_detail` | 시나리오/규제 조회 (ISMS-P · GDPR · PCI DSS 등) |

**Skip 옵션**: `MCP_HTTP_ENABLED=false` — 외부 도구 노출 안 함.

---

## Part 6. 업그레이드 · 백업 · 모니터링

> **EN**: Day-2 operations. Upgrade path, backup strategy by scenario, what to monitor.

### 6-A. 업그레이드 — Docker vs Helm

#### Docker Compose

```bash
cd ~/mond
git fetch && git checkout v0.2.0    # 신규 태그 체크아웃
docker compose pull                  # 새 이미지 받기
docker compose up -d                 # 무중단 재시작 (DB는 보존)
docker compose exec backend alembic upgrade head   # 스키마 마이그레이션
```

#### Helm

```bash
helm upgrade mond oci://ghcr.io/jland-93/charts/mond \
  --version 0.2.0 \
  -n mond \
  --reuse-values

# 또는 새 values로 덮어쓰기
helm upgrade mond oci://ghcr.io/jland-93/charts/mond \
  --version 0.2.0 \
  -n mond \
  -f charts/mond/values-prod.yaml
```

> ✅ 백엔드 Deployment의 `initContainer`가 자동으로 `alembic upgrade head` 실행. 수동 단계 불필요.

> 주의 — 메이저 업그레이드(v0.x → v1.x)는 반드시 [CHANGELOG.md](../CHANGELOG.md)의 BREAKING CHANGES 섹션 확인 후.

### 6-B. 백업 전략 — 시나리오별

| 시나리오 | DB 백업 | 시크릿 백업 | 빈도 |
|---|---|---|---|
| A (개인) | 불필요 | 불필요 | — |
| B (사내 데모) | `docker compose exec postgres pg_dump -U mond mond > backup.sql` | `.env` 파일 git-crypt | 주 1회 |
| **C (운영)** | **RDS automated backup** (PIT 7~35일) | External-Secrets 소스(AWS SM 자체 백업) | 자동 |
| **D (폐쇄망)** | 사내 `pg_dump` cron + 외부 스토리지 격리 | Sealed-Secrets는 Git에 봉인된 채로 보관 | 일 1회 |

#### 백업 명령 예시

```bash
# Docker
docker compose exec -T postgres pg_dump -U mond mond | gzip > mond-$(date +%F).sql.gz

# Kubernetes
kubectl -n mond exec deploy/postgres -- pg_dump -U mond mond | gzip > mond-$(date +%F).sql.gz

# 복구
gunzip -c mond-2026-06-18.sql.gz | docker compose exec -T postgres psql -U mond mond
```

> 주의 — **Mond 백업 = DB 백업**입니다. 사용자·자산·정책·발견사항·MFA factor 모두 DB에 있음. 시크릿(SECRET_KEY 등)만 별도 관리.

### 6-C. 모니터링 — 무엇을 봐야 하나

| 항목 | 어디서 | 임계값 |
|---|---|---|
| 백엔드 health | `GET /health` → 200 OK | 5xx 발생 시 알림 |
| Prometheus metrics | `GET :8000/metrics` | scrape 5s |
| Pod restart 횟수 | `kubectl get pods -n mond` | 1시간 3회 이상 알림 |
| DB connection pool 포화 | metrics `mond_db_pool_used` | 80% 이상 알림 |
| AI 호출 실패율 | metrics `mond_ai_request_total{status="error"}` | 10% 이상 알림 |
| 스캔 실패율 | metrics `mond_scan_total{status="failed"}` | 20% 이상 알림 |

#### Prometheus + Grafana 권장 (C 시나리오)

```yaml
# ServiceMonitor (prometheus-operator)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mond-backend
  namespace: mond
spec:
  selector:
    matchLabels: { app: mond-backend }
  endpoints:
    - port: http
      path: /metrics
      interval: 5s
```

#### 로그 확인

```bash
# Docker
docker compose logs -f backend
docker compose logs -f frontend

# Kubernetes
kubectl -n mond logs -f deploy/mond-backend
kubectl -n mond logs -f deploy/mond-frontend
```

### 6-D. 사용자 데이터 마이그레이션 (이전 인스턴스 → 새 인스턴스)

```bash
# 1) 기존 인스턴스에서 dump
docker compose exec -T postgres pg_dump -U mond mond > dump.sql

# 2) 새 인스턴스에서 restore
docker compose exec -T postgres psql -U mond -d mond < dump.sql

# 3) SECRET_KEY는 그대로 유지 — 안 그러면 모든 세션 무효화
```

> 주의 — SECRET_KEY를 바꾸면 기존 세션 쿠키·MFA enrollment 모두 무효화. 의도된 경우만 변경.

---

## Part 7. 트러블슈팅

> **EN**: Common pitfalls and fixes.

### Q. AI Insights 카드가 "ANTHROPIC_API_KEY 미설정" 안내만 보임

→ 휴리스틱 모드. `.env`에 `ANTHROPIC_API_KEY` 또는 다른 provider 설정 후 백엔드 재시작.

### Q. `/mfa`에서 패스키 등록 버튼이 비활성

→ HTTP + 사내 IP 환경. **TOTP 사용** (Google Authenticator 등). 또는 HTTPS 도메인으로 배포.

### Q. 첫 로그인이 admin이 안 됨

→ `SSO_ADMIN_EMAILS`에 미리 박혀있지 않으면, **DB에 사용자가 1명도 없을 때 첫 가입자**만 admin. 이미 다른 사용자가 있다면 기존 admin이 Users & Roles에서 승격해야 함.

### Q. 운영 부팅 실패 — "SECRET_KEY too short"

→ 운영 가드. `SECRET_KEY`를 48자 이상 random으로 교체. `python -c 'import secrets;print(secrets.token_urlsafe(48))'`.

### Q. IAM source가 "demo" 상태로 표시됨

→ GCP / Azure는 v0.1에서 capability API가 `demo`/`coming_soon`을 정직하게 노출. AWS / K8s / LDAP은 production ready. v0.2에서 grant/revoke 완성 예정.

### Q. 스캔이 매우 느림 / 타임아웃

→ 현재 인라인 동기 실행. 대용량 자산은 v0.2 Celery 큐 도입 예정. 그동안은 자산 단위로 작게 쪼개기.

### Q. MCP 서버를 Claude Desktop에 연결하고 싶다

→ [Part 5 · 11) MCP 서버 활성화](#11-mcp-서버-활성화-선택--claude-desktop--code-연동) 참고. 운영에선 `MCP_HTTP_AUTH_TOKEN`을 반드시 설정하고 client config의 `headers.Authorization: Bearer ...`로 전달.

---

## 📖 다음 단계

- 🌙 Mond가 뭐 하는 OSS인지 → [docs/ABOUT.md](ABOUT.md)
- 🤝 기여 → [CONTRIBUTING.md](../CONTRIBUTING.md)
- 🔐 보안 정책 → [SECURITY.md](../SECURITY.md)
- 📋 사전 릴리즈 체크리스트 → [PRE_RELEASE_CHECKLIST.md](../PRE_RELEASE_CHECKLIST.md)
- 📜 라이선스 → MIT

---

## 🧭 문서 한눈에 · Doc Map

| 문서 | 위치 | 무엇 |
|---|---|---|
| 🏠 **메인 README** | [`/README.md`](../README.md) | 프로젝트 소개 · 스크린샷 · 빠른 시작 |
| 🌙 **About** | [`docs/ABOUT.md`](ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ **Setup** (이 문서) | [`docs/SETUP.md`](SETUP.md) | 설치 · 운영 · 시나리오 가이드 |
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
