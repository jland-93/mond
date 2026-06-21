"""
CycloneDX SBOM — 헬퍼 함수 invariant.

cyclonedx_sbom 자체는 DB + GitHub 의존이라 통합 테스트가 어려워, purl/component/
vulnerability 변환 함수와 URI 파싱을 단위로 검증한다.
"""

from app.models.finding import Finding, FindingStatus, Severity
from app.services.reports import (
    _bom_ref,
    _parse_github_uri,
    _purl,
    _to_component,
    _to_vulnerability,
)
from app.services.sbom_parser import Package


def test_purl_npm_format():
    assert _purl("npm", "react", "18.3.1") == "pkg:npm/react@18.3.1"


def test_purl_pypi_format():
    assert _purl("pypi", "fastapi", "0.115.0") == "pkg:pypi/fastapi@0.115.0"


def test_purl_go_uses_golang_scheme():
    # CycloneDX/purl-spec에서 go는 golang scheme.
    assert _purl("go", "github.com/gin-gonic/gin", "v1.10.0").startswith("pkg:golang/")


def test_purl_docker_uses_oci_scheme():
    assert _purl("docker", "alpine", "3.20").startswith("pkg:oci/")


def test_purl_without_version_omits_at_sign():
    assert _purl("pypi", "requests", None) == "pkg:pypi/requests"


def test_bom_ref_unspecified_when_no_version():
    assert _bom_ref("npm", "left-pad", None) == "npm:left-pad@unspecified"


def test_to_component_carries_ecosystem_property():
    p = Package(ecosystem="npm", name="react", version="18.3.1", source_file="package.json")
    comp = _to_component(p)
    assert comp["type"] == "library"
    assert comp["name"] == "react"
    assert comp["version"] == "18.3.1"
    assert comp["purl"] == "pkg:npm/react@18.3.1"
    props = {x["name"]: x["value"] for x in comp["properties"]}
    assert props["mond:ecosystem"] == "npm"
    assert props["mond:source"] == "package.json"


def test_to_component_dev_dependency_flag():
    p = Package(ecosystem="npm", name="vitest", version="2.0", dev=True)
    comp = _to_component(p)
    props = {x["name"]: x["value"] for x in comp["properties"]}
    assert props.get("mond:dev") == "true"


def test_to_vulnerability_basic_shape():
    f = Finding(
        asset_id=1,
        rule_id="CVE-2024-1234",
        title="injection in foo",
        severity=Severity.CRITICAL,
        status=FindingStatus.NEW,
        scanner="trivy",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"],
        extra={},
        fingerprint="fp-abc",
    )
    v = _to_vulnerability(f)
    assert v["id"] == "CVE-2024-1234"
    assert v["bom-ref"] == "fp-abc"
    assert v["source"]["name"] == "trivy"
    assert v["ratings"][0]["severity"] == "critical"
    # CycloneDX 1.5: CVSSv3 method
    assert v["ratings"][0]["method"] == "CVSSv3"
    assert v["advisories"][0]["url"].startswith("https://nvd")


def test_to_vulnerability_semgrep_method_owasp():
    f = Finding(
        asset_id=1,
        rule_id="js.lang.security.audit.unsafe-formatstring",
        title="format string",
        severity=Severity.HIGH,
        status=FindingStatus.TRIAGED,
        scanner="semgrep",
        references=[],
        extra={},
        fingerprint="fp-sg",
    )
    v = _to_vulnerability(f)
    assert v["ratings"][0]["method"] == "OWASP"


def test_parse_github_uri_https():
    assert _parse_github_uri("https://github.com/jland-93/mond") == ("jland-93", "mond")


def test_parse_github_uri_with_dot_git_suffix():
    assert _parse_github_uri("https://github.com/jland-93/mond.git") == ("jland-93", "mond")


def test_parse_github_uri_non_github_returns_none():
    assert _parse_github_uri("https://gitlab.com/user/repo") is None


def test_parse_github_uri_none():
    assert _parse_github_uri(None) is None
