"""
사용자별 Slack 알림 설정.

User 테이블에 컬럼을 추가하면 schema migration이 필요하지만,
별도 테이블로 두면 Base.metadata.create_all로 신규 환경에서 자동 생성된다.
이미 운영 중인 환경에는 backend 재시작 시 누락 테이블이 추가된다.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UserSlackPreference(Base, TimestampMixin):
    __tablename__ = "user_slack_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    # 본인 DM webhook (선택) — workspace에서 본인 DM을 받는 채널을 위한 URL.
    # 보통 Slack workflow 또는 사용자 본인이 만든 채널의 webhook을 등록.
    slack_dm_webhook_url: Mapped[str | None] = mapped_column(String(1024))
    # Slack user ID (선택) — U12345 형식. organization 채널 알림에 @mention용.
    slack_user_id: Mapped[str | None] = mapped_column(String(64))
    # 본인 owner asset의 신규 finding을 DM으로 받을지.
    notify_finding: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
