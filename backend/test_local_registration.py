#!/usr/bin/env python3
"""
Test registration locally with the SHA256 fix
"""

import requests
import time
import os

def test_local_registration():
    """Test registration on local server"""
    
    base_url = "http://localhost:8000"
    
    test_cases = [
        {
            "name": "Simple password",
            "password": "test123"
        },
        {
            "name": "Long password (100 chars)",
            "password": "a" * 100
        },
        {
            "name": "Unicode password",
            "password": "🚀🚀🚀test123🚀🚀🚀"
        }
    ]
    
    print("🧪 Testing local registration with SHA256 fix")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        test_user = {
            "username": f"local_test_{int(time.time())}_{i}",
            "email": f"local_test_{int(time.time())}_{i}@test.com",
            "password": test_case["password"],
            "full_name": "Local Test"
        }
        
        print(f"   Password: '{test_case['password'][:20]}{'...' if len(test_case['password']) > 20 else ''}'")
        print(f"   Length: {len(test_case['password'])} chars, {len(test_case['password'].encode('utf-8'))} bytes")
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/auth/register",
                json=test_user,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                print("   ✅ SUCCESS: Registration worked!")
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("error", "")
                print(f"   ❌ FAIL: {error_msg}")
                return False
            else:
                print(f"   ❌ FAIL: Unexpected status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Local server not running. Start with: uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
            return False
    
    print(f"\n🎉 All local registration tests passed!")
    return True

if __name__ == "__main__":
    test_local_registration()