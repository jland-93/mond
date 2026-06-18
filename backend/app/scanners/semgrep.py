"""
Semgrep 어댑터 — 정적 코드 분석 (SAST)
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


class SemgrepAdapter(ScannerAdapter):
    name = "semgrep"
    supported_asset_types = (AssetType.REPOSITORY.value,)

    async def scan(self, asset: Asset) -> ScanResult:
        binary = shutil.which(settings.SCANNER_SEMGREP_BIN or "semgrep")
        if not binary:
            return self._stub_result(asset)

        cmd = [binary, "--config", "p/ci", "--json", "--quiet", asset.uri]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        except FileNotFoundError as exc:
            return ScanResult(findings=[], raw_output={}, error=str(exc))

        if proc.returncode not in (0, 1):  # 1 = findings present
            return ScanResult(
                findings=[],
                raw_output={"stderr": stderr.decode(errors="ignore")},
                error=f"semgrep exit {proc.returncode}",
            )

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            return ScanResult(findings=[], raw_output={"stdout": stdout.decode(errors="ignore")}, error=str(exc))

        return ScanResult(findings=list(self._parse(data)), raw_output=data)

    def _parse(self, data: dict):
        for r in data.get("results", []):
            sev = (r.get("extra", {}).get("severity") or "info").lower()
            yield RawFinding(
                rule_id=r.get("check_id", "UNKNOWN"),
                title=r.get("extra", {}).get("message", r.get("check_id", "Semgrep finding")),
                severity=sev,
                description=r.get("extra", {}).get("message"),
                location=f"{r.get('path', '')}:{r.get('start', {}).get('line', 0)}",
                references=r.get("extra", {}).get("references", []) or [],
                extra={"metadata": r.get("extra", {}).get("metadata", {})},
            )

    def _stub_result(self, asset: Asset) -> ScanResult:
        logger.warning("semgrep_binary_not_found", asset_id=asset.id, mode="stub")
        return ScanResult(
            findings=[
                RawFinding(
                    rule_id="python.lang.security.insecure-hashlib-md5",
                    title="[Demo] Insecure MD5 usage detected by Semgrep stub",
                    severity="medium",
                    description=(
                        "Semgrep 바이너리가 환경에 없어 데모 결과입니다. "
                        "`pip install semgrep` 후 다시 스캔하세요."
                    ),
                    location=f"{asset.uri}:demo.py:42",
                    references=["https://semgrep.dev"],
                    extra={"stub": True},
                ),
            ],
            raw_output={"stub": True, "asset_uri": asset.uri},
        )
