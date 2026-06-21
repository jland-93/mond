"""
API v1 라우터
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_audit_log,
    admin_github_sync,
    admin_slack,
    ai,
    ai_providers,
    assets,
    auth,
    dashboard,
    digest,
    findings,
    health,
    iam,
    integrations,
    knowledge,
    me,
    mfa,
    policies,
    policy_sim,
    policy_templates,
    regulations,
    reports,
    role_requests,
    scans,
    users,
    webhook_tokens,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(mfa.router, prefix="/auth/mfa", tags=["MFA"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(me.router, prefix="/me", tags=["My Mond"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(policy_sim.router, prefix="/policy", tags=["Policy Simulation"])
api_router.include_router(policy_templates.router, prefix="/policy", tags=["Policy Templates"])
api_router.include_router(regulations.router, tags=["Regulations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(ai_providers.router, prefix="/admin/ai-providers", tags=["AI Providers (Admin)"])
api_router.include_router(admin_slack.router, prefix="/admin/slack", tags=["Slack Channels (Admin)"])
api_router.include_router(admin_github_sync.router, prefix="/admin/github-sync", tags=["GitHub Sync (Admin)"])
api_router.include_router(admin_audit_log.router, prefix="/admin/audit-log", tags=["Audit Log (Admin)"])
api_router.include_router(digest.router, prefix="/admin/digest", tags=["Daily Digest (Admin)"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(webhook_tokens.router, prefix="/webhook-tokens", tags=["Webhook Tokens"])
api_router.include_router(iam.router, prefix="/iam", tags=["IAM Self-Service"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Hub"])
api_router.include_router(users.router, prefix="/users", tags=["Users (Admin)"])
api_router.include_router(role_requests.router, tags=["Role Requests"])
