"""
스캐너 어댑터 베이스

각 통합(Trivy/Semgrep/Nuclei/…)은 ScannerAdapter를 구현한다.
바이너리/원격 API 없이도 stub 모드로 동작해 OSS 사용자가 즉시 데모할 수 있다.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass

from app.models.asset import Asset


@dataclass
class RawFinding:
    """어댑터가 반환하는 스캐너-중립 발견 사항."""

    rule_id: str
    title: str
    severity: str  # critical / high / medium / low / info
    description: str | None = None
    location: str | None = None
    references: list[str] | None = None
    extra: dict | None = None


@dataclass
class ScanResult:
    findings: list[RawFinding]
    raw_output: dict
    error: str | None = None


class ScannerAdapter(abc.ABC):
    """스캐너 어댑터 인터페이스."""

    name: str = "base"
    """레지스트리 등록 키 (소문자)."""

    supported_asset_types: tuple[str, ...] = ()
    """해당 어댑터가 처리할 수 있는 자산 타입."""

    @abc.abstractmethod
    async def scan(self, asset: Asset) -> ScanResult:
        """자산을 스캔하고 결과를 반환한다. 예외를 던지지 말고 ScanResult.error로 표기."""

    def supports(self, asset: Asset) -> bool:
        return not self.supported_asset_types or asset.asset_type.value in self.supported_asset_types
