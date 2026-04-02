# app/models/activity.py
# Activity-related Pydantic models

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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

# SQLAlchemy model for activity_feedback table
class ActivityFeedback(Base):
    """SQLAlchemy model for activity_feedback table"""
    __tablename__ = 'activity_feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    activity_id = Column(String, nullable=False)
    mood_before = Column(String)
    mood_after = Column(String)
    helpful = Column(Boolean, nullable=False)
    completion_id = Column(Integer)
    created_at = Column(DateTime, nullable=False)
