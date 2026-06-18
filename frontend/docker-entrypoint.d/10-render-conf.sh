#!/bin/sh
# 🌙 nginx.conf의 ${MOND_API_UPSTREAM}을 런타임 ENV로 치환한다.
# nginx-unprivileged 이미지가 /docker-entrypoint.d/*.sh를 자동 실행한다.
set -eu
: "${MOND_API_UPSTREAM:=http://backend:8000}"
envsubst '${MOND_API_UPSTREAM}' \
  < /etc/nginx/conf.d/default.conf \
  > /tmp/default.conf \
  && cat /tmp/default.conf > /etc/nginx/conf.d/default.conf
