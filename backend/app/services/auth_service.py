# app/services/auth_service.py
# Authentication business logic

from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import AuthenticationError, BadRequestError
from typing import Dict

class AuthService:
    """Service for authentication operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def register_user(self, username: str, email: str, password: str, full_name: str = "") -> Dict:
        """Register a new user"""
        # Validate password length
        if len(password) < 6:
            raise BadRequestError("Password must be at least 6 characters")
        
        # Validate password isn't too long (bcrypt limit is 72 bytes)
        if len(password.encode('utf-8')) > 72:
            raise BadRequestError("Password is too long. Please use a shorter password.")
        
        # Check if user already exists
        if self.user_repo.exists(username=username, email=email):
            raise BadRequestError("Username or email already exists")
        
        # Hash password and create user
        password_hash = get_password_hash(password)
        user_id = self.user_repo.create(username, email, password_hash, full_name)
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "username": username
        }
    
    def login_user(self, username: str, password: str) -> Dict:
        """Login user and return token"""
        # Find user
        user = self.user_repo.get_by_username(username)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            raise AuthenticationError("Invalid username or password")
        
        # Update last login
        self.user_repo.update_last_login(user['id'])
        
        # Create access token
        access_token = create_access_token(data={"sub": user['id']})
        
        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user.get('full_name')
            }
        }
    
    def get_user_by_id(self, user_id: int) -> Dict:
        """Get user by ID"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Remove sensitive data
        user_data = dict(user)
        user_data.pop('password_hash', None)
        return user_data
