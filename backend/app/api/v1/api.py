"""
🌙 Mond API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import tags, security, dashboard, auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tag Management"])
api_router.include_router(security.router, prefix="/security", tags=["Security"])
