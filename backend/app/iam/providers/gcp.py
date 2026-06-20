"""
Google Cloud IAM provider.

config 키:
  project_id    : 필수. 예 "my-project-123"
credentials_env_ref:
  google_application_credentials : ENV name (예 "GOOGLE_APPLICATION_CREDENTIALS")
                                   → 서비스 계정 키 JSON 파일 경로
  google_credentials_json        : ENV name → JSON 문자열을 임시 파일로 풀어 사용

fetch 모델:
  identities  = 프로젝트 IAM policy의 모든 member들 (user:..., group:..., serviceAccount:...)
  permissions = predefined + custom roles (project scope)
"""

from __future__ import annotations

import os as _os

from app.models.iam import IAMIdentity, IAMSource, IdentityType, Permission

from .base import (
    AttachResult,
    FetchedIdentity,
    FetchedPermission,
    FetchResult,
    logger,
    resolve_credentials,
)


def _credentials_path(source: IAMSource) -> str | None:
    creds = resolve_credentials(source)
    p = creds.get("google_application_credentials")
    if p:
        return p
    json_str = creds.get("google_credentials_json")
    if json_str:
        import tempfile
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        fh.write(json_str)
        fh.flush()
        fh.close()
        return fh.name
    return None


def fetch(source: IAMSource) -> FetchResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return _stub("missing project_id")

    cred_path = _credentials_path(source)
    if not cred_path:
        return _stub()

    try:
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import iam_admin_v1, resourcemanager_v3  # type: ignore
        from google.iam.v1 import iam_policy_pb2  # type: ignore
    except ImportError:
        logger.warning("gcp_sdk_missing")
        return _stub()

    identities: list[FetchedIdentity] = []
    permissions: list[FetchedPermission] = []
    try:
        projects = resourcemanager_v3.ProjectsClient()
        resource = f"projects/{project_id}"
        policy = projects.get_iam_policy(request=iam_policy_pb2.GetIamPolicyRequest(resource=resource))

        seen_members: set[str] = set()
        for binding in policy.bindings:
            for m in binding.members:
                if m in seen_members:
                    continue
                seen_members.add(m)
                kind, _, ident = m.partition(":")
                itype = (
                    IdentityType.USER if kind == "user"
                    else IdentityType.GROUP if kind == "group"
                    else IdentityType.SERVICE_ACCOUNT if kind == "serviceAccount"
                    else IdentityType.USER
                )
                identities.append(
                    FetchedIdentity(
                        identity_type=itype,
                        name=ident or m,
                        external_id=m,
                        attributes={"member_type": kind},
                    )
                )

        # 프로젝트 사용 가능한 role 목록 (custom + predefined 일부)
        roles_client = iam_admin_v1.IAMClient()
        # custom roles (프로젝트 자체)
        try:
            for r in roles_client.list_roles(parent=resource):
                permissions.append(
                    FetchedPermission(
                        name=r.title or r.name,
                        external_id=r.name,
                        description=r.description or None,
                        risk_hint="admin" if "owner" in (r.name or "").lower() else "write",
                    )
                )
        except Exception:
            pass
        # 자주 쓰는 predefined roles 고정 노출 (전체 목록은 수천 개라 너무 큼)
        for role_id, risk in [
            ("roles/viewer", "read"),
            ("roles/editor", "write"),
            ("roles/owner", "admin"),
            ("roles/iam.securityReviewer", "read"),
            ("roles/storage.objectViewer", "read"),
            ("roles/storage.admin", "admin"),
        ]:
            permissions.append(
                FetchedPermission(
                    name=role_id,
                    external_id=role_id,
                    description=f"GCP predefined role · {role_id}",
                    risk_hint=risk,
                )
            )
    except Exception as exc:
        logger.warning("gcp_iam_import_failed", error=str(exc))
        return FetchResult(identities=[], permissions=[], error=str(exc))

    return FetchResult(identities=identities, permissions=permissions)


# IAM policy는 다른 클라이언트가 동시에 수정할 수 있어 etag 충돌이 가끔 난다.
# read-modify-write를 짧은 backoff로 최대 3회 재시도.
_MAX_RETRIES = 3
# etag mismatch · ABORTED는 GCP가 이렇게 알려준다.
_RETRYABLE_HINTS = ("aborted", "etag", "concurrent", "conflict")


def _normalize_member(identity: IAMIdentity) -> str:
    """member는 'user:alice@corp.com' 같이 prefix가 있어야 한다.
    external_id에 이미 prefix가 있으면 그대로, 아니면 identity_type에 따라 prefix 추가."""
    raw = identity.external_id or identity.name
    if not raw:
        return ""
    if ":" in raw:
        return raw
    prefix_map = {
        IdentityType.USER: "user",
        IdentityType.GROUP: "group",
        IdentityType.SERVICE_ACCOUNT: "serviceAccount",
    }
    return f"{prefix_map.get(identity.identity_type, 'user')}:{raw}"


