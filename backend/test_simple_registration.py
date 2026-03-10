#!/usr/bin/env python3
"""
Simple registration test to check deployed version
"""

import requests
import json
import os

def test_simple_registration():
    """Test with a very simple, short password"""
    
    base_url = "https://ai-enhanced-fitness-coach.onrender.com"
    
    # Test data with very simple password
    test_user = {
        "username": f"simple_{os.urandom(4).hex()}",
        "email": f"simple_{os.urandom(4).hex()}@test.com",
        "password": "test123",  # Very simple 7-character password
        "full_name": "Simple Test"
    }
    
    print(f"🧪 Testing simple registration with password: '{test_user['password']}'")
    print(f"   Username: {test_user['username']}")
    print(f"   Password length: {len(test_user['password'])} characters")
    print(f"   Password bytes: {len(test_user['password'].encode('utf-8'))} bytes")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=15
        )
        
        print(f"\n📊 Results:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("   ✅ SUCCESS: Registration worked!")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", "")
            
            if "already exists" in error_msg:
                print("   ✅ SUCCESS: Validation works (user exists)")
                return True
            elif "72 bytes" in error_msg:
                print("   ❌ FAIL: Still getting bcrypt 72-byte error")
                print("   🔍 This means the deployed version doesn't have our fixes")
                return False
            else:
                print(f"   ⚠️  Different error: {error_msg}")
                return False
        else:
            print(f"   ❌ FAIL: Unexpected status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ FAIL: Network error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Registration Test")
    print("=" * 50)
    
    success = test_simple_registration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Registration is working on the deployed version!")
    else:
        print("⚠️  Registration is still broken on the deployed version.")
        print("💡 The deployment may not have the latest fixes yet.")