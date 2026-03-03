# app/api/deps.py
# Shared API dependencies

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings
from app.repositories.user_repository import UserRepository
from typing import Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert string back to int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user
