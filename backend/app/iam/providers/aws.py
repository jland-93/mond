"""AWS IAM provider — boto3 기반 사용자/역할/정책 동기화 및 attach/detach."""

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


def fetch(source: IAMSource) -> FetchResult:
    creds = resolve_credentials(source)
    access_key = creds.get("access_key_id")
    secret_key = creds.get("secret_access_key")
    region = (source.config or {}).get("region", "us-east-1")

    if not access_key or not secret_key:
        return _stub()

    try:
        import boto3
    except ImportError:
        logger.warning("boto3_missing")
        return _stub()

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


def attach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    creds = resolve_credentials(source)
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


def detach(source: IAMSource, identity: IAMIdentity, permission: Permission) -> AttachResult:
    """attach의 역연산. 만료 시 자동 회수 + 수동 회수에 사용."""
    creds = resolve_credentials(source)
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


def _stub() -> FetchResult:
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
