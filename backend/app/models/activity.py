# app/models/activity.py
# Activity-related Pydantic models

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ActivityButtonClick(BaseModel):
    activity_id: str

class ActivityLogRequest(BaseModel):
    activity_type: str
    value: float
    unit: str
    notes: Optional[str] = ""

class ActivityResponse(BaseModel):
    success: bool
    activities: List[Dict[str, Any]]

class ActivitySummaryResponse(BaseModel):
    success: bool
    summary: Dict[str, Any]
