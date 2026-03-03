# app/models/auth.py
# Authentication-related Pydantic models

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = ""

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user: dict
