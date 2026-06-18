"""
LDAP / Active Directory provider — 온프레미스 사내 디렉토리.

자격증명:
  credentials_env_ref.bind_dn       → ENV 변수에 담긴 bind DN
  credentials_env_ref.bind_password → ENV 변수에 담긴 bind 비밀번호

config 키:
  server          : "ldaps://ad.corp.local" (TLS 권장)
  base_dn         : "DC=corp,DC=local"
  user_base_dn    : "CN=Users,DC=corp,DC=local"
  group_base_dn   : "CN=Groups,DC=corp,DC=local"  (없으면 base_dn 사용)
  user_filter     : 기본 "(objectClass=person)"
  group_filter    : 기본 "(objectClass=group)"  — OpenLDAP은 "(objectClass=groupOfNames)"
  user_id_attr    : 기본 "sAMAccountName" (AD) — OpenLDAP은 "uid"
  group_id_attr   : 기본 "cn"
  member_attr     : 기본 "member" — OpenLDAP은 "member" 또는 "uniqueMember"
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


def _connection(source: IAMSource):
    try:
        from ldap3 import ALL, Connection, Server  # type: ignore
    except ImportError:
        logger.warning("ldap3_sdk_missing")
        return None

    creds = resolve_credentials(source)
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


def fetch(source: IAMSource) -> FetchResult:
    conn = _connection(source)
    if conn is None:
        return _stub()

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


def _member_attr(source: IAMSource) -> str:
    return (source.config or {}).get("member_attr", "member")


def attach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """그룹 멤버십에 사용자 DN을 add → 권한 부여."""
    conn = _connection(source)
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

    attr = _member_attr(source)
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


def detach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    conn = _connection(source)
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

    attr = _member_attr(source)
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


def _stub() -> FetchResult:
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
