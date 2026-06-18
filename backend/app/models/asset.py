"""
Asset — 보호 대상 (repo / image / host / URL / cloud resource / application)

회사 특화 ARN/AWS 의존을 제거하고, URI 기반의 범용 자산으로 일반화한다.
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.scan import Scan


class AssetType(str, enum.Enum):
    REPOSITORY = "repository"          # git+ssh://... or https://github.com/...
    CONTAINER_IMAGE = "container_image"  # docker://registry/image:tag
    HOST = "host"                       # ssh://host or ip://
    URL = "url"                         # https://example.com
    CLOUD_RESOURCE = "cloud_resource"   # aws://..., gcp://..., k8s://...
    APPLICATION = "application"         # 논리적 서비스 묶음


class Asset(Base, TimestampMixin):
    """보호 대상 자산. 모든 스캔과 발견사항의 단일 진실 공급원."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", native_enum=False),
        nullable=False,
        index=True,
    )
    uri: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(2048))

    # 자유 라벨 (key→value). 예: {"team": "platform", "criticality": "high"}
    labels: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    owner: Mapped[str | None] = mapped_column(String(255), index=True)
    environment: Mapped[str | None] = mapped_column(String(64), index=True)  # dev / staging / prod

    # 통계 캐시 (서비스 계층에서 갱신)
    open_findings_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_scanned_at_str: Mapped[str | None] = mapped_column(String(64))

    scans: Mapped[list["Scan"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