def attach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return AttachResult(success=False, detail={"error": "missing project_id"})

    cred_path = _credentials_path(source)
    if not cred_path:
        return AttachResult(success=True, detail={"stub": True, "note": "GCP 자격 미설정 — DB만 갱신"})

    try:
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import resourcemanager_v3  # type: ignore
        from google.iam.v1 import iam_policy_pb2, policy_pb2  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "google-cloud SDK not installed"})

    member = _normalize_member(identity)
    role = permission.external_id or permission.name
    if not (member and role):
        return AttachResult(success=False, detail={"error": "missing member/role"})

    resource = f"projects/{project_id}"

    last_error: str | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            projects = resourcemanager_v3.ProjectsClient()
            policy = projects.get_iam_policy(
                request=iam_policy_pb2.GetIamPolicyRequest(resource=resource)
            )
            target = next((b for b in policy.bindings if b.role == role), None)
            if target is not None and member in target.members:
                # 이미 부여됨 — 멱등성 success
                return AttachResult(
                    success=True,
                    detail={"resource": resource, "role": role, "member": member, "already": True},
                )
            if target is None:
                policy.bindings.append(policy_pb2.Binding(role=role, members=[member]))
            else:
                target.members.append(member)
            projects.set_iam_policy(
                request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy)
            )
            return AttachResult(
                success=True,
                detail={"resource": resource, "role": role, "member": member, "attempt": attempt},
            )
        except Exception as exc:
            msg = str(exc).lower()
            last_error = str(exc)
            if attempt < _MAX_RETRIES and any(h in msg for h in _RETRYABLE_HINTS):
                logger.info("gcp_iam_retry", attempt=attempt, error=last_error[:200])
                continue
            return AttachResult(success=False, detail={"error": last_error, "attempt": attempt})
    return AttachResult(success=False, detail={"error": last_error or "unknown", "attempt": _MAX_RETRIES})


def detach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return AttachResult(success=False, detail={"error": "missing project_id"})

    cred_path = _credentials_path(source)
    if not cred_path:
        return AttachResult(success=True, detail={"stub": True, "note": "GCP 자격 미설정 — DB만 갱신"})

    try:
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import resourcemanager_v3  # type: ignore
        from google.iam.v1 import iam_policy_pb2  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "google-cloud SDK not installed"})

    member = _normalize_member(identity)
    role = permission.external_id or permission.name
    resource = f"projects/{project_id}"

    last_error: str | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            projects = resourcemanager_v3.ProjectsClient()
            policy = projects.get_iam_policy(
                request=iam_policy_pb2.GetIamPolicyRequest(resource=resource)
            )
            target = next((b for b in policy.bindings if b.role == role), None)
            if target is None or member not in target.members:
                # 이미 없음 — 멱등성 success
                return AttachResult(
                    success=True,
                    detail={"resource": resource, "role": role, "member": member, "already_absent": True},
                )
            target.members.remove(member)
            # binding이 비면 제거 (GCP 정책상 빈 binding은 거부될 수 있음)
            if not target.members:
                policy.bindings.remove(target)
            projects.set_iam_policy(
                request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy)
            )
            return AttachResult(
                success=True,
                detail={"resource": resource, "role": role, "member": member, "attempt": attempt},
            )
        except Exception as exc:
            msg = str(exc).lower()
            last_error = str(exc)
            if attempt < _MAX_RETRIES and any(h in msg for h in _RETRYABLE_HINTS):
                logger.info("gcp_iam_retry", attempt=attempt, error=last_error[:200])
                continue
            return AttachResult(success=False, detail={"error": last_error, "attempt": attempt})
    return AttachResult(success=False, detail={"error": last_error or "unknown", "attempt": _MAX_RETRIES})


def _stub(reason: str | None = None) -> FetchResult:
    return FetchResult(
        stub=True,
        error=reason,
        identities=[
            FetchedIdentity(identity_type=IdentityType.USER, name="alice@corp.com", external_id="user:alice@corp.com"),
            FetchedIdentity(identity_type=IdentityType.SERVICE_ACCOUNT, name="ci-runner", external_id="serviceAccount:ci-runner@demo.iam.gserviceaccount.com"),
            FetchedIdentity(identity_type=IdentityType.GROUP, name="devops@corp.com", external_id="group:devops@corp.com"),
        ],
        permissions=[
            FetchedPermission(name="roles/viewer", external_id="roles/viewer", risk_hint="read", description="GCP predefined role · viewer"),
            FetchedPermission(name="roles/editor", external_id="roles/editor", risk_hint="write", description="GCP predefined role · editor"),
            FetchedPermission(name="roles/owner", external_id="roles/owner", risk_hint="admin", description="GCP predefined role · owner"),
            FetchedPermission(name="roles/storage.admin", external_id="roles/storage.admin", risk_hint="admin", description="GCP storage admin"),
        ],
    )
