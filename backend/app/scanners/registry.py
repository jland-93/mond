"""
스캐너 레지스트리 — 이름으로 어댑터를 조회한다.
"""

from app.scanners.base import ScannerAdapter
from app.scanners.nuclei import NucleiAdapter
from app.scanners.semgrep import SemgrepAdapter
from app.scanners.trivy import TrivyAdapter

_REGISTRY: dict[str, ScannerAdapter] = {}


def _register(adapter: ScannerAdapter) -> None:
    _REGISTRY[adapter.name] = adapter


_register(TrivyAdapter())
_register(SemgrepAdapter())
_register(NucleiAdapter())


def list_scanners() -> list[dict]:
    return [
        {"name": a.name, "asset_types": list(a.supported_asset_types)}
        for a in _REGISTRY.values()
    ]


def get_scanner(name: str) -> ScannerAdapter | None:
    return _REGISTRY.get(name.lower())
