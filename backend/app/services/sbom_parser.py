"""
의존성 파일 파서 — npm · pip · Go modules · Dockerfile.

기존 lightweight_sbom은 finding 기반 합성. 여기는 의존성 선언 파일에서 직접 추출.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class Package:
    ecosystem: str
    name: str
    version: str | None
    source_file: str | None = None
    dev: bool = False


def detect_ecosystem(filename: str) -> str | None:
    base = filename.rsplit("/", 1)[-1].lower()
    if base in ("package.json", "package-lock.json"):
        return "npm"
    if base in ("requirements.txt", "pyproject.toml", "poetry.lock"):
        return "pypi"
    if base == "go.mod":
        return "go"
    if base == "dockerfile" or base.endswith(".dockerfile"):
        return "docker"
    return None


def parse_package_json(content: str, source_file: str | None = None) -> list[Package]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    out: list[Package] = []
    for k, v in (data.get("dependencies") or {}).items():
        out.append(Package(ecosystem="npm", name=k, version=str(v), source_file=source_file))
    for k, v in (data.get("devDependencies") or {}).items():
        out.append(Package(ecosystem="npm", name=k, version=str(v), source_file=source_file, dev=True))
    return out


def parse_package_lock_json(content: str, source_file: str | None = None) -> list[Package]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    out: list[Package] = []
    # v3 lockfile: packages dict (key는 node_modules/pkg)
    for path, meta in (data.get("packages") or {}).items():
        if path == "":
            continue
        name = path.split("node_modules/")[-1] if "node_modules/" in path else path
        version = (meta or {}).get("version")
        if name and version:
            out.append(
                Package(
                    ecosystem="npm",
                    name=name,
                    version=version,
                    source_file=source_file,
                    dev=bool((meta or {}).get("dev")),
                )
            )
    # v1/v2 fallback — dependencies (deprecated이지만 흔함)
    if not out:
        for name, meta in (data.get("dependencies") or {}).items():
            version = (meta or {}).get("version")
            if version:
                out.append(Package(ecosystem="npm", name=name, version=version, source_file=source_file))
    return out


_REQ_LINE = re.compile(r"^([A-Za-z0-9_\-\.\[\]]+)\s*([=<>!~]+)\s*([^\s,;]+)")


def parse_requirements_txt(content: str, source_file: str | None = None) -> list[Package]:
    out: list[Package] = []
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):  # -r other.txt 등 skip
            continue
        m = _REQ_LINE.match(line)
        if m:
            out.append(
                Package(ecosystem="pypi", name=m.group(1), version=m.group(3), source_file=source_file)
            )
        else:
            # 버전 없이 패키지만 (== 없이)
            name = line.split()[0]
            if re.match(r"^[A-Za-z0-9_\-\.]+$", name):
                out.append(Package(ecosystem="pypi", name=name, version=None, source_file=source_file))
    return out


_GO_REQUIRE_LINE = re.compile(r"^\s*([^\s]+)\s+v?([^\s]+)")


def parse_go_mod(content: str, source_file: str | None = None) -> list[Package]:
    out: list[Package] = []
    in_block = False
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("require ("):
            in_block = True
            continue
        if in_block and line == ")":
            in_block = False
            continue
        if in_block:
            m = _GO_REQUIRE_LINE.match(line)
            if m:
                out.append(
                    Package(ecosystem="go", name=m.group(1), version=m.group(2), source_file=source_file)
                )
        elif line.startswith("require "):
            m = _GO_REQUIRE_LINE.match(line[len("require "):])
            if m:
                out.append(
                    Package(ecosystem="go", name=m.group(1), version=m.group(2), source_file=source_file)
                )
    return out


_DOCKER_FROM = re.compile(r"^FROM\s+(?:--platform=[^\s]+\s+)?([^\s:]+)(?::([^\s@]+))?", re.IGNORECASE)


def parse_dockerfile(content: str, source_file: str | None = None) -> list[Package]:
    out: list[Package] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _DOCKER_FROM.match(line)
        if m:
            out.append(
                Package(
                    ecosystem="docker",
                    name=m.group(1),
                    version=m.group(2),  # 태그 없으면 None
                    source_file=source_file,
                )
            )
    return out


def parse(content: str, filename: str) -> tuple[str | None, list[Package]]:
    """filename으로 ecosystem 감지 후 알맞은 파서 실행."""
    base = filename.rsplit("/", 1)[-1].lower()
    eco = detect_ecosystem(filename)
    if eco is None:
        return None, []
    if base == "package.json":
        return eco, parse_package_json(content, filename)
    if base == "package-lock.json":
        return eco, parse_package_lock_json(content, filename)
    if base == "requirements.txt":
        return eco, parse_requirements_txt(content, filename)
    if base == "go.mod":
        return eco, parse_go_mod(content, filename)
    if base == "dockerfile" or base.endswith(".dockerfile"):
        return eco, parse_dockerfile(content, filename)
    return eco, []
