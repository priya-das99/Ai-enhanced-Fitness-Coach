#!/usr/bin/env python3
"""
Test Login Functionality
Quick test to verify login works correctly
"""

import os
import sys
import requests
import json

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_login():
    """Test login endpoint"""
    print("🧪 Testing login functionality...")
    
    # Test data
    login_data = {
        "username": "demo",
        "password": "demo123"
    }
    
    try:
        # Make login request
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   User: {data.get('user', {}).get('username', 'N/A')}")
        else:
            print("❌ Login failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_login()