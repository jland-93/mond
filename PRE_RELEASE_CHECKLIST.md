# 🌙 Mond Pre-Release Checklist

OSS 공개 / 마이너 버전 릴리스 전에 점검할 항목들입니다.

## 🔒 보안 검토

- [ ] 시크릿/토큰/API 키가 코드에 하드코딩되어 있지 않은지 grep
- [ ] `.env`가 `.gitignore`에 포함되어 있는지 확인
- [ ] 외부에 노출되는 OpenAPI 스키마가 내부 정보를 새지 않는지 확인
- [ ] 새로 추가된 의존성에 알려진 취약점이 없는지 확인 (`pip-audit` / `npm audit`)

## 📝 라이선스 / IP

- [ ] 새 의존성의 라이선스가 MIT와 호환되는지 확인 (GPL-only 등 회피)
- [ ] 외부 코드 차용분에 출처/라이선스 표기

## 🧹 코드 품질

- [ ] `ruff check .` 통과
- [ ] `npm run lint` 통과
- [ ] 도커 이미지 빌드 성공
- [ ] `docker compose up`으로 데모 시드 확인

## 📚 문서

- [ ] README의 Quick Start가 깨끗한 환경에서 동작
- [ ] `.env.example`에 모든 신규 환경 변수 반영
- [ ] `CHANGELOG.md` 의 `[Unreleased]` 섹션을 신규 버전 헤더로 굴리기

## 🧪 기능 검증

- [ ] 자산 생성 → 스캔 트리거 → Finding 생성 → AI 분석 흐름 수동 확인
- [ ] AI 키 없는 환경에서 기본 규칙 fallback 동작 확인
- [ ] 새 스캐너 어댑터를 추가했다면 stub 모드 동작 확인

## 🚀 릴리스

- [ ] 태그 생성 (`v0.x.y`)
- [ ] GitHub Release 노트 작성 (Conventional Commits 기반)
- [ ] Security 영향이 있다면 Advisory 동반 게시

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
| 📋 [`CHANGELOG.md`](CHANGELOG.md) | 변경 내역 |
| ✅ [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) (이 문서) | 릴리즈 점검 |
