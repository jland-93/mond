"""
🌙 Mond 설정

환경 변수는 .env 파일에서 로드한다. 모든 설정은 pydantic-settings로 검증된다.
"""

import logging
from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# 운영에서 쓰면 안 되는 기본/약한 SECRET_KEY 패턴.
# .env.example의 placeholder 풀 문자열도 거부 — 사용자가 그대로 운영에 올리는 사고를 막는다.
_WEAK_SECRET_KEYS = {
    "change-me-in-production",
    "change-me-in-production-use-a-long-random-string",
    "changeme",
    "secret",
    "dev",
    "mond",
}


class Settings(BaseSettings):
    """애플리케이션 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 애플리케이션 메타
    APP_NAME: str = "Mond"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(default="change-me-in-production", min_length=8)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1일

    # 데이터베이스 — asyncpg URL
    DATABASE_URL: str = "postgresql+asyncpg://mond:mond@localhost:5432/mond"

    # Redis (Celery broker + 캐시)
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── LLM provider 추상화 ─────────────────────────────────────
    # 사용자가 자기 환경의 AI API를 끌어다 쓰게 한다.
    # 지원: anthropic / openai / bedrock / ollama
    # 빈 값이면 휴리스틱(기본 규칙) 모드로 자동 폴백.
    AI_PROVIDER: str = "anthropic"  # 또는 "openai" / "bedrock" / "ollama"

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL_DEFAULT: str = "claude-haiku-4-5-20251001"
    AI_MODEL_DEEP: str = "claude-sonnet-4-6"
    AI_MAX_TOKENS: int = 2048

    # OpenAI (GPT-4o, GPT-5, GPT-4 turbo 등)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None      # Azure OpenAI 호환 또는 사내 게이트웨이
    OPENAI_MODEL_DEFAULT: str = "gpt-4o-mini"
    OPENAI_MODEL_DEEP: str = "gpt-4o"

    # AWS Bedrock (boto3 자격으로 Claude / Llama / Titan 호출)
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MODEL_DEFAULT: str = "anthropic.claude-3-5-haiku-20241022-v1:0"
    BEDROCK_MODEL_DEEP: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Ollama / vLLM (로컬 LLM — 폐쇄망/데이터 외부 유출 금지 환경)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_DEFAULT: str = "llama3.1:8b"
    OLLAMA_MODEL_DEEP: str = "llama3.1:70b"

    # 스캐너 통합 토글 (없으면 stub 모드로 동작)
    SCANNER_TRIVY_BIN: Optional[str] = "trivy"
    SCANNER_SEMGREP_BIN: Optional[str] = "semgrep"
    SCANNER_NUCLEI_BIN: Optional[str] = "nuclei"

    # 관측성
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_ENABLED: bool = True

    # 시드 데이터 (개발용)
    SEED_ON_STARTUP: bool = True

    # 알림 채널 (URL 비어 있으면 no-op)
    SLACK_WEBHOOK_URL: Optional[str] = None
    GENERIC_WEBHOOK_URL: Optional[str] = None
    NOTIFY_MIN_SEVERITY: str = "high"  # critical / high / medium / low / info

    # 외부 통합 — GitHub Webhook 검증용 (없으면 검증 생략, 개발 편의)
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # i18n 기본 언어 (UI 초기 로드 시 사용)
    DEFAULT_LOCALE: str = "ko"

    # MCP HTTP 마운트 — Streamable HTTP > SSE 순서로 시도. mcp 패키지가 둘 다 실패해도 backend는 정상.
    MCP_HTTP_ENABLED: bool = True

    # ── SSO / RBAC ──────────────────────────────────────────────
    # 인증 모드: "sso" (실제 IdP) / "dev" (이메일 입력만, OSS 데모용)
    AUTH_MODE: str = "dev"
    # 세션 cookie 이름 / 유효 시간 / Secure 플래그
    SESSION_COOKIE: str = "mond_session"
    SESSION_DAYS: int = 7
    SESSION_SECURE: bool = False  # prod는 true(HTTPS)
    # 콤마로 묶인 활성 OIDC provider 목록 (예: "keycloak,okta,google")
    SSO_PROVIDERS: str = ""
    # 각 provider별 설정 — ENV로 주입. provider 이름 prefix.
    SSO_KEYCLOAK_ISSUER: Optional[str] = None
    SSO_KEYCLOAK_CLIENT_ID: Optional[str] = None
    SSO_KEYCLOAK_CLIENT_SECRET: Optional[str] = None
    SSO_OKTA_ISSUER: Optional[str] = None
    SSO_OKTA_CLIENT_ID: Optional[str] = None
    SSO_OKTA_CLIENT_SECRET: Optional[str] = None
    SSO_GOOGLE_CLIENT_ID: Optional[str] = None
    SSO_GOOGLE_CLIENT_SECRET: Optional[str] = None
    # 로그인 후 리다이렉트 base URL (FE)
    SSO_REDIRECT_BASE: str = "http://localhost:3000"
    # 첫 가입자 자동 ADMIN 지정 — empty면 모두 EMPLOYEE
    SSO_ADMIN_EMAILS: str = ""

    # ── MFA (패스키 + TOTP + 백업 코드) ─────────────────────────
    # 강제 대상 role 콤마 목록. 비우면 MFA 미강제(권장만).
    MFA_REQUIRED_ROLES: str = "admin,reviewer"
    # WebAuthn Relying Party
    MFA_RP_ID: str = "localhost"               # 운영: 도메인 (예: mond.your-corp.com)
    MFA_RP_NAME: str = "Mond"
    MFA_RP_ORIGIN: str = "http://localhost:3000"  # 운영: https://...
    # MFA challenge TTL(초)
    MFA_CHALLENGE_TTL: int = 300

    # ── 운영 가드 ───────────────────────────────────────────────
    @model_validator(mode="after")
    def _validate_for_production(self) -> "Settings":
        """ENVIRONMENT=production 일 때 위험한 설정 조합을 거부한다.

        Why: 오픈소스 배포 시 기본값 그대로 운영에 올라가는 사고를 막기 위함.
        """
        if self.ENVIRONMENT.lower() != "production":
            return self
        problems: list[str] = []
        if self.SECRET_KEY.strip().lower() in _WEAK_SECRET_KEYS or len(self.SECRET_KEY) < 32:
            problems.append(
                "SECRET_KEY가 약하다. 32자 이상 무작위 값 사용. 예) python -c \"import secrets;print(secrets.token_urlsafe(48))\""
            )
        if self.DEBUG:
            problems.append("DEBUG=true는 운영에서 금지")
        if self.AUTH_MODE == "dev":
            problems.append("AUTH_MODE=dev는 데모용. 운영에서는 'sso' + SSO_PROVIDERS 설정 필수")
        if not self.SESSION_SECURE:
            problems.append("SESSION_SECURE=true 필요 (HTTPS 쿠키 강제)")
        if problems:
            joined = "\n  - " + "\n  - ".join(problems)
            raise ValueError(f"운영(production) 환경에서 다음 설정을 고쳐야 한다:{joined}")
        return self


settings = Settings()
