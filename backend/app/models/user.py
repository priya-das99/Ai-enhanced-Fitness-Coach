# app/models/user.py
# User-related Pydantic models

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import synonym

Base = declarative_base()

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = ""

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: Optional[str]
    last_login: Optional[str]
    
    class Config:
        from_attributes = True

# SQLAlchemy models for insight system compatibility
class MoodLog(Base):
    """SQLAlchemy model for mood_logs table"""
    __tablename__ = 'mood_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    mood = Column(String, nullable=False)
    mood_emoji = Column(String)
    reason = Column(String)
    reason_category = Column(String)
    mood_intensity = Column(Integer)
    stress_level = Column(Integer)
    energy_level = Column(Integer)
    confidence_level = Column(Integer)
    tags = Column(Text)
    timestamp = Column(DateTime)
    
    # Alias for compatibility without remapping the same Column twice
    created_at = synonym("timestamp")

class ActivityCompletion(Base):
    """SQLAlchemy model for user_activity_history table"""
    __tablename__ = 'user_activity_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    activity_id = Column(String, nullable=False)
    activity_name = Column(String, nullable=False)
    activity_type = Column(String)
    mood_emoji = Column(String)
    reason = Column(String)
    completed = Column(Boolean)
    duration_minutes = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    timestamp = Column(DateTime)
    day_of_week = Column(String)
    time_of_day = Column(String)
    completion_percentage = Column(Integer)
    user_rating = Column(Integer)
    energy_before = Column(Integer)
    energy_after = Column(Integer)
    satisfaction_score = Column(Integer)
    would_repeat = Column(Boolean)
    notes = Column(Text)
    
    # Alias for compatibility without remapping the same Column twice
    created_at = synonym("timestamp")
