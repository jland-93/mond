"""
provider 디스패처 + capability 매트릭스.

각 IAMSourceKind가 실제로 어디까지 동작하는지 정직하게 노출한다.
UI는 CAPABILITIES를 받아 dropdown에 배지(ready/demo/coming_soon)로 표시한다.
"""

from __future__ import annotations

from app.models.iam import IAMIdentity, IAMSource, IAMSourceKind, IdentityType, Permission

from . import aws, azure, gcp, k8s, ldap
from .base import AttachResult, FetchedIdentity, FetchedPermission, FetchResult


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


_FETCH_FNS = {
    IAMSourceKind.AWS: aws.fetch,
    IAMSourceKind.K8S: k8s.fetch,
    IAMSourceKind.LDAP: ldap.fetch,
    IAMSourceKind.GCP: gcp.fetch,
    IAMSourceKind.AZURE: azure.fetch,
}

_ATTACH_FNS = {
    IAMSourceKind.AWS: aws.attach,
    IAMSourceKind.K8S: k8s.attach,
    IAMSourceKind.LDAP: ldap.attach,
    IAMSourceKind.GCP: gcp.attach,
    IAMSourceKind.AZURE: azure.attach,
}

_DETACH_FNS = {
    IAMSourceKind.AWS: aws.detach,
    IAMSourceKind.K8S: k8s.detach,
    IAMSourceKind.LDAP: ldap.detach,
    IAMSourceKind.GCP: gcp.detach,
    IAMSourceKind.AZURE: azure.detach,
}


def fetch_for(source: IAMSource) -> FetchResult:
    fn = _FETCH_FNS.get(source.kind)
    if fn is not None:
        return fn(source)
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
    fn = _ATTACH_FNS.get(source.kind)
    if fn is not None:
        return fn(source, identity, permission)
    return AttachResult(
        success=False,
        detail={"stub": True, "note": f"{source.kind.value} grant는 별도 설계"},
    )


def detach_for(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    fn = _DETACH_FNS.get(source.kind)
    if fn is not None:
        return fn(source, identity, permission)
    return AttachResult(
        success=False,
        detail={"stub": True, "note": f"{source.kind.value} 회수는 별도 설계"},
    )
