"""
Trivy 어댑터 — 컨테이너 이미지/IaC/SBOM 스캐너

trivy 바이너리가 PATH에 있으면 실제 호출하고, 없으면 stub 결과를 반환한다.
"""

from __future__ import annotations

import asyncio
import json
import shutil

from app.core.config import settings
from app.core.logging import get_logger
from app.models.asset import Asset, AssetType
from app.scanners.base import RawFinding, ScannerAdapter, ScanResult

logger = get_logger(__name__)


class TrivyAdapter(ScannerAdapter):
    name = "trivy"
    supported_asset_types = (
        AssetType.CONTAINER_IMAGE.value,
        AssetType.REPOSITORY.value,
        AssetType.CLOUD_RESOURCE.value,
    )

    async def scan(self, asset: Asset) -> ScanResult:
        binary = shutil.which(settings.SCANNER_TRIVY_BIN or "trivy")
        if not binary:
            return self._stub_result(asset)

        target = asset.uri
        cmd = [binary, "image" if asset.asset_type == AssetType.CONTAINER_IMAGE else "fs", "--format", "json", "--quiet", target]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        except FileNotFoundError as exc:
            return ScanResult(findings=[], raw_output={}, error=str(exc))

        if proc.returncode and proc.returncode != 0:
            return ScanResult(
                findings=[],
                raw_output={"stderr": stderr.decode(errors="ignore")},
                error=f"trivy exit {proc.returncode}",
            )

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            return ScanResult(findings=[], raw_output={"stdout": stdout.decode(errors="ignore")}, error=str(exc))

        return ScanResult(findings=list(self._parse(data)), raw_output=data)

    def _parse(self, data: dict):
        for result in data.get("Results", []):
            target_path = result.get("Target", "")
            for vuln in result.get("Vulnerabilities", []) or []:
                yield RawFinding(
                    rule_id=vuln.get("VulnerabilityID", "UNKNOWN"),
                    title=vuln.get("Title") or vuln.get("VulnerabilityID", "Unknown vulnerability"),
                    severity=(vuln.get("Severity") or "info").lower(),
                    description=vuln.get("Description"),
                    location=f"{target_path}::{vuln.get('PkgName', '')}@{vuln.get('InstalledVersion', '')}",
                    references=vuln.get("References") or [],
                    extra={
                        "cvss": vuln.get("CVSS"),
                        "fixed_version": vuln.get("FixedVersion"),
                    },
                )

    def _stub_result(self, asset: Asset) -> ScanResult:
        """trivy 바이너리가 없을 때 OSS 사용자가 즉시 UI를 볼 수 있도록 데모 데이터 생성."""
        logger.warning("trivy_binary_not_found", asset_id=asset.id, mode="stub")
        return ScanResult(
            findings=[
                RawFinding(
                    rule_id="CVE-DEMO-0001",
                    title="[Demo] Vulnerable package detected by Trivy stub",
                    severity="high",
                    description=(
                        "Trivy 바이너리가 환경에 없어 데모 결과를 반환합니다. "
                        "`brew install aquasec/trivy/trivy` 후 다시 스캔하세요."
                    ),
                    location=asset.uri,
                    references=["https://aquasecurity.github.io/trivy/"],
                    extra={"stub": True},
                ),
            ],
            raw_output={"stub": True, "asset_uri": asset.uri},
        )
