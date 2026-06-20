"""
개발용 시드 데이터

빈 DB에 데모 자산/정책을 채워 OSS 사용자가 `docker-compose up` 직후 UI를 둘러볼 수 있게 한다.
이미 데이터가 있으면 아무것도 하지 않는다.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.data.knowledge_seed import SEED as KNOWLEDGE_SEED
from app.iam import providers as iam_providers
from app.models.asset import Asset, AssetType
from app.models.iam import IAMIdentity, IAMSource, IAMSourceKind, Permission
from app.models.knowledge import KnowledgeCard, KnowledgeSource
from app.models.policy import Policy, PolicyType

logger = get_logger(__name__)


DEMO_ASSETS = [
    {
        "name": "mond-backend",
        "asset_type": AssetType.REPOSITORY,
        "uri": "https://github.com/jland-93/mond",
        "description": "Mond backend repository (self-host scan demo)",
        "labels": {"team": "platform", "criticality": "high"},
        "owner": "platform",
        "environment": "prod",
    },
    {
        "name": "demo-nginx-image",
        "asset_type": AssetType.CONTAINER_IMAGE,
        "uri": "docker.io/library/nginx:1.25-alpine",
        "description": "데모용 nginx 컨테이너 이미지",
        "labels": {"runtime": "container"},
        "owner": "ops",
        "environment": "dev",
    },
    {
        "name": "demo-public-site",
        "asset_type": AssetType.URL,
        "uri": "https://example.com",
        "description": "DAST 데모용 공개 사이트",
        "labels": {"surface": "public"},
        "owner": "appsec",
        "environment": "prod",
    },
]


DEMO_POLICIES = [
    {
        "name": "Block Critical Vulnerabilities",
        "policy_type": PolicyType.SCA,
        "description": "critical 이상의 의존성 취약점 발견 시 파이프라인 차단",
        "enabled": True,
        "severity_threshold": "critical",
        "definition": {"block_above": "critical"},
        "compliance_refs": ["OWASP-A06"],
    },
    {
        "name": "Container Hardening Baseline",
        "policy_type": PolicyType.CONTAINER,
        "description": "이미지에 high 이상 취약점이 누적되지 않도록 한다",
        "enabled": True,
        "severity_threshold": "high",
        "definition": {"block_above": "high", "deny_root_user": True},
        "compliance_refs": ["CIS-Docker-4.1"],
    },
    {
        "name": "Secrets in Code",
        "policy_type": PolicyType.SECRETS,
        "description": "리포지토리 내 평문 시크릿 차단",
        "enabled": True,
        "severity_threshold": "high",
        "definition": {"rules": ["AKIA[0-9A-Z]{16}", "-----BEGIN.*PRIVATE KEY-----"]},
        "compliance_refs": ["OWASP-A02"],
    },
    {
        # OPA Rego 데모 — Trivy의 특정 rule_id를 deny.
        # OPA 바이너리가 backend 이미지에 함께 빌드되어 즉시 평가 가능.
        # 비활성으로 시드해 OSS 첫 부팅에 영향 없음; Admin UI에서 활성화.
        "name": "Sample OPA — Deny Trivy CVE-2024-0001",
        "policy_type": PolicyType.CUSTOM,
        "description": "OPA Rego 평가 데모 — 특정 CVE rule_id가 발견되면 deny",
        "enabled": False,
        "severity_threshold": "low",
        "engine": "opa",
        "definition": {
            "rego": """package mond

# OPA v1 Rego — keywords가 기본 포함이므로 import 불필요
deny contains msg if {
    some f in input.findings
    f.rule_id == "CVE-2024-0001"
    msg := sprintf("blocked vulnerability %s (%s)", [f.rule_id, f.severity])
}
""",
            "query": "data.mond.deny",
        },
        "compliance_refs": [],
    },
]


async def seed_if_empty(db: AsyncSession) -> None:
    asset_count = (await db.execute(select(func.count(Asset.id)))).scalar_one()
    policy_count = (await db.execute(select(func.count(Policy.id)))).scalar_one()

    if asset_count == 0:
        for payload in DEMO_ASSETS:
            db.add(Asset(**payload))
        logger.info("seed_assets", count=len(DEMO_ASSETS))

    if policy_count == 0:
        for payload in DEMO_POLICIES:
            db.add(Policy(**payload))
        logger.info("seed_policies", count=len(DEMO_POLICIES))

    if asset_count == 0 or policy_count == 0:
        await db.commit()

    # IAM 데모 source — AWS 자격증명이 없으면 stub identities + permissions가 들어간다.
    iam_count = (await db.execute(select(func.count(IAMSource.id)))).scalar_one()
    if iam_count == 0:
        source = IAMSource(
            name="aws-demo",
            kind=IAMSourceKind.AWS,
            config={"region": "us-east-1", "account_id": "000000000000"},
            credentials_env_ref={
                "access_key_id": "AWS_ACCESS_KEY_ID",
                "secret_access_key": "AWS_SECRET_ACCESS_KEY",
            },
        )
        db.add(source)
        await db.flush()  # source.id 확보
        result = iam_providers.fetch_for(source)
        for ident in result.identities:
            db.add(
                IAMIdentity(
                    source_id=source.id,
                    identity_type=ident.identity_type,
                    name=ident.name,
                    external_id=ident.external_id,
                    attributes=ident.attributes or {},
                )
            )
        for perm in result.permissions:
            db.add(
                Permission(
                    source_id=source.id,
                    name=perm.name,
                    external_id=perm.external_id,
                    description=perm.description,
                    risk_hint=perm.risk_hint,
                    attributes=perm.attributes or {},
                )
            )
        logger.info("seed_iam", stub=result.stub, identities=len(result.identities), permissions=len(result.permissions))
        await db.commit()

    # Knowledge Hub — slug 기준 upsert.
    # OSS 업스트림에서 refs/summary가 갱신되면 부팅 시 SEED 행만 자동 동기화.
    # source=AI 또는 사용자가 직접 수정한 카드는 절대 건드리지 않는다.
    inserted = 0
    refreshed = 0
    for payload in KNOWLEDGE_SEED:
        existing = (
            await db.execute(select(KnowledgeCard).where(KnowledgeCard.slug == payload["slug"]))
        ).scalar_one_or_none()
        if existing is None:
            db.add(KnowledgeCard(**payload, source=KnowledgeSource.SEED, published=True))
            inserted += 1
            continue
        # 사용자가 손댔거나 AI가 만든 카드는 그대로 둠
        if existing.source != KnowledgeSource.SEED:
            continue
        # SEED 행은 업스트림 값으로 갱신 (refs/title/summary/ask/category)
        changed = False
        for key in ("title_ko", "title_en", "summary_ko", "summary_en", "ask_ko", "ask_en", "refs", "category"):
            new_val = payload.get(key)
            if new_val is not None and getattr(existing, key) != new_val:
                setattr(existing, key, new_val)
                changed = True
        if changed:
            refreshed += 1
    logger.info("seed_knowledge", inserted=inserted, refreshed=refreshed, total=len(KNOWLEDGE_SEED))
    await db.commit()
