# app/api/v1/endpoints/activity.py
# Activity endpoints

from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.activity import (
    ActivityButtonClick, 
    ActivityLogRequest,
    ActivityResponse, 
    ActivitySummaryResponse
)
from app.services.activity_service import ActivityService
from app.api.deps import get_current_user
from typing import Dict

router = APIRouter()
activity_service = ActivityService()

@router.post("/button-click")
async def handle_button_click(
    request: ActivityButtonClick,
    current_user: Dict = Depends(get_current_user)
):
    """Handle activity button click"""
    try:
        response = activity_service.handle_button_click(
            current_user['id'], 
            request.activity_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today", response_model=ActivityResponse)
async def get_today_activities(current_user: Dict = Depends(get_current_user)):
    """Get today's activities for logged-in user"""
    try:
        activities = activity_service.get_today_activities(current_user['id'])
        return {"success": True, "activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    activity_type: str = Query(..., description="Type of activity"),
    days: int = Query(7, description="Number of days to summarize"),
    current_user: Dict = Depends(get_current_user)
):
    """Get activity summary for logged-in user"""
    try:
        summary = activity_service.get_activity_summary(
            current_user['id'], 
            activity_type, 
            days
        )
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log")
async def log_activity(
    request: ActivityLogRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Log a health activity"""
    try:
        activity_id = activity_service.log_activity(
            user_id=current_user['id'],
            activity_type=request.activity_type,
            value=request.value,
            unit=request.unit,
            notes=request.notes
        )
        return {
            "success": True,
            "activity_id": activity_id,
            "message": f"Logged {request.value} {request.unit} of {request.activity_type}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
