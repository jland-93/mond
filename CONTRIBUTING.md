# 🌙 Contributing to Mond

Thank you for your interest in contributing to Mond! We welcome contributions from the community and are excited to see what you'll bring to this project.

## 🎯 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Git

### Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/mond.git
cd mond
```

2. **Backend Setup**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Optional: ANTHROPIC_API_KEY=...  (없으면 기본 규칙 모드)
```

5. **Run with Docker (recommended)**
```bash
docker compose up -d
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

## 🛠️ Development Workflow

### Branch Naming Convention
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Message Format
We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(scanners): add Snyk scanner adapter
fix(ai): handle malformed JSON from model
docs(readme): clarify ANTHROPIC_API_KEY setup
```

## 🧪 Testing

### Running Tests
```bash
# Backend tests
cd backend
pytest -v

# Frontend type check + build
cd frontend
npm run build
```

### Tests
- Test contributions are very welcome — current coverage is intentionally light (MVP).
- New scanner adapters / AI prompts / policy rules should ship with at least one unit test.
- Integration tests for API endpoints are encouraged for any endpoint that mutates state.

## 📝 Code Style

### Python (Backend)
```bash
# Format
black .

# Lint (replaces flake8 + isort + much of mypy)
ruff check .
```

### TypeScript (Frontend)
```bash
npm run lint
npm run format
```

### Code conventions
- **한글 주석** — 도메인 의도를 한국어로. API 텍스트는 영어.
- **Conventional Commits** — `<type>(<scope>): <subject>`
- Pure functions in services, side effects only in routes.

## 🎨 UI/UX Guidelines

### Design Principles
- **Moonlight Theme**: Dark UI with gentle blue accents
- **Minimalism**: Clean, uncluttered interfaces
- **Accessibility**: WCAG 2.1 AA compliance
- **Responsiveness**: Mobile-first design

### Component Standards
- Use Ant Design components as a base
- Implement proper TypeScript interfaces
- Co-locate components by domain; share common UI in `components/`

## 🔒 Security Guidelines

### Security Best Practices
- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper input validation
- Follow OWASP security guidelines
- Regular dependency updates

### Reporting Security Issues
See [SECURITY.md](SECURITY.md). Prefer GitHub Security Advisories for private disclosure.

## 📋 Pull Request Process

### Before Submitting
1. ✅ Tests pass locally
2. ✅ Code follows style guidelines
3. ✅ Documentation updated
4. ✅ No merge conflicts
5. ✅ Descriptive PR title and description

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs
2. **Code Review**: At least one maintainer review
3. **Testing**: QA testing for significant changes
4. **Approval**: Maintainer approval required
5. **Merge**: Squash and merge to main

---

## 🤖 자동화 · Automation (불특정 다수 기여자가 알아두면 좋은 것)

PR을 올리면 다음이 **자동**으로 일어납니다 — 손댈 필요 없습니다.

| 자동화 | 무엇이 일어나는가 | 어디 |
|---|---|---|
| **CI** | Backend (Python 3.12) / Frontend (Node 24) / Knowledge Link Check 동시 실행 | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| **CodeQL** | Python + TypeScript 정적 보안 분석. 결과는 Security → Code scanning 탭 | [.github/workflows/codeql.yml](.github/workflows/codeql.yml) |
| **PR auto-label by path** | 변경 파일 경로 기반으로 `backend`/`frontend`/`design`/`docs` 등 자동 라벨 | [.github/labeler.yml](.github/labeler.yml) |
| **PR auto-label by title** | Conventional Commits title(`feat:` / `fix:` / `docs:` ...)로 라벨 자동 부착 | [.github/release-drafter.yml](.github/release-drafter.yml) |
| **Release Drafter** | PR이 머지될 때마다 다음 릴리즈의 노트 draft 자동 갱신 | [.github/workflows/release-drafter.yml](.github/workflows/release-drafter.yml) |
| **CODEOWNERS auto-review** | 변경 경로에 따라 reviewer가 자동 지정 | [.github/CODEOWNERS](.github/CODEOWNERS) |
| **Dependabot** | 의존성 업데이트를 weekly로 자동 PR (4 ecosystem: pip · npm · actions · docker) | [.github/dependabot.yml](.github/dependabot.yml) |

