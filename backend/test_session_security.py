#!/usr/bin/env python3
"""
Test script to verify session security fixes
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_session_security():
    """Test that logout properly invalidates tokens"""
    print("🔐 Testing Session Security")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    register_data = {
        "username": f"testuser_security_{int(time.time())}",  # Unique username
        "email": f"test{int(time.time())}@security.com",      # Unique email
        "password": "testpass123",
        "full_name": "Security Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("   ✅ User registered successfully")
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    # Step 2: Login and get token
    print("2. Logging in...")
    login_data = {
        "username": register_data["username"],  # Use the same username from registration
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        login_result = response.json()
        token = login_result["access_token"]
        print("   ✅ Login successful")
        print(f"   Token: {token[:20]}...")
    else:
        print(f"   ❌ Login failed: {response.text}")
        return
    
    # Step 3: Test authenticated endpoint
    print("3. Testing authenticated endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✅ Authenticated successfully as: {user_info['username']}")
    else:
        print(f"   ❌ Authentication failed: {response.text}")
        return
    
    # Step 4: Logout
    print("4. Logging out...")
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    if response.status_code == 200:
        print("   ✅ Logout successful")
    else:
        print(f"   ❌ Logout failed: {response.text}")
        return
    
    # Step 5: Try to use the same token again (should fail)
    print("5. Testing token after logout...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 401:
        print("   ✅ Token properly invalidated - authentication failed as expected")
    else:
        print(f"   ❌ SECURITY ISSUE: Token still valid after logout! Response: {response.text}")
        return
    
    print("\n🎉 Session security test PASSED!")
    print("✅ Tokens are properly invalidated on logout")

def test_token_expiration():
    """Test that tokens expire properly"""
    print("\n⏰ Testing Token Expiration")
    print("=" * 50)
    
    # Create a new user for this test
    import time
    register_data = {
        "username": f"testuser_exp_{int(time.time())}",
        "email": f"testexp{int(time.time())}@security.com",
        "password": "testpass123",
        "full_name": "Expiration Test User"
    }
    
    # Register the user first
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code != 201:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    # Login
    login_data = {
        "username": register_data["username"],
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        login_result = response.json()
        token = login_result["access_token"]
        print("   ✅ Login successful")
        
        # Decode token to check expiration
        import jwt
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                from datetime import datetime
                exp_time = datetime.utcfromtimestamp(exp_timestamp)  # Use UTC
                current_time = datetime.utcnow()
                time_diff = (exp_time - current_time).total_seconds() / 60
                print(f"   ✅ Token expires in {time_diff:.1f} minutes")
                
                if time_diff <= 16:  # Allow small buffer for processing time
                    print("   ✅ Token expiration time is appropriate")
                else:
                    print(f"   ⚠️  Token expiration time is longer than expected: {time_diff:.1f} minutes")
            else:
                print("   ❌ No expiration time found in token")
        except Exception as e:
            print(f"   ❌ Error decoding token: {e}")
    else:
        print(f"   ❌ Login failed: {response.text}")

if __name__ == "__main__":
    try:
        test_session_security()
        test_token_expiration()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()