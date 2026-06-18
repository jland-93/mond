"""
Nuclei 어댑터 — 템플릿 기반 동적 스캐너 (DAST)
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


class NucleiAdapter(ScannerAdapter):
    name = "nuclei"
    supported_asset_types = (AssetType.URL.value,)

    async def scan(self, asset: Asset) -> ScanResult:
        binary = shutil.which(settings.SCANNER_NUCLEI_BIN or "nuclei")
        if not binary:
            return self._stub_result(asset)

        cmd = [binary, "-u", asset.uri, "-jsonl", "-silent"]
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
                error=f"nuclei exit {proc.returncode}",
            )

        events: list[dict] = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        findings = [self._convert(e) for e in events]
        return ScanResult(findings=findings, raw_output={"events": events})

    def _convert(self, event: dict) -> RawFinding:
        info = event.get("info", {})
        return RawFinding(
            rule_id=event.get("template-id", "UNKNOWN"),
            title=info.get("name", event.get("template-id", "Nuclei finding")),
            severity=(info.get("severity") or "info").lower(),
            description=info.get("description"),
            location=event.get("matched-at") or event.get("host"),
            references=info.get("reference", []) or [],
            extra={"tags": info.get("tags", [])},
        )

    def _stub_result(self, asset: Asset) -> ScanResult:
        logger.warning("nuclei_binary_not_found", asset_id=asset.id, mode="stub")
        return ScanResult(
            findings=[
                RawFinding(
                    rule_id="http-missing-security-headers",
                    title="[Demo] Missing security headers detected by Nuclei stub",
                    severity="low",
                    description=(
                        "Nuclei 바이너리가 환경에 없어 데모 결과입니다. "
                        "`brew install nuclei` 후 다시 스캔하세요."
                    ),
                    location=asset.uri,
                    references=["https://docs.projectdiscovery.io/tools/nuclei"],
                    extra={"stub": True},
                ),
            ],
            raw_output={"stub": True, "asset_uri": asset.uri},
        )
