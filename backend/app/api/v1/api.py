"""
🌙 API v1 라우터
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    assets,
    dashboard,
    findings,
    health,
    integrations,
    policies,
    policy_sim,
    regulations,
    reports,
    scans,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(policy_sim.router, prefix="/policy", tags=["Policy Simulation"])
api_router.include_router(regulations.router, tags=["Regulations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
