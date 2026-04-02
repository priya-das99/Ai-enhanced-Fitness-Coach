# app/repositories/user_repository.py
# User data access layer

from app.core.database import get_db
from typing import Optional, Dict
from datetime import datetime

class UserRepository:
    """Repository for user database operations"""
    
    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create(self, username: str, email: str, password_hash: str, full_name: str = "") -> int:
        """Create new user"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name) 
                   VALUES (?, ?, ?, ?)""",
                (username, email, password_hash, full_name)
            )
            return cursor.lastrowid
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user_id)
            )
    
    def exists(self, username: str = None, email: str = None) -> bool:
        """Check if user exists by username or email"""
        with get_db() as conn:
            cursor = conn.cursor()
            if username and email:
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (username, email)
                )
            elif username:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            elif email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            else:
                return False
            
            return cursor.fetchone() is not None
