# app/api/v1/router.py
# Main API router - aggregates all endpoint routers

from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, activity, health, analytics, admin, demo_insights

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])  # Phase 3
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])  # Storage management
api_router.include_router(demo_insights.router, prefix="/demo", tags=["Demo Insights"])  # AI Insights Demo
