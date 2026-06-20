"""
Azure RBAC provider.

config 키:
  subscription_id : 필수
  scope           : 기본 "/subscriptions/{subscription_id}"
credentials_env_ref (Service Principal):
  tenant_id, client_id, client_secret  (각각 ENV 변수 이름)
"""

from __future__ import annotations

from app.models.iam import IAMIdentity, IAMSource, IdentityType, Permission

from .base import (
    AttachResult,
    FetchedIdentity,
    FetchedPermission,
    FetchResult,
    logger,
    resolve_credentials,
)


def _credential(source: IAMSource):
    try:
        from azure.identity import ClientSecretCredential  # type: ignore
    except ImportError:
        logger.warning("azure_identity_missing")
        return None
    creds = resolve_credentials(source)
    tenant = creds.get("tenant_id")
    client = creds.get("client_id")
    secret = creds.get("client_secret")
    if not (tenant and client and secret):
        return None
    try:
        return ClientSecretCredential(tenant_id=tenant, client_id=client, client_secret=secret)
    except Exception as exc:
        logger.warning("azure_credential_build_failed", error=str(exc))
        return None


def _scope(source: IAMSource) -> str:
    cfg = source.config or {}
    if cfg.get("scope"):
        return cfg["scope"]
    sub = cfg.get("subscription_id", "")
    return f"/subscriptions/{sub}" if sub else ""


def fetch(source: IAMSource) -> FetchResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return _stub("missing subscription_id")

    cred = _credential(source)
    if cred is None:
        return _stub()

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return _stub()

    identities: list[FetchedIdentity] = []
    permissions: list[FetchedPermission] = []
    scope = _scope(source)
    try:
        client = AuthorizationManagementClient(cred, subscription_id=sub)
        # 1) 현재 role assignments → 사용된 principal들을 identity로 (Graph API 없이 Azure AD 사용자 직접 조회 불가)
        seen: set[str] = set()
        for ra in client.role_assignments.list_for_scope(scope=scope):
            pid = ra.principal_id
            if not pid or pid in seen:
                continue
            seen.add(pid)
            ptype_str = (ra.principal_type or "user").lower()
            itype = (
                IdentityType.GROUP if ptype_str == "group"
                else IdentityType.SERVICE_ACCOUNT if "service" in ptype_str
                else IdentityType.USER
            )
            identities.append(
                FetchedIdentity(
                    identity_type=itype,
                    name=pid,
                    external_id=pid,
                    attributes={"principal_type": ra.principal_type or "User"},
                )
            )

        # 2) 사용 가능한 builtin roleDefinitions
        for rd in client.role_definitions.list(scope=scope, filter="type eq 'BuiltInRole'"):
            risk = (
                "admin" if "owner" in (rd.role_name or "").lower() or "administrator" in (rd.role_name or "").lower()
                else "write" if "contributor" in (rd.role_name or "").lower()
                else "read"
            )
            permissions.append(
                FetchedPermission(
                    name=rd.role_name or rd.id or "",
                    external_id=rd.id,
                    description=rd.description or None,
                    risk_hint=risk,
                )
            )
    except Exception as exc:
        logger.warning("azure_iam_import_failed", error=str(exc))
        return FetchResult(identities=[], permissions=[], error=str(exc))

    return FetchResult(identities=identities, permissions=permissions)


def attach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return AttachResult(success=False, detail={"error": "missing subscription_id"})

    cred = _credential(source)
    if cred is None:
        return AttachResult(success=True, detail={"stub": True, "note": "Azure 자격 미설정 — DB만 갱신"})

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "azure-mgmt-authorization not installed"})

    scope = _scope(source)
    principal_id = identity.external_id or identity.name
    role_def_id = permission.external_id or permission.name

    try:
        import uuid
        client = AuthorizationManagementClient(cred, subscription_id=sub)

        # 멱등성 — 동일 scope/principal/role 조합이 이미 있으면 그대로 success
        for ra in client.role_assignments.list_for_scope(scope=scope):
            if ra.principal_id == principal_id and ra.role_definition_id == role_def_id:
                return AttachResult(
                    success=True,
                    detail={
                        "assignment_name": ra.name,
                        "scope": scope,
                        "already": True,
                    },
                )

        assignment_name = str(uuid.uuid4())
        client.role_assignments.create(
            scope=scope,
            role_assignment_name=assignment_name,
            parameters={
                "properties": {
                    "role_definition_id": role_def_id,
                    "principal_id": principal_id,
                }
            },
        )
        return AttachResult(success=True, detail={"assignment_name": assignment_name, "scope": scope})
    except Exception as exc:
        msg = str(exc)
        # Azure가 race로 RoleAssignmentExists를 반환하면 success로 흡수
        if "RoleAssignmentExists" in msg or "already exists" in msg.lower():
            return AttachResult(
                success=True,
                detail={"scope": scope, "already": True, "raced": True},
            )
        return AttachResult(success=False, detail={"error": msg})


def detach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return AttachResult(success=False, detail={"error": "missing subscription_id"})

    cred = _credential(source)
    if cred is None:
        return AttachResult(success=True, detail={"stub": True, "note": "Azure 자격 미설정 — DB만 갱신"})

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "azure-mgmt-authorization not installed"})

    scope = _scope(source)
    principal_id = identity.external_id or identity.name
    role_def_id = permission.external_id or permission.name

    try:
        client = AuthorizationManagementClient(cred, subscription_id=sub)
        # 해당 (principal, role) 쌍의 모든 assignment 삭제
        deleted = 0
        for ra in client.role_assignments.list_for_scope(scope=scope):
            if ra.principal_id == principal_id and ra.role_definition_id == role_def_id:
                client.role_assignments.delete_by_id(role_assignment_id=ra.id)
                deleted += 1
        return AttachResult(success=deleted > 0, detail={"deleted": deleted, "scope": scope})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})


def _stub(reason: str | None = None) -> FetchResult:
    return FetchResult(
        stub=True,
        error=reason,
        identities=[
            FetchedIdentity(identity_type=IdentityType.USER, name="00000000-0000-0000-0000-000000000001", external_id="00000000-0000-0000-0000-000000000001", attributes={"principal_type": "User"}),
            FetchedIdentity(identity_type=IdentityType.SERVICE_ACCOUNT, name="00000000-0000-0000-0000-000000000002", external_id="00000000-0000-0000-0000-000000000002", attributes={"principal_type": "ServicePrincipal"}),
        ],
        permissions=[
            FetchedPermission(name="Reader", external_id="/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7", risk_hint="read", description="View all resources"),
            FetchedPermission(name="Contributor", external_id="/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c", risk_hint="write", description="Manage everything except access"),
            FetchedPermission(name="Owner", external_id="/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635", risk_hint="admin", description="Full access incl. role assignment"),
        ],
    )
