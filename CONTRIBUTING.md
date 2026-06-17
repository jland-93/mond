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
# Optional: ANTHROPIC_API_KEY=...  (없으면 휴리스틱 모드)
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

### Test Coverage
- Maintain minimum 80% test coverage
- Write unit tests for new features
- Include integration tests for API endpoints
- Add E2E tests for critical user flows

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
- Use Ant Design components as base
- Follow atomic design methodology
- Implement proper TypeScript interfaces
- Include Storybook documentation

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
- Join our [Slack community](https://slack.mond.dev)
- Start a [GitHub Discussion](https://github.com/jland-93/mond/discussions)

### Mentorship
New contributors can request mentorship through:
- GitHub Discussions with `mentorship` label
- Slack `#newcomers` channel
- Direct message to maintainers

---

**Thank you for contributing to Mond! Together, we're illuminating the path to secure DevOps. 🌙**
