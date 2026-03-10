# app/core/security.py
# Security utilities: password hashing, JWT tokens

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using SHA256 pre-hashing"""
    import hashlib
    
    # Pre-hash the plain password with SHA256 (same as during registration)
    password_bytes = plain_password.encode('utf-8')
    sha_hash = hashlib.sha256(password_bytes).digest()
    
    # Verify the SHA256 hash against the stored bcrypt hash
    return pwd_context.verify(sha_hash, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using SHA256 pre-hashing to avoid bcrypt 72-byte limit"""
    import hashlib
    
    # Log password details for debugging
    char_length = len(password)
    byte_length = len(password.encode('utf-8'))
    
    print(f"[PASSWORD] Character length: {char_length}")
    print(f"[PASSWORD] Byte length: {byte_length}")
    
    try:
        # Pre-hash with SHA256 to ensure we never exceed bcrypt's 72-byte limit
        # SHA256 always produces exactly 32 bytes, which is well under the limit
        password_bytes = password.encode('utf-8')
        sha_hash = hashlib.sha256(password_bytes).digest()
        
        print(f"[PASSWORD] SHA256 pre-hash length: {len(sha_hash)} bytes")
        
        # Now hash the SHA256 digest with bcrypt
        hashed = pwd_context.hash(sha_hash)
        print("[PASSWORD] Successfully hashed password with SHA256 + bcrypt")
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
