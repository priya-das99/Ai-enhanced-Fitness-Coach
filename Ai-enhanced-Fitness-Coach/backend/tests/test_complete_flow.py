"""
Complete Flow Test
Tests the entire user journey: register → login → chat → mood logging → activity logging
"""

import sys
import os
import requests
import json
from datetime import datetime
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = f"flowtest_{datetime.now().timestamp()}@example.com"
TEST_USER_PASSWORD = "FlowTest123!"
TEST_USER_USERNAME = f"flowtest_{int(datetime.now().timestamp())}"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num, message):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step_num}]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"  {message}")

def step1_register():
    """Step 1: Register a new user"""
    print_step(1, "Register New User")
    
    payload = {
        "username": TEST_USER_USERNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "Flow Test User"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            data = response.json()
            username = data.get('username')
            print_success(f"Registered user: {username}")
            return True
        else:
            print_error(f"Registration failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception during registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def step2_login():
    """Step 2: Login with the registered user"""
    print_step(2, "Login")
    
    payload = {
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print_success(f"Login successful, token: {token[:20]}...")
        return token
    else:
        print_error(f"Login failed: {response.text}")
        return None

def step3_init_chat(token):
    """Step 3: Initialize chat conversation"""
    print_step(3, "Initialize Chat")
    
    response = requests.get(
        f"{API_BASE_URL}/chat/init",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Chat initialized: {data.get('message', '')[:50]}...")
        return True
    else:
        print_error(f"Chat init failed: {response.text}")
        return False

def step4_send_mood_message(token):
    """Step 4: Send mood logging message"""
    print_step(4, "Log Mood (Negative)")
    
    payload = {
        "message": "😟"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Mood logged: {data.get('message', '')[:50]}...")
        print_info(f"UI Elements: {data.get('ui_elements', [])}")
        return True
    else:
        print_error(f"Mood logging failed: {response.text}")
        return False

def step5_send_reason(token):
    """Step 5: Send reason for negative mood"""
    print_step(5, "Provide Reason")
    
    payload = {
        "message": "work"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Reason provided: {data.get('message', '')[:80]}...")
        return True
    else:
        print_error(f"Reason submission failed: {response.text}")
        return False

def step6_log_activity(token):
    """Step 6: Log water activity"""
    print_step(6, "Log Water Activity")
    
    # First, trigger water logging
    payload = {
        "message": "log_water"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Water logging started: {data.get('message', '')}")
        
        # Now provide quantity
        time.sleep(0.5)
        payload2 = {
            "message": "8"
        }
        
        response2 = requests.post(
            f"{API_BASE_URL}/chat/message",
            json=payload2,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            print_success(f"Water logged: {data2.get('message', '')}")
            return True
        else:
            print_error(f"Water quantity failed: {response2.text}")
            return False
    else:
        print_error(f"Water logging failed: {response.text}")
        return False

def step7_check_analytics(token):
    """Step 7: Check analytics data"""
    print_step(7, "Check Analytics")
    
    response = requests.get(
        f"{API_BASE_URL}/analytics/events/summary?days=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Analytics retrieved")
        print_info(f"Total events: {data.get('total_events', 0)}")
        print_info(f"Event counts: {data.get('event_counts', {})}")
        return True
    else:
        print_error(f"Analytics failed: {response.text}")
        return False

def main():
    """Run complete flow test"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Complete User Flow Test{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # Check backend
    try:
        requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
    except:
        print_error("\nBackend is not running!")
        print_info("Start backend with: cd backend && python run_fastapi.py")
        return 1
    
    # Run flow
    steps_passed = 0
    total_steps = 7
    
    # Step 1: Register
    if step1_register():
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Registration failed")
        return 1
    
    # Step 2: Login
    token = step2_login()
    if token:
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Login failed")
        return 1
    
    # Step 3: Init Chat
    if step3_init_chat(token):
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Chat init failed")
        return 1
    
    # Step 4: Log Mood
    if step4_send_mood_message(token):
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Mood logging failed")
        return 1
    
    # Step 5: Send Reason
    if step5_send_reason(token):
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Reason submission failed")
        return 1
    
    # Step 6: Log Activity
    if step6_log_activity(token):
        steps_passed += 1
    else:
        print_error("\nFlow stopped: Activity logging failed")
        return 1
    
    # Step 7: Check Analytics
    if step7_check_analytics(token):
        steps_passed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Flow Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Steps Completed: {steps_passed}/{total_steps}")
    
    if steps_passed == total_steps:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Complete flow test passed!{Colors.END}")
        print(f"\n{Colors.GREEN}The application is working end-to-end!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Flow partially completed ({steps_passed}/{total_steps} steps){Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
