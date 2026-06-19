# 🌙 Mond Frontend — multi-stage 운영용 이미지
# - vite build → nginx-unprivileged(8080) static serve
# - 비루트(101) 실행
# - API base URL은 빌드 시 ARG로 또는 런타임 env 주입(/env.js)으로 변경 가능

ARG NODE_VERSION=20-alpine
ARG NGINX_VERSION=1.27-alpine

# ── 1) 빌드 스테이지 ───────────────────────────────────────────
FROM node:${NODE_VERSION} AS build

ENV CI=true

WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; \
    else npm install --no-audit --no-fund; fi

COPY . .

# 빌드 시 정적으로 박힐 backend URL. 운영에선 보통 같은 도메인의 /api로 프록시한다.
ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


# ── 2) 런타임 스테이지 (nginx unprivileged) ────────────────────
FROM nginxinc/nginx-unprivileged:${NGINX_VERSION} AS runtime

# nginx-unprivileged는 기본 8080 포트 + nginx user.
# nginx.conf는 templates/로 두면 표준 entrypoint(20-envsubst-on-templates.sh)가
# ${MOND_API_UPSTREAM} 등을 ENV로 치환해 /etc/nginx/conf.d/default.conf로 작성한다.
USER root
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER nginx

ENV MOND_API_UPSTREAM=http://backend:8000

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
  CMD wget -q -O- http://127.0.0.1:8080/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
