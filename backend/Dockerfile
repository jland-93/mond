# 🌙 Mond Backend — multi-stage 운영용 이미지
# - 비루트(uid 1000) 실행
# - 의존성과 코드 레이어 분리로 캐시 효율↑
# - tini를 PID 1로 + uvicorn 직접 실행
# - /api/v1/health 기반 HEALTHCHECK

ARG PYTHON_VERSION=3.12-slim

# ── 1) 의존성 빌드 ─────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


# ── 2) 런타임 ─────────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 mond \
    && useradd  --system --uid 1000 --gid mond --create-home --home-dir /home/mond mond

# OPA Rego 평가 — 단일 Go 바이너리. arm64/amd64 자동 분기.
# 미설치 환경도 동작(엔진 'opa' 정책만 비활성)하므로 download 실패 시 build를 끊지 않음.
ARG OPA_VERSION=v1.17.1
RUN set -e; \
    arch="$(uname -m)"; \
    case "$arch" in \
      x86_64)  opa_arch=amd64 ;; \
      aarch64) opa_arch=arm64 ;; \
      arm64)   opa_arch=arm64 ;; \
      *)       echo "Skip OPA install for arch=$arch"; exit 0 ;; \
    esac; \
    if curl -fsSL -o /usr/local/bin/opa \
         "https://github.com/open-policy-agent/opa/releases/download/${OPA_VERSION}/opa_linux_${opa_arch}_static"; then \
      chmod 755 /usr/local/bin/opa; \
      /usr/local/bin/opa version; \
    else \
      echo "OPA download failed — engine 'opa' will be disabled"; \
      rm -f /usr/local/bin/opa; \
    fi

COPY --from=deps /opt/venv /opt/venv

WORKDIR /app
COPY --chown=mond:mond . .

USER 1000:1000

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/api/v1/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips=*"]