→ 기여자가 신경 쓸 건 **PR title을 Conventional Commits 형식으로** 적는 것만 신경 쓰면 됨.

### Branch Protection (main)

`main`은 보호되어 있습니다:
- 직접 push **차단** — 반드시 PR
- PR 머지에 **CI 통과 + 1명 이상 review 승인** 필요
- force-push / 삭제 차단
- 머지 방식: merge commit (commit 의미 단위 보존)

### Issue / Discussion 동선

| 무엇을 하고 싶나 | 어디로 |
|---|---|
| 🐛 버그 신고 | [Issue → Bug Report](https://github.com/jland-93/mond/issues/new?template=bug_report.yml) |
| ✨ 새 기능 제안 | [Issue → Feature Request](https://github.com/jland-93/mond/issues/new?template=feature_request.yml) |
| ❓ 설치/사용 질문 (구체) | [Issue → Question](https://github.com/jland-93/mond/issues/new?template=question.yml) |
| 💬 자유 토론 / 아이디어 / 로드맵 의견 | [GitHub Discussions](https://github.com/jland-93/mond/discussions) |
| 🔐 보안 취약점 (비공개) | [Security Advisory](https://github.com/jland-93/mond/security/advisories/new) |

### 처음 기여하시나요?

→ [`good first issue` 라벨](https://github.com/jland-93/mond/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 부터 살펴보세요. 메인테이너가 가이드도 함께 답변합니다.

## 🏷️ Issue Guidelines

### Bug Reports
Use the bug report template and include:
- Environment details
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/logs if applicable

### Feature Requests
Use the feature request template and include:
- Problem description
- Proposed solution
- Alternative solutions considered
- Additional context

### Issue Labels
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority/high` - High priority items

## 🌟 Recognition

### Contributors
All contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights

### Maintainer Path
Active contributors may be invited to become maintainers based on:
- Consistent quality contributions
- Community engagement
- Technical expertise
- Alignment with project values

## 📚 Resources

### Documentation
- [Architecture](docs/development/architecture.md)
- [README](README.md) — Quick start & feature overview

### Community
- [GitHub Issues](https://github.com/jland-93/mond/issues)
- [GitHub Discussions](https://github.com/jland-93/mond/discussions)

## 🤝 Getting Help

### Questions?
- Check existing [GitHub Issues](https://github.com/jland-93/mond/issues)
- Start a [GitHub Discussion](https://github.com/jland-93/mond/discussions)

### Mentorship
New contributors can request mentorship by opening a GitHub Discussion with the `mentorship` label.

---

**Thank you for contributing to Mond! Together, we're illuminating the path to secure DevOps. 🌙**

---

## 🧭 문서 한눈에 · Doc Map

| 문서 | 무엇 |
|---|---|
| 🏠 [`README.md`](README.md) | 프로젝트 소개 · 스크린샷 |
| 🌙 [`docs/ABOUT.md`](docs/ABOUT.md) | 왜 만들었나 · 무엇을 푸는가 · 로드맵 |
| 🛠️ [`docs/SETUP.md`](docs/SETUP.md) | 설치 · 운영 · 시나리오 가이드 |
| 🏗️ [`docs/development/architecture.md`](docs/development/architecture.md) | 시스템 구조 |
| 🤝 [`CONTRIBUTING.md`](CONTRIBUTING.md) (이 문서) | 기여 가이드 |
| 🔐 [`SECURITY.md`](SECURITY.md) | 취약점 신고 |
| 📜 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | 커뮤니티 규범 |
| 📋 [`CHANGELOG.md`](CHANGELOG.md) | 변경 내역 |
| ✅ [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) | 릴리즈 점검 |
