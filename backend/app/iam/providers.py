"""
IAM 프로바이더 어댑터 — AWS / mock

각 프로바이더는 (1) `import_identities_and_permissions(source)` 로 외부에서 데이터를 가져오고
(2) `attach(identity, permission)` 로 실제 권한을 부여한다.

자격증명이 없거나 외부 SDK 미설치 시 stub 결과를 반환해 OSS 사용자 UX를 보장한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.iam import IAMIdentity, IAMSource, IAMSourceKind, IdentityType, Permission

logger = get_logger(__name__)


@dataclass
class FetchedIdentity:
    identity_type: IdentityType
    name: str
    external_id: str | None = None
    attributes: dict | None = None


@dataclass
class FetchedPermission:
    name: str
    external_id: str | None = None
    description: str | None = None
    risk_hint: str | None = None
    attributes: dict | None = None


@dataclass
class FetchResult:
    identities: list[FetchedIdentity]
    permissions: list[FetchedPermission]
    stub: bool = False
    error: str | None = None


@dataclass
class AttachResult:
    success: bool
    detail: dict


def _resolve_credentials(source: IAMSource) -> dict[str, str]:
    """credentials_env_ref가 {"access_key_id": "AWS_ACCESS_KEY_ID"} 형태일 때 ENV에서 실값을 가져온다."""
    return {k: os.environ.get(v, "") for k, v in (source.credentials_env_ref or {}).items()}


# ── AWS provider ─────────────────────────────────────────────────
def fetch_aws(source: IAMSource) -> FetchResult:
    creds = _resolve_credentials(source)
    access_key = creds.get("access_key_id")
    secret_key = creds.get("secret_access_key")
    region = (source.config or {}).get("region", "us-east-1")

    if not access_key or not secret_key:
        return _aws_stub()

    try:
        import boto3
    except ImportError:
        logger.warning("boto3_missing")
        return _aws_stub()

    try:
        iam = boto3.client(
            "iam",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        users = iam.list_users().get("Users", [])
        roles = iam.list_roles().get("Roles", [])
        policies = iam.list_policies(Scope="AWS").get("Policies", []) + iam.list_policies(Scope="Local").get(
            "Policies", []
        )
    except Exception as exc:  # 자격 오류 / 권한 부족 등
        logger.warning("aws_iam_import_failed", error=str(exc))
        return FetchResult(identities=[], permissions=[], error=str(exc))

    identities: list[FetchedIdentity] = []
    for u in users:
        identities.append(
            FetchedIdentity(
                identity_type=IdentityType.USER,
                name=u.get("UserName", ""),
                external_id=u.get("Arn"),
                attributes={"created": str(u.get("CreateDate"))},
            )
        )
    for r in roles:
        identities.append(
            FetchedIdentity(
                identity_type=IdentityType.ROLE,
                name=r.get("RoleName", ""),
                external_id=r.get("Arn"),
                attributes={"trust_policy": r.get("AssumeRolePolicyDocument")},
            )
        )

    perms: list[FetchedPermission] = []
    for p in policies:
        name = p.get("PolicyName", "")
        risk = "admin" if "Admin" in name else "write" if "FullAccess" in name else "read"
        perms.append(
            FetchedPermission(
                name=name,
                external_id=p.get("Arn"),
                description=p.get("Description"),
                risk_hint=risk,
                attributes={"is_attachable": p.get("IsAttachable", True)},
            )
        )

    return FetchResult(identities=identities, permissions=perms)


def attach_aws(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    creds = _resolve_credentials(source)
    access_key = creds.get("access_key_id")
    secret_key = creds.get("secret_access_key")
    region = (source.config or {}).get("region", "us-east-1")

    if not access_key or not secret_key:
        # 자격증명이 없는 데모 환경에서도 만료/회수 흐름을 보여주기 위해 success로 마킹.
        # 다만 실제 외부 IAM에는 적용되지 않았음을 detail.stub=True로 명시.
        return AttachResult(
            success=True,
            detail={
                "stub": True,
                "note": (
                    "AWS 자격증명이 없어 실제 attach_policy를 건너뛰고 DB 상태만 갱신했습니다. "
                    ".env에 AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY를 채우면 진짜 권한 부여까지 자동화됩니다."
                ),
            },
        )

    try:
        import boto3
    except ImportError:
        return AttachResult(success=False, detail={"error": "boto3 not installed"})

    iam = boto3.client(
        "iam",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    policy_arn = permission.external_id
    if not policy_arn:
        return AttachResult(success=False, detail={"error": "missing policy ARN"})

    try:
        if identity.identity_type == IdentityType.USER:
            iam.attach_user_policy(UserName=identity.name, PolicyArn=policy_arn)
        elif identity.identity_type == IdentityType.ROLE:
            iam.attach_role_policy(RoleName=identity.name, PolicyArn=policy_arn)
        else:
            return AttachResult(
                success=False,
                detail={"error": f"unsupported identity_type {identity.identity_type.value}"},
            )
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})

    return AttachResult(
        success=True,
        detail={
            "attached_at": "now",
            "identity": identity.name,
            "identity_type": identity.identity_type.value,
            "policy_arn": policy_arn,
        },
    )


def detach_aws(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """attach_aws의 역연산. 만료 시 자동 회수 + 수동 회수에 사용."""
    creds = _resolve_credentials(source)
    access_key = creds.get("access_key_id")
    secret_key = creds.get("secret_access_key")
    region = (source.config or {}).get("region", "us-east-1")

    if not access_key or not secret_key:
        return AttachResult(
            success=True,
            detail={
                "stub": True,
                "note": (
                    "AWS 자격증명이 없어 실제 detach_policy를 건너뛰고 DB 상태만 갱신했습니다."
                ),
            },
        )

    try:
        import boto3
    except ImportError:
        return AttachResult(success=False, detail={"error": "boto3 not installed"})

    iam = boto3.client(
        "iam",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    policy_arn = permission.external_id
    if not policy_arn:
        return AttachResult(success=False, detail={"error": "missing policy ARN"})

    try:
        if identity.identity_type == IdentityType.USER:
            iam.detach_user_policy(UserName=identity.name, PolicyArn=policy_arn)
        elif identity.identity_type == IdentityType.ROLE:
            iam.detach_role_policy(RoleName=identity.name, PolicyArn=policy_arn)
        else:
            return AttachResult(
                success=False,
                detail={"error": f"unsupported identity_type {identity.identity_type.value}"},
            )
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})

    return AttachResult(
        success=True,
        detail={
            "detached_at": "now",
            "identity": identity.name,
            "identity_type": identity.identity_type.value,
            "policy_arn": policy_arn,
        },
    )


def _aws_stub() -> FetchResult:
    return FetchResult(
        stub=True,
        identities=[
            FetchedIdentity(identity_type=IdentityType.USER, name="alice", external_id="arn:aws:iam::000000000000:user/alice"),
            FetchedIdentity(identity_type=IdentityType.USER, name="bob", external_id="arn:aws:iam::000000000000:user/bob"),
            FetchedIdentity(identity_type=IdentityType.ROLE, name="DeveloperRole", external_id="arn:aws:iam::000000000000:role/DeveloperRole"),
            FetchedIdentity(identity_type=IdentityType.ROLE, name="ReadOnlyRole", external_id="arn:aws:iam::000000000000:role/ReadOnlyRole"),
        ],
        permissions=[
            FetchedPermission(name="ReadOnlyAccess", external_id="arn:aws:iam::aws:policy/ReadOnlyAccess", risk_hint="read", description="모든 AWS 리소스 읽기"),
            FetchedPermission(name="AmazonS3FullAccess", external_id="arn:aws:iam::aws:policy/AmazonS3FullAccess", risk_hint="write", description="S3 모든 권한"),
            FetchedPermission(name="AdministratorAccess", external_id="arn:aws:iam::aws:policy/AdministratorAccess", risk_hint="admin", description="모든 권한"),
            FetchedPermission(name="AmazonEC2ReadOnlyAccess", external_id="arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess", risk_hint="read", description="EC2 읽기"),
        ],
    )


# ── Kubernetes provider ──────────────────────────────────────────
#
# 자격증명 우선순위:
#   1) credentials_env_ref.kubeconfig_path → ENV 변수에 담긴 kubeconfig 파일 경로
#   2) credentials_env_ref.kubeconfig → ENV 변수에 담긴 kubeconfig YAML 문자열(임시 파일로 풀어서 사용)
#   3) in-cluster ServiceAccount (Pod 안에서 자동 마운트되는 token)
#   4) 위 셋 다 없으면 stub
#
# config 키:
#   - namespace: RoleBinding 범위 (기본 'default'). 비우거나 '*' → ClusterRoleBinding 사용
#   - context:   kubeconfig multi-cluster일 때 선택
def _k8s_clients(source: IAMSource):
    """kubernetes RBAC/Core API 클라이언트 튜플. 자격 미설정/SDK 미설치면 None 반환."""
    try:
        from kubernetes import client, config  # type: ignore
    except ImportError:
        logger.warning("kubernetes_sdk_missing")
        return None

    creds = _resolve_credentials(source)
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


def fetch_k8s(source: IAMSource) -> FetchResult:
    pair = _k8s_clients(source)
    if pair is None:
        return _k8s_stub()
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
            risk = _k8s_risk_of(cr.rules or [])
            permissions.append(
                FetchedPermission(
                    name=f"ClusterRole/{cr.metadata.name}",
                    external_id=f"clusterrole/{cr.metadata.name}",
                    description=_k8s_rules_summary(cr.rules or []),
                    risk_hint=risk,
                    attributes={"scope": "cluster"},
                )
            )
        roles = rbac.list_role_for_all_namespaces().items if cluster_scope else rbac.list_namespaced_role(ns).items
        for r in roles:
            risk = _k8s_risk_of(r.rules or [])
            permissions.append(
                FetchedPermission(
                    name=f"Role/{r.metadata.namespace}/{r.metadata.name}",
                    external_id=f"role/{r.metadata.namespace}/{r.metadata.name}",
                    description=_k8s_rules_summary(r.rules or []),
                    risk_hint=risk,
                    attributes={"scope": "namespace", "namespace": r.metadata.namespace},
                )
            )
    except Exception as exc:
        logger.warning("k8s_iam_import_failed", error=str(exc))
        return FetchResult(identities=[], permissions=[], error=str(exc))

    return FetchResult(identities=identities, permissions=permissions)


def _k8s_risk_of(rules) -> str:
    """RBAC rules에서 권한 위험도 추정. verbs=['*'] 또는 resources=['*']에 'admin'."""
    has_wildcard = any("*" in (rl.verbs or []) or "*" in (rl.resources or []) for rl in rules)
    if has_wildcard:
        return "admin"
    write_verbs = {"create", "update", "patch", "delete", "deletecollection"}
    has_write = any(write_verbs & set(rl.verbs or []) for rl in rules)
    return "write" if has_write else "read"


def _k8s_rules_summary(rules) -> str:
    parts = []
    for rl in rules[:3]:
        verbs = ",".join(rl.verbs or [])
        res = ",".join(rl.resources or [])
        parts.append(f"{verbs} on {res}")
    return " · ".join(parts) or "no rules"


def attach_k8s(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """RoleBinding(또는 ClusterRoleBinding) 생성으로 ServiceAccount에 Role/ClusterRole 부여."""
    pair = _k8s_clients(source)
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


def detach_k8s(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    pair = _k8s_clients(source)
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
    """fetch_k8s가 만든 identity.name 형식 'namespace:sa_name'을 분해."""
    if identity.identity_type != IdentityType.SERVICE_ACCOUNT:
        return ("", "")
    if ":" in (identity.name or ""):
        ns, name = identity.name.split(":", 1)
        return (ns, name)
    return ("default", identity.name)


def _k8s_stub() -> FetchResult:
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


# ── LDAP / Active Directory provider (온프레미스 사내 디렉토리) ─────
#
# 자격증명:
#   credentials_env_ref.bind_dn       → ENV 변수에 담긴 bind DN
#   credentials_env_ref.bind_password → ENV 변수에 담긴 bind 비밀번호
#
# config 키:
#   server          : "ldaps://ad.corp.local" (TLS 권장)
#   base_dn         : "DC=corp,DC=local"
#   user_base_dn    : "CN=Users,DC=corp,DC=local"
#   group_base_dn   : "CN=Groups,DC=corp,DC=local"  (없으면 base_dn 사용)
#   user_filter     : 기본 "(objectClass=person)"
#   group_filter    : 기본 "(objectClass=group)"  — OpenLDAP은 "(objectClass=groupOfNames)"
#   user_id_attr    : 기본 "sAMAccountName" (AD) — OpenLDAP은 "uid"
#   group_id_attr   : 기본 "cn"
#   member_attr     : 기본 "member" — OpenLDAP은 "member" 또는 "uniqueMember"
def _ldap_connection(source: IAMSource):
    try:
        from ldap3 import Connection, Server, ALL  # type: ignore
    except ImportError:
        logger.warning("ldap3_sdk_missing")
        return None

    creds = _resolve_credentials(source)
    bind_dn = creds.get("bind_dn")
    bind_pw = creds.get("bind_password")
    server_uri = (source.config or {}).get("server")
    if not (server_uri and bind_dn and bind_pw):
        return None

    try:
        srv = Server(server_uri, get_info=ALL, use_ssl=server_uri.startswith("ldaps://"))
        conn = Connection(srv, user=bind_dn, password=bind_pw, auto_bind=True)
        return conn
    except Exception as exc:
        logger.warning("ldap_bind_failed", error=str(exc))
        return None


def fetch_ldap(source: IAMSource) -> FetchResult:
    conn = _ldap_connection(source)
    if conn is None:
        return _ldap_stub()

    cfg = source.config or {}
    base_dn = cfg.get("base_dn", "")
    user_base = cfg.get("user_base_dn") or base_dn
    group_base = cfg.get("group_base_dn") or base_dn
    user_filter = cfg.get("user_filter", "(objectClass=person)")
    group_filter = cfg.get("group_filter", "(objectClass=group)")
    user_id_attr = cfg.get("user_id_attr", "sAMAccountName")
    group_id_attr = cfg.get("group_id_attr", "cn")

    identities: list[FetchedIdentity] = []
    permissions: list[FetchedPermission] = []
    try:
        # 1) 사용자
        conn.search(user_base, user_filter, attributes=[user_id_attr, "mail", "displayName", "distinguishedName"])
        for e in conn.entries:
            uid = str(getattr(e, user_id_attr, "")).strip()
            if not uid:
                continue
            identities.append(
                FetchedIdentity(
                    identity_type=IdentityType.USER,
                    name=uid,
                    external_id=str(e.entry_dn),
                    attributes={"mail": str(getattr(e, "mail", "") or ""), "displayName": str(getattr(e, "displayName", "") or "")},
                )
            )

        # 2) 그룹 → permission으로 모델링 (그룹 멤버십 = 권한 부여)
        conn.search(group_base, group_filter, attributes=[group_id_attr, "description", "distinguishedName"])
        for e in conn.entries:
            gname = str(getattr(e, group_id_attr, "")).strip()
            if not gname:
                continue
            desc = str(getattr(e, "description", "") or "") or None
            risk = "admin" if any(k in gname.lower() for k in ("admin", "root", "domain admins")) else "write" if "ops" in gname.lower() else "read"
            permissions.append(
                FetchedPermission(
                    name=f"Group/{gname}",
                    external_id=str(e.entry_dn),
                    description=desc,
                    risk_hint=risk,
                )
            )
    except Exception as exc:
        logger.warning("ldap_search_failed", error=str(exc))
        try:
            conn.unbind()
        except Exception:
            pass
        return FetchResult(identities=[], permissions=[], error=str(exc))
    finally:
        try:
            conn.unbind()
        except Exception:
            pass
    return FetchResult(identities=identities, permissions=permissions)


def _ldap_member_attr(source: IAMSource) -> str:
    return (source.config or {}).get("member_attr", "member")


def attach_ldap(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """그룹 멤버십에 사용자 DN을 add → 권한 부여."""
    conn = _ldap_connection(source)
    if conn is None:
        return AttachResult(success=True, detail={"stub": True, "note": "LDAP 자격 미설정 — DB만 갱신"})

    try:
        from ldap3 import MODIFY_ADD  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "ldap3 not installed"})

    user_dn = identity.external_id
    group_dn = permission.external_id
    if not user_dn or not group_dn:
        return AttachResult(success=False, detail={"error": "missing DN(s)"})

    attr = _ldap_member_attr(source)
    try:
        ok = conn.modify(group_dn, {attr: [(MODIFY_ADD, [user_dn])]})
        detail = {"result": conn.result, "attr": attr}
        return AttachResult(success=bool(ok), detail=detail)
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})
    finally:
        try:
            conn.unbind()
        except Exception:
            pass


def detach_ldap(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    conn = _ldap_connection(source)
    if conn is None:
        return AttachResult(success=True, detail={"stub": True, "note": "LDAP 자격 미설정 — DB만 갱신"})

    try:
        from ldap3 import MODIFY_DELETE  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "ldap3 not installed"})

    user_dn = identity.external_id
    group_dn = permission.external_id
    if not user_dn or not group_dn:
        return AttachResult(success=False, detail={"error": "missing DN(s)"})

    attr = _ldap_member_attr(source)
    try:
        ok = conn.modify(group_dn, {attr: [(MODIFY_DELETE, [user_dn])]})
        return AttachResult(success=bool(ok), detail={"result": conn.result, "attr": attr})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})
    finally:
        try:
            conn.unbind()
        except Exception:
            pass


def _ldap_stub() -> FetchResult:
    return FetchResult(
        stub=True,
        identities=[
            FetchedIdentity(identity_type=IdentityType.USER, name="alice.kim", external_id="CN=Alice Kim,CN=Users,DC=corp,DC=local", attributes={"mail": "alice@corp.local"}),
            FetchedIdentity(identity_type=IdentityType.USER, name="bob.lee",   external_id="CN=Bob Lee,CN=Users,DC=corp,DC=local",   attributes={"mail": "bob@corp.local"}),
            FetchedIdentity(identity_type=IdentityType.USER, name="charlie",   external_id="CN=Charlie,CN=Users,DC=corp,DC=local",  attributes={"mail": "charlie@corp.local"}),
        ],
        permissions=[
            FetchedPermission(name="Group/Domain Admins",  external_id="CN=Domain Admins,CN=Users,DC=corp,DC=local",  risk_hint="admin", description="도메인 관리자"),
            FetchedPermission(name="Group/DevOps",         external_id="CN=DevOps,CN=Users,DC=corp,DC=local",         risk_hint="write", description="배포·인프라"),
            FetchedPermission(name="Group/Developers",     external_id="CN=Developers,CN=Users,DC=corp,DC=local",     risk_hint="write", description="개발자"),
            FetchedPermission(name="Group/VPN Users",      external_id="CN=VPN Users,CN=Users,DC=corp,DC=local",      risk_hint="read",  description="사내 VPN 접속"),
        ],
    )


# ── Google Cloud IAM provider ────────────────────────────────────
#
# config 키:
#   project_id    : 필수. 예 "my-project-123"
# credentials_env_ref:
#   google_application_credentials : ENV name (예 "GOOGLE_APPLICATION_CREDENTIALS")
#                                    → 서비스 계정 키 JSON 파일 경로
#   google_credentials_json        : ENV name → JSON 문자열을 임시 파일로 풀어 사용
#
# fetch 모델:
#   identities  = 프로젝트 IAM policy의 모든 member들 (user:..., group:..., serviceAccount:...)
#   permissions = predefined + custom roles (project scope)
def _gcp_credentials_path(source: IAMSource) -> str | None:
    creds = _resolve_credentials(source)
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


def fetch_gcp(source: IAMSource) -> FetchResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return _gcp_stub("missing project_id")

    cred_path = _gcp_credentials_path(source)
    if not cred_path:
        return _gcp_stub()

    try:
        import os as _os
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import resourcemanager_v3  # type: ignore
        from google.cloud import iam_admin_v1  # type: ignore
        from google.iam.v1 import iam_policy_pb2  # type: ignore
    except ImportError:
        logger.warning("gcp_sdk_missing")
        return _gcp_stub()

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


def attach_gcp(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return AttachResult(success=False, detail={"error": "missing project_id"})

    cred_path = _gcp_credentials_path(source)
    if not cred_path:
        return AttachResult(success=True, detail={"stub": True, "note": "GCP 자격 미설정 — DB만 갱신"})

    try:
        import os as _os
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import resourcemanager_v3  # type: ignore
        from google.iam.v1 import iam_policy_pb2, policy_pb2  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "google-cloud SDK not installed"})

    member = identity.external_id or identity.name
    role = permission.external_id or permission.name
    if not (member and role):
        return AttachResult(success=False, detail={"error": "missing member/role"})

    try:
        projects = resourcemanager_v3.ProjectsClient()
        resource = f"projects/{project_id}"
        policy = projects.get_iam_policy(request=iam_policy_pb2.GetIamPolicyRequest(resource=resource))
        target = None
        for b in policy.bindings:
            if b.role == role:
                target = b
                break
        if target is None:
            target = policy_pb2.Binding(role=role, members=[member])
            policy.bindings.append(target)
        else:
            if member not in target.members:
                target.members.append(member)
        projects.set_iam_policy(request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy))
        return AttachResult(success=True, detail={"resource": resource, "role": role, "member": member})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})


def detach_gcp(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    project_id = (source.config or {}).get("project_id")
    if not project_id:
        return AttachResult(success=False, detail={"error": "missing project_id"})

    cred_path = _gcp_credentials_path(source)
    if not cred_path:
        return AttachResult(success=True, detail={"stub": True, "note": "GCP 자격 미설정 — DB만 갱신"})

    try:
        import os as _os
        _os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        from google.cloud import resourcemanager_v3  # type: ignore
        from google.iam.v1 import iam_policy_pb2  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "google-cloud SDK not installed"})

    member = identity.external_id or identity.name
    role = permission.external_id or permission.name

    try:
        projects = resourcemanager_v3.ProjectsClient()
        resource = f"projects/{project_id}"
        policy = projects.get_iam_policy(request=iam_policy_pb2.GetIamPolicyRequest(resource=resource))
        for b in policy.bindings:
            if b.role == role and member in b.members:
                b.members.remove(member)
        projects.set_iam_policy(request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy))
        return AttachResult(success=True, detail={"resource": resource, "role": role, "member": member})
    except Exception as exc:
        return AttachResult(success=False, detail={"error": str(exc)})


def _gcp_stub(reason: str | None = None) -> FetchResult:
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


# ── Azure RBAC provider ──────────────────────────────────────────
#
# config 키:
#   subscription_id : 필수
#   scope           : 기본 "/subscriptions/{subscription_id}"
# credentials_env_ref (Service Principal):
#   tenant_id, client_id, client_secret  (각각 ENV 변수 이름)
def _azure_credential(source: IAMSource):
    try:
        from azure.identity import ClientSecretCredential  # type: ignore
    except ImportError:
        logger.warning("azure_identity_missing")
        return None
    creds = _resolve_credentials(source)
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


def _azure_scope(source: IAMSource) -> str:
    cfg = source.config or {}
    if cfg.get("scope"):
        return cfg["scope"]
    sub = cfg.get("subscription_id", "")
    return f"/subscriptions/{sub}" if sub else ""


def fetch_azure(source: IAMSource) -> FetchResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return _azure_stub("missing subscription_id")

    cred = _azure_credential(source)
    if cred is None:
        return _azure_stub()

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return _azure_stub()

    identities: list[FetchedIdentity] = []
    permissions: list[FetchedPermission] = []
    scope = _azure_scope(source)
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


def attach_azure(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return AttachResult(success=False, detail={"error": "missing subscription_id"})

    cred = _azure_credential(source)
    if cred is None:
        return AttachResult(success=True, detail={"stub": True, "note": "Azure 자격 미설정 — DB만 갱신"})

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "azure-mgmt-authorization not installed"})

    scope = _azure_scope(source)
    principal_id = identity.external_id or identity.name
    role_def_id = permission.external_id or permission.name

    try:
        import uuid
        client = AuthorizationManagementClient(cred, subscription_id=sub)
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
        return AttachResult(success=False, detail={"error": str(exc)})


def detach_azure(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    cfg = source.config or {}
    sub = cfg.get("subscription_id")
    if not sub:
        return AttachResult(success=False, detail={"error": "missing subscription_id"})

    cred = _azure_credential(source)
    if cred is None:
        return AttachResult(success=True, detail={"stub": True, "note": "Azure 자격 미설정 — DB만 갱신"})

    try:
        from azure.mgmt.authorization import AuthorizationManagementClient  # type: ignore
    except ImportError:
        return AttachResult(success=False, detail={"error": "azure-mgmt-authorization not installed"})

    scope = _azure_scope(source)
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


def _azure_stub(reason: str | None = None) -> FetchResult:
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


# ── Capability map ───────────────────────────────────────────────
#
# 각 kind가 실제로 어디까지 동작하는지 정직하게 노출.
# UI는 이 값을 받아 dropdown에 배지(ready/demo/coming_soon)로 표시한다.
CAPABILITIES: dict[IAMSourceKind, dict[str, object]] = {
    IAMSourceKind.AWS: {
        "status": "ready",
        "sync": True,
        "grant": True,
        "revoke": True,
        "note": "boto3 기반 IAM 사용자/역할/정책 동기화 + attach/detach. 자격 미설정 시 데모 데이터.",
    },
    IAMSourceKind.K8S: {
        "status": "ready",
        "sync": True,
        "grant": True,
        "revoke": True,
        "note": "kubeconfig 또는 in-cluster ServiceAccount. RoleBinding/ClusterRoleBinding 생성/삭제. 자격 미설정 시 데모.",
    },
    IAMSourceKind.LDAP: {
        "status": "ready",
        "sync": True,
        "grant": True,
        "revoke": True,
        "note": "사내 온프레미스 디렉토리. Active Directory / OpenLDAP / FreeIPA / Samba AD. 그룹 멤버십으로 권한 부여/회수.",
    },
    IAMSourceKind.GCP: {
        "status": "ready",
        "sync": True,
        "grant": True,
        "revoke": True,
        "note": "google-cloud-resource-manager + iam_admin. 프로젝트 IAM policy 동기화 + binding add/remove. 자격 미설정 시 데모.",
    },
    IAMSourceKind.AZURE: {
        "status": "ready",
        "sync": True,
        "grant": True,
        "revoke": True,
        "note": "azure-mgmt-authorization. Subscription 단위 roleAssignments 생성/삭제. 자격 미설정 시 데모.",
    },
    IAMSourceKind.CUSTOM: {
        "status": "demo",
        "sync": False,
        "grant": False,
        "revoke": False,
        "note": "데모 placeholder. webhook 기반 사내 IAM 연동 스펙은 별도 설계 예정.",
    },
}


def get_capabilities() -> list[dict]:
    return [
        {"kind": kind.value, **caps}
        for kind, caps in CAPABILITIES.items()
    ]


# ── 디스패치 ──────────────────────────────────────────────────
def fetch_for(source: IAMSource) -> FetchResult:
    if source.kind == IAMSourceKind.AWS:
        return fetch_aws(source)
    if source.kind == IAMSourceKind.K8S:
        return fetch_k8s(source)
    if source.kind == IAMSourceKind.LDAP:
        return fetch_ldap(source)
    if source.kind == IAMSourceKind.GCP:
        return fetch_gcp(source)
    if source.kind == IAMSourceKind.AZURE:
        return fetch_azure(source)
    # custom — stub만 (별도 설계)
    return FetchResult(
        stub=True,
        identities=[
            FetchedIdentity(identity_type=IdentityType.USER, name=f"{source.kind.value}-demo-user"),
        ],
        permissions=[
            FetchedPermission(name=f"{source.kind.value}-read", risk_hint="read"),
            FetchedPermission(name=f"{source.kind.value}-admin", risk_hint="admin"),
        ],
    )


def attach_for(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    if source.kind == IAMSourceKind.AWS:
        return attach_aws(source, identity, permission)
    if source.kind == IAMSourceKind.K8S:
        return attach_k8s(source, identity, permission)
    if source.kind == IAMSourceKind.LDAP:
        return attach_ldap(source, identity, permission)
    if source.kind == IAMSourceKind.GCP:
        return attach_gcp(source, identity, permission)
    if source.kind == IAMSourceKind.AZURE:
        return attach_azure(source, identity, permission)
    return AttachResult(
        success=False,
        detail={"stub": True, "note": f"{source.kind.value} grant는 별도 설계"},
    )


def detach_for(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    if source.kind == IAMSourceKind.AWS:
        return detach_aws(source, identity, permission)
    if source.kind == IAMSourceKind.K8S:
        return detach_k8s(source, identity, permission)
    if source.kind == IAMSourceKind.LDAP:
        return detach_ldap(source, identity, permission)
    if source.kind == IAMSourceKind.GCP:
        return detach_gcp(source, identity, permission)
    if source.kind == IAMSourceKind.AZURE:
        return detach_azure(source, identity, permission)
    return AttachResult(
        success=False,
        detail={"stub": True, "note": f"{source.kind.value} 회수는 별도 설계"},
    )
