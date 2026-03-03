# app/api/v1/endpoints/health.py
# Health check endpoint

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Chat Assistant API is running"}
