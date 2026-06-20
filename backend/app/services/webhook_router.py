"""
Webhook push 이벤트 → 스캐너 자동 선택

GitHub push payload의 commits[*].{added,modified,removed} 파일 경로를 보고
어떤 스캐너가 가장 적합한지 결정. SAST 코드 변경 비중이 크면 semgrep,
IaC/Container/의존성 위주면 trivy.

자산 타입 호환성:
  REPOSITORY 자산은 trivy(filesystem mode) + semgrep 둘 다 가능.
  CONTAINER_IMAGE는 trivy만.
  URL 자산은 nuclei.

기본은 trivy fallback — 어댑터가 항상 있고, IaC/SCA/Container/Secrets
까지 단일 도구로 커버.
"""

from __future__ import annotations

from app.models.asset import Asset, AssetType
from app.scanners.registry import get_scanner

# 파일 경로/이름 패턴 → 카테고리. 가장 구체적인 패턴부터.
_SCA_NAMES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "poetry.lock", "uv.lock",
    "go.mod", "go.sum",
    "gemfile", "gemfile.lock",
    "cargo.toml", "cargo.lock",
    "pom.xml", "build.gradle", "build.gradle.kts",
}

_CONTAINER_NAMES = {"dockerfile"}
_CONTAINER_SUFFIXES = (".dockerfile",)

_IAC_SUFFIXES = (".tf", ".tfvars", ".hcl")
_IAC_NAMES = {"main.tf"}

_SAST_SUFFIXES = (
    ".py", ".go", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".rb",
    ".php", ".cs", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp",
)


def _classify(path: str) -> str:
    """파일 경로를 카테고리로 분류. unknown은 카운트에서 빠짐."""
    if not path:
        return "unknown"
    name = path.rsplit("/", 1)[-1].lower()
    if name in _SCA_NAMES:
        return "sca"
    if name in _CONTAINER_NAMES or name.endswith(_CONTAINER_SUFFIXES):
        return "container"
    if name in _IAC_NAMES or name.endswith(_IAC_SUFFIXES):
        return "iac"
    if name.endswith(_SAST_SUFFIXES):
        return "sast"
    return "unknown"


def categorize_files(files: list[str]) -> dict[str, int]:
    """파일 목록 → {sca, container, iac, sast, unknown} 카운트."""
    counts = {"sca": 0, "container": 0, "iac": 0, "sast": 0, "unknown": 0}
    for f in files:
        counts[_classify(f)] += 1
    return counts


def pick_scanner(asset: Asset, files: list[str]) -> tuple[str, dict]:
    """
    자산 + 변경 파일 목록 → 최적 스캐너 이름과 결정 근거.

    Returns: (scanner_name, decision)
      decision = {"reason": str, "counts": {...}, "fallback": bool}
    """
    counts = categorize_files(files)

    # 1) URL 자산 — DAST(nuclei) 외 선택지 없음.
    if asset.asset_type == AssetType.URL:
        if get_scanner("nuclei"):
            return "nuclei", {"reason": "URL asset → DAST", "counts": counts, "fallback": False}
        return "trivy", {"reason": "URL asset (nuclei 미설치) → trivy fallback", "counts": counts, "fallback": True}

    # 2) CONTAINER_IMAGE — trivy 외 선택지 없음.
    if asset.asset_type == AssetType.CONTAINER_IMAGE:
        return "trivy", {"reason": "container image → trivy", "counts": counts, "fallback": False}

    # 3) REPOSITORY — 변경 파일로 SAST vs SCA/IaC/Container 판단.
    #    SAST 변경이 다른 모든 카테고리 합보다 많으면 semgrep 우선.
    other = counts["sca"] + counts["container"] + counts["iac"]
    if counts["sast"] > 0 and counts["sast"] > other and get_scanner("semgrep"):
        return "semgrep", {
            "reason": f"SAST 파일 {counts['sast']}건이 다른 카테고리 합({other})보다 많음",
            "counts": counts,
            "fallback": False,
        }

    # 4) 명백한 SCA/Container/IaC 변경 → trivy
    if other > 0:
        return "trivy", {
            "reason": f"SCA/Container/IaC 변경 {other}건 — trivy 단일 도구로 커버",
            "counts": counts,
            "fallback": False,
        }

    # 5) 그 외(unknown만 변경되거나 파일 정보 자체가 없음) → trivy 기본
    return "trivy", {
        "reason": "변경 파일 분류 불가 — 기본 trivy",
        "counts": counts,
        "fallback": True,
    }


def files_from_push_payload(payload: dict) -> list[str]:
    """GitHub push payload의 commits에서 added/modified/removed 파일을 dedup."""
    seen: set[str] = set()
    for c in payload.get("commits") or []:
        for key in ("added", "modified", "removed"):
            for f in c.get(key) or []:
                if f and f not in seen:
                    seen.add(f)
    return list(seen)
