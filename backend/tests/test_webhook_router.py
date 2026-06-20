"""
Webhook push → 스캐너 자동 선택 라우터 테스트
"""

from app.models.asset import Asset, AssetType
from app.services import webhook_router as wr


def _repo() -> Asset:
    return Asset(name="r", asset_type=AssetType.REPOSITORY, uri="https://github.com/x/y")


def _image() -> Asset:
    return Asset(name="i", asset_type=AssetType.CONTAINER_IMAGE, uri="docker.io/x/y:tag")


def _url() -> Asset:
    return Asset(name="u", asset_type=AssetType.URL, uri="https://example.com")


def test_classify_basics():
    assert wr._classify("api/foo.py") == "sast"
    assert wr._classify("web/main.go") == "sast"
    assert wr._classify("Dockerfile") == "container"
    assert wr._classify("services/api.dockerfile") == "container"
    assert wr._classify("infra/main.tf") == "iac"
    assert wr._classify("vars.tfvars") == "iac"
    assert wr._classify("backend/requirements.txt") == "sca"
    assert wr._classify("frontend/package.json") == "sca"
    assert wr._classify("README.md") == "unknown"


def test_categorize_counts():
    c = wr.categorize_files([
        "src/a.py", "src/b.py", "src/c.go",
        "Dockerfile",
        "requirements.txt",
        "docs/readme.md",
    ])
    assert c == {"sast": 3, "container": 1, "iac": 0, "sca": 1, "unknown": 1}


def test_files_from_push_payload_dedup():
    payload = {
        "commits": [
            {"added": ["a.py"], "modified": ["b.py"], "removed": []},
            {"added": [], "modified": ["b.py", "Dockerfile"], "removed": ["old.go"]},
        ]
    }
    files = wr.files_from_push_payload(payload)
    assert set(files) == {"a.py", "b.py", "Dockerfile", "old.go"}


def test_url_asset_routes_to_nuclei_or_fallback():
    scanner, decision = wr.pick_scanner(_url(), [])
    # nuclei 등록되어 있으면 nuclei, 아니면 trivy fallback
    assert scanner in ("nuclei", "trivy")
    assert "URL" in decision["reason"]


def test_container_image_always_trivy():
    scanner, decision = wr.pick_scanner(_image(), ["src/anything.py"])
    assert scanner == "trivy"
    assert "container" in decision["reason"].lower()


def test_repo_sast_dominant_routes_to_semgrep():
    files = ["src/a.py", "src/b.py", "src/c.py", "Dockerfile"]
    scanner, decision = wr.pick_scanner(_repo(), files)
    assert scanner == "semgrep"
    assert decision["counts"]["sast"] == 3
    assert decision["counts"]["container"] == 1


def test_repo_sca_routes_to_trivy():
    files = ["requirements.txt", "go.mod", "src/a.py"]
    scanner, decision = wr.pick_scanner(_repo(), files)
    # SAST=1, other=2 → trivy
    assert scanner == "trivy"
    assert "trivy" in decision["reason"].lower() or "SCA" in decision["reason"]


def test_repo_no_known_files_fallback_trivy():
    scanner, decision = wr.pick_scanner(_repo(), ["docs/CHANGES.md", "README.md"])
    assert scanner == "trivy"
    assert decision["fallback"] is True


def test_repo_empty_files_fallback_trivy():
    scanner, decision = wr.pick_scanner(_repo(), [])
    assert scanner == "trivy"
    assert decision["fallback"] is True
