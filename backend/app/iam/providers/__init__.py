"""
IAM provider 어댑터 패키지.

외부에서는 dispatcher 함수만 호출:
- get_capabilities() -> list[dict]
- fetch_for(source) -> FetchResult
- attach_for(source, identity, permission) -> AttachResult
- detach_for(source, identity, permission) -> AttachResult

provider별 구현은 같은 패키지의 aws / k8s / ldap / gcp / azure 모듈에 있고,
공통 dataclasses와 helper는 base 모듈에 있다.
"""

from __future__ import annotations

from .base import (
    AttachResult,
    FetchResult,
    FetchedIdentity,
    FetchedPermission,
)
from .registry import (
    CAPABILITIES,
    attach_for,
    detach_for,
    fetch_for,
    get_capabilities,
)

__all__ = [
    "AttachResult",
    "FetchResult",
    "FetchedIdentity",
    "FetchedPermission",
    "CAPABILITIES",
    "attach_for",
    "detach_for",
    "fetch_for",
    "get_capabilities",
]
