# 🔒 Security Policy

## 🌙 Mond Security Commitment

Security is at the heart of Mond's mission. As a DevSecOps platform, we take security seriously and are committed to maintaining the highest standards of security for our users and contributors.

## 🛡️ Supported Versions

Mond is pre-1.0. We currently support security fixes for the latest minor release on `main` only.

| Version | Supported          |
| ------- | ------------------ |
| 0.x (main) | ✅ Yes |
| earlier | ❌ No |

## 🚨 Reporting Security Vulnerabilities

### 🔐 Private Disclosure

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities responsibly through one of these channels:

#### Preferred — GitHub Security Advisory
- **Open a private advisory**: <https://github.com/jland-93/mond/security/advisories/new>
- The advisory thread is end-to-end private to maintainers until disclosed.

#### Alternative
- Open a private GitHub Discussion and mention `@jland-93` if the advisory flow is unavailable.

### 📋 What to Include

When reporting a security vulnerability, please include:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and attack scenarios
3. **Reproduction**: Step-by-step instructions to reproduce
4. **Environment**: Affected versions and configurations
5. **Proof of Concept**: Code or screenshots (if applicable)
6. **Suggested Fix**: If you have ideas for remediation

### 📝 Report Template

```markdown
## Vulnerability Summary
Brief description of the vulnerability

## Impact Assessment
- Severity: [Critical/High/Medium/Low]
- Attack Vector: [Network/Local/Physical]
- Authentication Required: [Yes/No]
- User Interaction: [Required/Not Required]

## Affected Components
- Component: [e.g., Scanner adapter, AI engine, Auth]
- Versions: [e.g., commit hash or release tag]
- Environment: [e.g., docker-compose, Kubernetes, local]

## Reproduction Steps
1. Step one
2. Step two
3. Step three

## Proof of Concept
[Code, screenshots, or detailed explanation]

## Suggested Mitigation
[Your suggestions for fixing the issue]

## Additional Context
[Any other relevant information]
```

## ⏱️ Response Timeline

We are committed to responding to security reports promptly:

| Severity | Initial Response | Status Update | Resolution Target |
|----------|------------------|---------------|-------------------|
| Critical | 24 hours | 48 hours | 7 days |
| High | 48 hours | 72 hours | 14 days |
| Medium | 72 hours | 1 week | 30 days |
| Low | 1 week | 2 weeks | 60 days |

## 🏆 Security Researcher Recognition

We believe in recognizing security researchers who help make Mond more secure:

### 🎖️ Hall of Fame
Security researchers who responsibly disclose vulnerabilities will be:
- Listed in our Security Hall of Fame (with permission)
- Credited in release notes and security advisories
- Invited to our private security researcher community

### 🎁 Rewards Program
While we don't currently offer monetary rewards, we provide:
- Public recognition and thanks
- Mond swag and merchandise
- Early access to new features
- Direct communication channel with maintainers

## 🔍 Security Best Practices

### For Users
- **Keep Updated**: Always use the latest version of Mond
- **Secure Configuration**: Follow our security configuration guide
- **Access Control**: Implement proper IAM and RBAC policies
- **Monitoring**: Enable security monitoring and alerting
- **Secrets Management**: Use proper secrets management solutions

### For Contributors
- **Secure Coding**: Follow OWASP secure coding practices
- **Dependency Management**: Keep dependencies updated
- **Code Review**: All code must be reviewed before merging
- **Testing**: Include security tests in your contributions
- **Documentation**: Document security considerations

## 🛠️ Security Posture (MVP)

Mond is an OSS DevSecOps platform — we hold ourselves to the standards we recommend. The current release includes:

- **OIDC SSO** (Keycloak / Okta / Google) + server-side sessions (opaque token, instant revoke)
- **4-tier RBAC** (VIEWER < EMPLOYEE < REVIEWER < ADMIN) enforced per endpoint via `require_role(...)`
- **MFA** — Passkey (WebAuthn / FIDO2) + TOTP + one-time backup codes, with `MFA_REQUIRED_ROLES` enforcement
- **Production boot gate** — refuses to start with weak `SECRET_KEY`, `DEBUG=true`, `AUTH_MODE=dev`, or `SESSION_SECURE=false`
- **Input validation** via pydantic at every API boundary
- **Structured audit logs** via `structlog`
- **No secrets in repo** — `.env` is gitignored; `.env.example` ships placeholders only
- **Scanner sandboxing** — adapter subprocess invocations are explicit and non-shell

Planned (see roadmap):

- Rate limiting / abuse protection
- E2E encryption for AI prompts containing customer code
- OPA Rego policy evaluation

## 📚 Security Resources

### Documentation
- [Architecture Overview](docs/development/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [OpenSSF Best Practices](https://www.bestpractices.dev/)

## 🔄 Security Updates

### Notification Channels
- **GitHub Security Advisories**: automatic notifications when published
- **Release Notes**: security fixes highlighted with `security:` scope

### Update Process
1. **Assessment**: Evaluate impact and severity
2. **Development**: Develop and test fix
3. **Review**: Security team review
4. **Release**: Coordinated disclosure and release
5. **Communication**: Notify users and community

## 🤝 Security Community

### Collaboration
We work with:
- Security researchers reporting through this policy
- Open source security communities
- Industry security organizations

### Contributions
Security contributions are welcome:
- Security feature implementations
- Vulnerability assessments
- Security documentation improvements
- Security testing and automation

## 📞 Contact Information

### Maintainer
- **Lead**: [@jland-93](https://github.com/jland-93)
- **GitHub Security Advisory**: <https://github.com/jland-93/mond/security/advisories/new> (preferred)

---

**Thank you for helping keep Mond and our community safe! 🌙🔒**
