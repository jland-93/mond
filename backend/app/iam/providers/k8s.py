"""
Kubernetes RBAC provider — kubeconfig 또는 in-cluster ServiceAccount.

자격증명 우선순위:
  1) credentials_env_ref.kubeconfig_path → ENV 변수에 담긴 kubeconfig 파일 경로
  2) credentials_env_ref.kubeconfig → ENV 변수에 담긴 kubeconfig YAML 문자열(임시 파일로 풀어서 사용)
  3) in-cluster ServiceAccount (Pod 안에서 자동 마운트되는 token)
  4) 위 셋 다 없으면 stub

config 키:
  - namespace: RoleBinding 범위 (기본 'default'). 비우거나 '*' → ClusterRoleBinding 사용
  - context:   kubeconfig multi-cluster일 때 선택
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


def _clients(source: IAMSource):
    """kubernetes RBAC/Core API 클라이언트 튜플. 자격 미설정/SDK 미설치면 None 반환."""
    try:
        from kubernetes import client, config  # type: ignore
    except ImportError:
        logger.warning("kubernetes_sdk_missing")
        return None

    creds = resolve_credentials(source)
    cfg = source.config or {}
    context = cfg.get("context") or None

    kubeconfig_path = creds.get("kubeconfig_path")
    kubeconfig_yaml = creds.get("kubeconfig")
    try:
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
        elif kubeconfig_yaml:
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
                fh.write(kubeconfig_yaml)
                fh.flush()
                config.load_kube_config(config_file=fh.name, context=context)
        else:
            # in-cluster (Pod의 /var/run/secrets/kubernetes.io/serviceaccount)
            config.load_incluster_config()
    except Exception as exc:
        logger.warning("k8s_load_config_failed", error=str(exc))
        return None

    return client.RbacAuthorizationV1Api(), client.CoreV1Api()


def fetch(source: IAMSource) -> FetchResult:
    pair = _clients(source)
    if pair is None:
        return _stub()
    rbac, core = pair
    cfg = source.config or {}
    ns = (cfg.get("namespace") or "").strip()
    cluster_scope = (not ns) or ns == "*"

    identities: list[FetchedIdentity] = []
    permissions: list[FetchedPermission] = []
    try:
        # 1) ServiceAccount → identity (service_account)
        sas = core.list_service_account_for_all_namespaces().items if cluster_scope else core.list_namespaced_service_account(ns).items
        for sa in sas:
            identities.append(
                FetchedIdentity(
                    identity_type=IdentityType.SERVICE_ACCOUNT,
                    name=f"{sa.metadata.namespace}:{sa.metadata.name}",
                    external_id=f"serviceaccount/{sa.metadata.namespace}/{sa.metadata.name}",
                    attributes={"namespace": sa.metadata.namespace},
                )
            )

        # 2) ClusterRole / Role → permission
        cluster_roles = rbac.list_cluster_role().items
        for cr in cluster_roles:
            risk = _risk_of(cr.rules or [])
            permissions.append(
                FetchedPermission(
                    name=f"ClusterRole/{cr.metadata.name}",
                    external_id=f"clusterrole/{cr.metadata.name}",
                    description=_rules_summary(cr.rules or []),
                    risk_hint=risk,
                    attributes={"scope": "cluster"},
                )
            )
        roles = rbac.list_role_for_all_namespaces().items if cluster_scope else rbac.list_namespaced_role(ns).items
        for r in roles:
            risk = _risk_of(r.rules or [])
            permissions.append(
                FetchedPermission(
                    name=f"Role/{r.metadata.namespace}/{r.metadata.name}",
                    external_id=f"role/{r.metadata.namespace}/{r.metadata.name}",
                    description=_rules_summary(r.rules or []),
                    risk_hint=risk,
                    attributes={"scope": "namespace", "namespace": r.metadata.namespace},
                )
            )
    except Exception as exc:
        logger.warning("k8s_iam_import_failed", error=str(exc))
        return FetchResult(identities=[], permissions=[], error=str(exc))

    return FetchResult(identities=identities, permissions=permissions)


def _risk_of(rules) -> str:
    """RBAC rules에서 권한 위험도 추정. verbs=['*'] 또는 resources=['*']에 'admin'."""
    has_wildcard = any("*" in (rl.verbs or []) or "*" in (rl.resources or []) for rl in rules)
    if has_wildcard:
        return "admin"
    write_verbs = {"create", "update", "patch", "delete", "deletecollection"}
    has_write = any(write_verbs & set(rl.verbs or []) for rl in rules)
    return "write" if has_write else "read"


def _rules_summary(rules) -> str:
    parts = []
    for rl in rules[:3]:
        verbs = ",".join(rl.verbs or [])
        res = ",".join(rl.resources or [])
        parts.append(f"{verbs} on {res}")
    return " · ".join(parts) or "no rules"


def attach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """RoleBinding(또는 ClusterRoleBinding) 생성으로 ServiceAccount에 Role/ClusterRole 부여."""
    pair = _clients(source)
    if pair is None:
        return AttachResult(success=True, detail={"stub": True, "note": "K8s 자격 미설정 — DB만 갱신"})
    rbac, _ = pair

    try:
        from kubernetes import client as kclient  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "kubernetes SDK not installed"})

    sa_ns, sa_name = _parse_sa(identity)
    if not sa_name:
        return AttachResult(success=False, detail={"error": "identity is not a ServiceAccount"})

    perm_ext = permission.external_id or ""
    binding_name = f"mond-{sa_name}-{permission.id}"

    try:
        if perm_ext.startswith("clusterrole/"):
            role_ref = kclient.V1RoleRef(api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=perm_ext.split("/", 1)[1])
            subj = kclient.RbacV1Subject(kind="ServiceAccount", name=sa_name, namespace=sa_ns)
            body = kclient.V1ClusterRoleBinding(metadata=kclient.V1ObjectMeta(name=binding_name), role_ref=role_ref, subjects=[subj])
            rbac.create_cluster_role_binding(body=body)
            return AttachResult(success=True, detail={"binding": "ClusterRoleBinding", "name": binding_name})
        if perm_ext.startswith("role/"):
            _, ns, role_name = perm_ext.split("/", 2)
            role_ref = kclient.V1RoleRef(api_group="rbac.authorization.k8s.io", kind="Role", name=role_name)
            subj = kclient.RbacV1Subject(kind="ServiceAccount", name=sa_name, namespace=sa_ns)
            body = kclient.V1RoleBinding(metadata=kclient.V1ObjectMeta(name=binding_name, namespace=ns), role_ref=role_ref, subjects=[subj])
            rbac.create_namespaced_role_binding(namespace=ns, body=body)
            return AttachResult(success=True, detail={"binding": "RoleBinding", "namespace": ns, "name": binding_name})
        return AttachResult(success=False, detail={"error": f"unknown permission external_id: {perm_ext}"})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})


def detach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    pair = _clients(source)
    if pair is None:
        return AttachResult(success=True, detail={"stub": True, "note": "K8s 자격 미설정 — DB만 갱신"})
    rbac, _ = pair

    sa_ns, sa_name = _parse_sa(identity)
    if not sa_name:
        return AttachResult(success=False, detail={"error": "identity is not a ServiceAccount"})

    perm_ext = permission.external_id or ""
    binding_name = f"mond-{sa_name}-{permission.id}"
    try:
        if perm_ext.startswith("clusterrole/"):
            rbac.delete_cluster_role_binding(name=binding_name)
            return AttachResult(success=True, detail={"deleted": "ClusterRoleBinding", "name": binding_name})
        if perm_ext.startswith("role/"):
            _, ns, _ = perm_ext.split("/", 2)
            rbac.delete_namespaced_role_binding(name=binding_name, namespace=ns)
            return AttachResult(success=True, detail={"deleted": "RoleBinding", "namespace": ns, "name": binding_name})
        return AttachResult(success=False, detail={"error": f"unknown permission external_id: {perm_ext}"})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})


def _parse_sa(identity: IAMIdentity) -> tuple[str, str]:
    """fetch가 만든 identity.name 형식 'namespace:sa_name'을 분해."""
    if identity.identity_type != IdentityType.SERVICE_ACCOUNT:
        return ("", "")
    if ":" in (identity.name or ""):
        ns, name = identity.name.split(":", 1)
        return (ns, name)
    return ("default", identity.name)


def _stub() -> FetchResult:
    return FetchResult(
        stub=True,
        identities=[
            FetchedIdentity(identity_type=IdentityType.SERVICE_ACCOUNT, name="default:app-runner", external_id="serviceaccount/default/app-runner"),
            FetchedIdentity(identity_type=IdentityType.SERVICE_ACCOUNT, name="kube-system:metrics", external_id="serviceaccount/kube-system/metrics"),
        ],
        permissions=[
            FetchedPermission(name="ClusterRole/view", external_id="clusterrole/view", risk_hint="read", description="get,list,watch on pods,services,deployments"),
            FetchedPermission(name="ClusterRole/edit", external_id="clusterrole/edit", risk_hint="write", description="create,update,delete on workloads"),
            FetchedPermission(name="ClusterRole/cluster-admin", external_id="clusterrole/cluster-admin", risk_hint="admin", description="* on *"),
        ],
    )
