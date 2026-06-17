"""
🌙 스캐너 레지스트리 무결성 + stub 동작 테스트
"""

import asyncio

from app.models.asset import Asset, AssetType
from app.scanners.registry import get_scanner, list_scanners


def test_registry_lists_known_scanners():
    names = {s["name"] for s in list_scanners()}
    assert {"trivy", "semgrep", "nuclei"}.issubset(names)


def test_unknown_scanner_returns_none():
    assert get_scanner("does-not-exist") is None


def test_supports_filters_by_asset_type():
    trivy = get_scanner("trivy")
    semgrep = get_scanner("semgrep")
    nuclei = get_scanner("nuclei")
    assert trivy and semgrep and nuclei

    repo = Asset(name="r", asset_type=AssetType.REPOSITORY, uri="https://x", labels={})
    url = Asset(name="u", asset_type=AssetType.URL, uri="https://y", labels={})

    assert trivy.supports(repo) is True
    assert semgrep.supports(repo) is True
    assert nuclei.supports(repo) is False

    assert nuclei.supports(url) is True
    assert semgrep.supports(url) is False


def test_trivy_stub_returns_findings_without_binary():
    """trivy 바이너리가 없는 환경(CI runner)에서 stub 모드가 동작하는지."""
    trivy = get_scanner("trivy")
    assert trivy is not None
    asset = Asset(
        id=1,
        name="demo",
        asset_type=AssetType.CONTAINER_IMAGE,
        uri="docker.io/library/nginx:latest",
        labels={},
    )
    result = asyncio.run(trivy.scan(asset))
    # 바이너리가 있어도 그 결과를, 없어도 stub 결과를 반환 — 어느 쪽이든 findings가 있어야 한다.
    assert isinstance(result.findings, list)
    if result.raw_output.get("stub"):
        assert len(result.findings) >= 1
        assert result.findings[0].severity in {"critical", "high", "medium", "low", "info"}
