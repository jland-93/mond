"""
Workspace — 다중 조직/팀이 한 Mond 인스턴스를 공유할 때 자산 scope.

v0.3 MVP는 Asset만 workspace로 분리한다 (NULL 허용으로 기존 데이터 백필
안전성 확보). Policy/Finding/IAM 등 나머지 자원은 v0.4에서 확장.

운영 모델
--------
- 단일 조직: workspace 1개(default)만 사용. 기존 사용자에게 영향 0.
- 다중 조직: 관리자가 Admin → 워크스페이스에서 추가. 자산 등록/조회 시
  현재 workspace에 자동 묶이고, X-Mond-Workspace 헤더로 전환.

slug는 URL/header 사용용 (소문자·하이픈). seed에서 'default' 1건을
is_default=True로 생성.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512))
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
