# app/api/v1/endpoints/auth.py
# Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from app.models.auth import LoginRequest, RegisterRequest, LoginResponse
from app.models.user import UserResponse
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, oauth2_scheme
from typing import Dict

router = APIRouter()
auth_service = AuthService()

@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        print(f"Registration attempt - Username: {request.username}, Email: {request.email}")
        print(f"Password length: {len(request.password)} characters, {len(request.password.encode('utf-8'))} bytes")
        
        result = auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        return result
    except HTTPException as e:
        # Return error in format frontend expects
        print(f"Registration HTTPException: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    try:
        result = auth_service.login_user(
            username=request.username,
            password=request.password
        )
        return result
    except HTTPException as e:
        print(f"Login HTTPException: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    except Exception as e:
        print(f"Login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    """Logout user and blacklist token"""
    try:
        # Decode token to get JTI
        from app.core.security import decode_access_token
        from app.services.token_service import TokenService
        from datetime import datetime, timedelta
        
        payload = decode_access_token(token)
        jti = payload.get("jti")
        user_id = current_user['id']
        
        if jti:
            # Blacklist the token
            token_service = TokenService()
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            token_service.blacklist_token(jti, user_id, expires_at)
            
            print(f"[LOGOUT] Token blacklisted for user {user_id}")
        
        return {"message": "Logout successful"}
    except Exception as e:
        print(f"[LOGOUT] Error during logout: {e}")
        # Even if blacklisting fails, return success (client will clear token)
        return {"message": "Logout successful"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current logged-in user information"""
    return {
        "id": current_user['id'],
        "username": current_user['username'],
        "email": current_user['email'],
        "full_name": current_user.get('full_name'),
        "created_at": current_user.get('created_at'),
        "last_login": current_user.get('last_login')
    }
