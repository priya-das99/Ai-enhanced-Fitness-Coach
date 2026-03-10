#!/usr/bin/env python3
"""
Monitor deployment status and test when fixes are live
"""

import requests
import time
import os

def test_deployment_status():
    """Test if the new fixes are deployed"""
    
    base_url = "https://ai-enhanced-fitness-coach.onrender.com"
    
    print("🔄 Testing if password validation fixes are deployed...")
    
    # Test with a simple password that should work
    test_user = {
        "username": f"deploy_test_{int(time.time())}",
        "email": f"deploy_test_{int(time.time())}@test.com",
        "password": "test123",  # Simple 7-character password
        "full_name": "Deploy Test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: New fixes are deployed! Registration works!")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", "")
            
            if "already exists" in error_msg:
                print("✅ SUCCESS: New fixes are deployed! (User exists)")
                return True
            elif "72 bytes" in error_msg:
                print("❌ OLD VERSION: Still getting bcrypt 72-byte error")
                print("⏳ Deployment may still be in progress...")
                return False
            elif "70 bytes" in error_msg:
                print("✅ SUCCESS: New validation is working! (70-byte limit)")
                return True
            else:
                print(f"🤔 Different error: {error_msg}")
                return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def monitor_deployment(max_attempts=10, wait_seconds=30):
    """Monitor deployment until fixes are live"""
    
    print("🚀 Monitoring Deployment Status")
    print("=" * 50)
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔍 Attempt {attempt}/{max_attempts}")
        
        if test_deployment_status():
            print(f"\n🎉 Deployment successful after {attempt} attempts!")
            return True
        
        if attempt < max_attempts:
            print(f"⏳ Waiting {wait_seconds} seconds before next check...")
            time.sleep(wait_seconds)
    
    print(f"\n⚠️  Deployment not detected after {max_attempts} attempts")
    print("💡 You may need to check Render dashboard for deployment status")
    return False

if __name__ == "__main__":
    monitor_deployment()