#!/usr/bin/env python3
"""
Test the SHA256 + bcrypt password hashing fix locally
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    """Test password hashing with various lengths"""
    
    test_passwords = [
        "test123",  # Simple 7-character password
        "a" * 50,   # 50 characters
        "a" * 100,  # 100 characters (would exceed bcrypt limit)
        "🚀" * 30,  # Unicode characters (emojis use multiple bytes)
        "password with spaces and special chars!@#$%^&*()",
    ]
    
    print("🧪 Testing SHA256 + bcrypt password hashing")
    print("=" * 60)
    
    for i, password in enumerate(test_passwords, 1):
        print(f"\n{i}. Testing password: '{password[:20]}{'...' if len(password) > 20 else ''}'")
        print(f"   Length: {len(password)} characters, {len(password.encode('utf-8'))} bytes")
        
        try:
            # Test hashing
            hashed = get_password_hash(password)
            print(f"   ✅ Hashing successful")
            print(f"   Hash length: {len(hashed)} characters")
            
            # Test verification with correct password
            if verify_password(password, hashed):
                print(f"   ✅ Verification successful (correct password)")
            else:
                print(f"   ❌ Verification failed (correct password)")
                return False
            
            # Test verification with wrong password
            if not verify_password(password + "wrong", hashed):
                print(f"   ✅ Verification correctly rejected wrong password")
            else:
                print(f"   ❌ Verification incorrectly accepted wrong password")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print(f"\n🎉 All password hashing tests passed!")
    return True

if __name__ == "__main__":
    success = test_password_hashing()
    if not success:
        sys.exit(1)