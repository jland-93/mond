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
        libpq5 curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 mond \
    && useradd  --system --uid 1000 --gid mond --create-home --home-dir /home/mond mond

COPY --from=deps /opt/venv /opt/venv

WORKDIR /app
COPY --chown=mond:mond . .

USER 1000:1000

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/api/v1/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips=*"]
