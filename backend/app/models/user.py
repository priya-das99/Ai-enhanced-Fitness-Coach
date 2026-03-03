# app/models/user.py
# User-related Pydantic models

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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
