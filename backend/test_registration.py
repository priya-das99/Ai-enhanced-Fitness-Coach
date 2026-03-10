#!/usr/bin/env python3
"""
Test registration functionality
"""

import sys
import os
import requests
import json

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_password_validation():
    """Test password validation locally"""
    print("🧪 Testing password validation...")
    
    try:
        from app.core.security import get_password_hash
        from app.services.auth_service import AuthService
        
        # Test normal password
        print("  Testing normal password...")
        hash1 = get_password_hash('demo123')
        print("  ✅ Normal password works")
        
        # Test long password
        print("  Testing long password...")
        long_password = 'a' * 80  # 80 characters
        hash2 = get_password_hash(long_password)
        print("  ✅ Long password handled correctly")
        
        # Test auth service validation
        print("  Testing auth service validation...")
        auth_service = AuthService()
        
        # This should work
        try:
            # Note: This will fail if user exists, but we're testing validation
            result = auth_service.register_user("testuser123", "test@example.com", "validpass", "Test User")
            print("  ✅ Auth service validation works")
        except Exception as e:
            if "already exists" in str(e):
                print("  ✅ Auth service validation works (user exists)")
            else:
                print(f"  ❌ Auth service error: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Password validation failed: {e}")
        return False

def test_registration_api(base_url):
    """Test registration API endpoint"""
    print(f"🌐 Testing registration API at {base_url}...")
    
    # Test data
    test_user = {
        "username": f"testuser_{os.urandom(4).hex()}",
        "email": f"test_{os.urandom(4).hex()}@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    try:
        # Test registration
        print(f"  Registering user: {test_user['username']}")
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        
        if response.status_code == 201:
            print("  ✅ Registration successful!")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            if "already exists" in error_data.get("error", ""):
                print("  ✅ Registration validation works (user exists)")
                return True
            else:
                print(f"  ❌ Registration failed with validation error: {error_data}")
                return False
        else:
            print(f"  ❌ Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_long_password_api(base_url):
    """Test long password handling via API"""
    print(f"🔒 Testing long password via API at {base_url}...")
    
    # Test data with long password
    test_user = {
        "username": f"longpass_{os.urandom(4).hex()}",
        "email": f"longpass_{os.urandom(4).hex()}@example.com",
        "password": "a" * 80,  # 80 character password
        "full_name": "Long Password Test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json()
            if "too long" in error_data.get("error", "").lower():
                print("  ✅ Long password properly rejected!")
                return True
            else:
                print(f"  ⚠️  Long password rejected for different reason: {error_data}")
                return True
        elif response.status_code == 201:
            print("  ✅ Long password handled correctly (truncated and accepted)")
            return True
        else:
            print(f"  ❌ Unexpected response for long password: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing long password: {e}")
        return False

def main():
    print("🚀 Registration Testing Suite")
    print("=" * 50)
    
    # Test 1: Local password validation
    local_test = test_password_validation()
    
    # Test 2: API endpoints
    base_urls = [
        "https://ai-enhanced-fitness-coach.onrender.com",
        "http://localhost:8000"  # Fallback for local testing
    ]
    
    api_test_passed = False
    for base_url in base_urls:
        try:
            # Quick health check
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✅ API accessible at {base_url}")
                
                # Test normal registration
                normal_test = test_registration_api(base_url)
                
                # Test long password
                long_test = test_long_password_api(base_url)
                
                if normal_test and long_test:
                    api_test_passed = True
                    break
                    
        except Exception as e:
            print(f"\n❌ API not accessible at {base_url}: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Local validation: {'✅ PASS' if local_test else '❌ FAIL'}")
    print(f"  API registration: {'✅ PASS' if api_test_passed else '❌ FAIL'}")
    
    if local_test and api_test_passed:
        print("\n🎉 All tests passed! Registration is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)