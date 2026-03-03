# app/api/v1/endpoints/admin.py
# Admin endpoints for system management

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.services.chat_cleanup_service import ChatCleanupService, run_scheduled_cleanup
from typing import Dict

router = APIRouter()
cleanup_service = ChatCleanupService()

@router.get("/storage/stats")
async def get_storage_stats(current_user: Dict = Depends(get_current_user)):
    """Get storage statistics"""
    try:
        stats = cleanup_service.get_storage_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/cleanup")
async def cleanup_storage(
    retention_days: int = 90,
    current_user: Dict = Depends(get_current_user)
):
    """
    Manually trigger storage cleanup
    
    Args:
        retention_days: Days to keep messages (default 90)
    """
    try:
        result = cleanup_service.cleanup_old_messages(retention_days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/optimize")
async def optimize_database(current_user: Dict = Depends(get_current_user)):
    """Optimize database"""
    try:
        result = cleanup_service.optimize_database()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/archive")
async def archive_old_messages(
    archive_days: int = 90,
    current_user: Dict = Depends(get_current_user)
):
    """
    Archive old messages to separate table
    
    Args:
        archive_days: Days after which to archive (default 90)
    """
    try:
        result = cleanup_service.archive_old_messages(archive_days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/run")
async def run_maintenance(current_user: Dict = Depends(get_current_user)):
    """Run full maintenance (cleanup + optimize)"""
    try:
        result = run_scheduled_cleanup()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
