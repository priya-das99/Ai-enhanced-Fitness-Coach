# app/core/security.py
# Security utilities: password hashing, JWT tokens

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password with proper bcrypt length handling"""
    # Log password details for debugging
    char_length = len(password)
    byte_length = len(password.encode('utf-8'))
    
    print(f"[PASSWORD] Character length: {char_length}")
    print(f"[PASSWORD] Byte length: {byte_length}")
    
    # Bcrypt has a 72-byte limit, so we need to handle this properly
    if byte_length > 72:
        print(f"[PASSWORD] Password too long ({byte_length} bytes), truncating to 72 bytes")
        # Truncate to 72 bytes, being careful with UTF-8 encoding
        password_bytes = password.encode('utf-8')[:72]
        # Decode back, ignoring any incomplete characters at the end
        password = password_bytes.decode('utf-8', errors='ignore')
        print(f"[PASSWORD] Truncated to {len(password)} characters, {len(password.encode('utf-8'))} bytes")
    
    try:
        hashed = pwd_context.hash(password)
        print("[PASSWORD] Successfully hashed password")
        return hashed
    except Exception as e:
        print(f"[PASSWORD] Error hashing password: {e}")
        raise

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    # Convert sub to string if it's an integer (JWT spec requires string)
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
