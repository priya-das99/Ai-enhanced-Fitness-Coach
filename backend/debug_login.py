#!/usr/bin/env python3
"""
Debug Login Issue
Make a direct request to see the exact error
"""

import requests
import json

def debug_login():
    """Debug the login endpoint"""
    print("🔍 Debugging login endpoint...")
    
    # Test data
    login_data = {
        "username": "demo",
        "password": "demo123"
    }
    
    try:
        print(f"Sending request to: http://localhost:8000/api/v1/auth/login")
        print(f"Data: {json.dumps(login_data, indent=2)}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
        else:
            print("❌ Login failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on localhost:8000?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    """Test health endpoint first"""
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == '__main__':
    if test_health():
        print("\n" + "="*50)
        debug_login()
    else:
        print("❌ Server is not responding. Please start the server first.")
        print("Run: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")