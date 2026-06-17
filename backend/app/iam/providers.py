"""
🌙 IAM 프로바이더 어댑터 — AWS / mock

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
        return AttachResult(
            success=False,
            detail={
                "stub": True,
                "note": (
                    "AWS 자격증명이 없어 실제 권한 부여(attach_policy)를 건너뜁니다. "
                    "Mond DB에는 결정 이력이 남지만, AWS IAM에는 적용되지 않았습니다. "
                    ".env에 AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY를 설정한 뒤 다시 시도하세요."
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


# ── 디스패치 ──────────────────────────────────────────────────
def fetch_for(source: IAMSource) -> FetchResult:
    if source.kind == IAMSourceKind.AWS:
        return fetch_aws(source)
    # GCP/Azure/k8s/custom — stub만 (후속 PR)
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
    return AttachResult(
        success=False,
        detail={"stub": True, "note": f"{source.kind.value} grant는 후속 PR에서 지원"},
    )
