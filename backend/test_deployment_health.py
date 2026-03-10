#!/usr/bin/env python3
"""
Test deployment health and connectivity
"""

import requests
import time

def test_deployment_health():
    """Test if the deployment is reachable"""
    
    base_url = "https://ai-enhanced-fitness-coach.onrender.com"
    
    print("🔍 Testing deployment connectivity...")
    
    # Test 1: Basic connectivity
    try:
        print("\n1️⃣ Testing basic connectivity...")
        response = requests.get(f"{base_url}/", timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
        if response.status_code == 200:
            print("   ✅ Basic connectivity works")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Basic connectivity failed: {e}")
        return False
    
    # Test 2: API health check
    try:
        print("\n2️⃣ Testing API health...")
        response = requests.get(f"{base_url}/api/v1/health", timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
        if response.status_code == 200:
            print("   ✅ API health check works")
            print(f"   Response: {response.text}")
        else:
            print(f"   ⚠️  API health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API health check failed: {e}")
    
    # Test 3: Registration endpoint with longer timeout
    try:
        print("\n3️⃣ Testing registration endpoint with longer timeout...")
        test_user = {
            "username": f"health_test_{int(time.time())}",
            "email": f"health_test_{int(time.time())}@test.com",
            "password": "test123",
            "full_name": "Health Test"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=60  # Longer timeout
        )
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {end_time - start_time:.2f}s")
        print(f"   Response: {response.text}")
        
        if response.status_code in [200, 201, 400]:
            print("   ✅ Registration endpoint is responding")
            return True
        else:
            print(f"   ⚠️  Unexpected registration response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Deployment Health Check")
    print("=" * 50)
    
    success = test_deployment_health()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Deployment appears to be healthy!")
    else:
        print("⚠️  Deployment has connectivity issues.")
        print("💡 This might be a temporary issue or the service might be down.")