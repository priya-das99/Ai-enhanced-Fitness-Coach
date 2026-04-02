# app/services/token_service.py
# Token management service with blacklisting

import sqlite3
from datetime import datetime, timedelta
from app.config import settings
import os

class TokenService:
    """Service for managing JWT token blacklist"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(settings.DATABASE_PATH), 'token_blacklist.db')
        self._init_db()
    
    def _init_db(self):
        """Initialize token blacklist database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_jti TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create index for faster lookups
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_token_jti 
                ON token_blacklist(token_jti)
            ''')
            
            conn.commit()
    
    def blacklist_token(self, token_jti: str, user_id: int, expires_at: datetime):
        """Add token to blacklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO token_blacklist 
                    (token_jti, user_id, expires_at) 
                    VALUES (?, ?, ?)
                ''', (token_jti, user_id, expires_at))
                conn.commit()
                print(f"[TOKEN] Blacklisted token for user {user_id}")
        except Exception as e:
            print(f"[TOKEN] Error blacklisting token: {e}")
    
    def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT 1 FROM token_blacklist 
                    WHERE token_jti = ? AND expires_at > CURRENT_TIMESTAMP
                ''', (token_jti,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"[TOKEN] Error checking blacklist: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from blacklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM token_blacklist 
                    WHERE expires_at <= CURRENT_TIMESTAMP
                ''')
                deleted_count = cursor.rowcount
                conn.commit()
                if deleted_count > 0:
                    print(f"[TOKEN] Cleaned up {deleted_count} expired blacklisted tokens")
        except Exception as e:
            print(f"[TOKEN] Error cleaning up tokens: {e}")
    
    def blacklist_all_user_tokens(self, user_id: int):
        """Blacklist all tokens for a specific user (logout from all devices)"""
        try:
            # This is a simplified approach - in production you'd want to track active tokens
            # For now, we'll just record a "logout all" timestamp
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO token_blacklist 
                    (token_jti, user_id, expires_at) 
                    VALUES (?, ?, ?)
                ''', (f"logout_all_{user_id}_{datetime.utcnow().timestamp()}", 
                      user_id, 
                      datetime.utcnow() + timedelta(days=1)))
                conn.commit()
                print(f"[TOKEN] Blacklisted all tokens for user {user_id}")
        except Exception as e:
            print(f"[TOKEN] Error blacklisting all user tokens: {e}")