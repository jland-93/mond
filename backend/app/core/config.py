"""
🌙 Mond 설정

환경 변수는 .env 파일에서 로드한다. 모든 설정은 pydantic-settings로 검증된다.
"""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # LLM (Anthropic Claude)
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL_DEFAULT: str = "claude-haiku-4-5-20251001"
    AI_MODEL_DEEP: str = "claude-sonnet-4-6"
    AI_MAX_TOKENS: int = 2048

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


settings = Settings()
