"""
조직 Slack workspace 연동 — 목적별 채널에 webhook URL 매핑.

OSS 사용자는 자기 워크스페이스의 Incoming Webhook URL을 Admin UI에서 등록.
ENV(SLACK_WEBHOOK_URL · DIGEST_SLACK_WEBHOOK_URL)는 fallback으로 남아 있다.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SlackPurpose(str, enum.Enum):
    DEFAULT = "default"            # purpose가 더 구체적으로 잡히지 않을 때 fallback
    DIGEST = "digest"              # Daily Security Digest
    FINDING = "finding"            # severity 임계 이상 신규 finding 알림
    ACCESS_REQUEST = "access_request"  # 권한 요청 / 검토 알림
    ROLE_REQUEST = "role_request"  # 역할 변경 요청


class SlackChannel(Base, TimestampMixin):
    __tablename__ = "slack_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    purpose: Mapped[SlackPurpose] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    label: Mapped[str | None] = mapped_column(String(255))  # 예: "#mond-alerts"
    webhook_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
