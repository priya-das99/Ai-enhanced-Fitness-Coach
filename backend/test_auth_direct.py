#!/usr/bin/env python3
"""
Direct Auth Service Test
Test auth service without HTTP layer
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_auth_service():
    """Test auth service directly"""
    print("🧪 Testing auth service directly...")
    
    try:
        from app.services.auth_service import AuthService
        
        auth_service = AuthService()
        
        # Test login
        result = auth_service.login_user("demo", "demo123")
        
        print("✅ Auth service test successful!")
        print(f"   Message: {result.get('message')}")
        print(f"   Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"   User: {result.get('user', {}).get('username')}")
        
    except Exception as e:
        print(f"❌ Auth service error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_auth_service()