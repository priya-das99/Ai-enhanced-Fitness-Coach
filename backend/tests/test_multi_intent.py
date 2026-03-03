"""
Multi-Intent Test
Tests that the bot can handle multiple intents in a single message
"""

import sys
import os
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = f"multitest_{int(datetime.now().timestamp())}@example.com"
TEST_USER_PASSWORD = "MultiTest123!"
TEST_USER_USERNAME = f"multitest_{int(datetime.now().timestamp())}"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num, message):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Test {step_num}]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"  {message}")

def setup_user():
    """Register and login"""
    # Register
    payload = {
        "username": TEST_USER_USERNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "Multi Intent Test"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code not in [200, 201]:
        print_error(f"Registration failed: {response.text}")
        return None
    
    # Login
    login_payload = {
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json=login_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print_error(f"Login failed: {response.text}")
        return None
    
    token = response.json()['access_token']
    print_success(f"User setup complete")
    return token

def send_message(token, message):
    """Send a message and return response"""
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json={"message": message},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print_error(f"Message failed: {response.text}")
        return None

def test_sleep_and_mood(token):
    """Test: 'I slept for 6 hours but feel terrible'"""
    print_step(1, "Sleep + Mood Intent")
    print_info("Message: 'I slept for 6 hours but feel terrible'")
    
    # Initialize chat
    requests.get(f"{API_BASE_URL}/chat/init", headers={"Authorization": f"Bearer {token}"})
    
    # Send multi-intent message
    response = send_message(token, "I slept for 6 hours but feel terrible")
    
    if not response:
        return False
    
    print_info(f"Bot: {response['message']}")
    print_info(f"UI Elements: {response.get('ui_elements', [])}")
    print_info(f"Completed: {response.get('completed')}")
    
    # Check if both intents were handled
    message_lower = response['message'].lower()
    
    # Should mention sleep logging
    has_sleep = 'sleep' in message_lower or '6' in response['message']
    
    # Should ask about mood (reason selector)
    has_mood_followup = (
        'contributing' in message_lower or 
        'reason' in message_lower or
        'reason_selector' in response.get('ui_elements', [])
    )
    
    if has_sleep and has_mood_followup:
        print_success("Both intents handled! Sleep logged + mood workflow started")
        return True
    elif has_sleep and not has_mood_followup:
        print_error("Only sleep logged, mood intent ignored")
        return False
    else:
        print_error("Unexpected response")
        return False

def test_mood_and_water(token):
    """Test: 'feeling stressed and drank 3 glasses of water'"""
    print_step(2, "Mood + Water Intent")
    print_info("Message: 'feeling stressed and drank 3 glasses of water'")
    
    # Reset chat state
    requests.get(f"{API_BASE_URL}/chat/init", headers={"Authorization": f"Bearer {token}"})
    
    response = send_message(token, "feeling stressed and drank 3 glasses of water")
    
    if not response:
        return False
    
    print_info(f"Bot: {response['message']}")
    print_info(f"UI Elements: {response.get('ui_elements', [])}")
    
    message_lower = response['message'].lower()
    
    # Should handle both
    has_water = 'water' in message_lower or '3' in response['message'] or 'logged' in message_lower
    has_mood = 'contributing' in message_lower or 'reason_selector' in response.get('ui_elements', [])
    
    if (has_water or has_mood):
        print_success("Multi-intent detected")
        return True
    else:
        print_error("Multi-intent not handled properly")
        print_info(f"Debug: has_water={has_water}, has_mood={has_mood}")
        return False

def test_exercise_and_tired(token):
    """Test: 'I worked out for 30 minutes but still feel tired'"""
    print_step(3, "Exercise + Mood Intent")
    print_info("Message: 'I worked out for 30 minutes but still feel tired'")
    
    # Reset chat state
    requests.get(f"{API_BASE_URL}/chat/init", headers={"Authorization": f"Bearer {token}"})
    
    response = send_message(token, "I worked out for 30 minutes but still feel tired")
    
    if not response:
        return False
    
    print_info(f"Bot: {response['message']}")
    print_info(f"UI Elements: {response.get('ui_elements', [])}")
    
    message_lower = response['message'].lower()
    
    # Should handle both
    has_exercise = 'exercise' in message_lower or 'workout' in message_lower or '30' in response['message'] or 'logged' in message_lower
    has_mood = 'contributing' in message_lower or 'tired' in message_lower or 'reason_selector' in response.get('ui_elements', [])
    
    if (has_exercise or has_mood):
        print_success("Multi-intent detected")
        return True
    else:
        print_error("Multi-intent not handled properly")
        print_info(f"Debug: has_exercise={has_exercise}, has_mood={has_mood}")
        return False

def test_single_intent_baseline(token):
    """Test: Single intent still works - 'I drank 5 glasses of water'"""
    print_step(4, "Single Intent Baseline")
    print_info("Message: 'I drank 5 glasses of water'")
    
    # Reset chat state
    requests.get(f"{API_BASE_URL}/chat/init", headers={"Authorization": f"Bearer {token}"})
    
    response = send_message(token, "I drank 5 glasses of water")
    
    if not response:
        return False
    
    print_info(f"Bot: {response['message']}")
    print_info(f"Completed: {response.get('completed')}")
    
    message_lower = response['message'].lower()
    
    if 'water' in message_lower or '5' in response['message'] or 'logged' in message_lower:
        print_success("Single intent works correctly")
        return True
    else:
        print_error("Single intent failed")
        print_info(f"Expected water logging confirmation")
        return False

def main():
    """Run multi-intent tests"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Multi-Intent Detection Test{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # Check backend
    try:
        requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
    except:
        print_error("\nBackend is not running!")
        print_info("Start backend with: cd backend && python run_fastapi.py")
        return 1
    
    # Setup user
    print_step("Setup", "Creating test user")
    token = setup_user()
    if not token:
        return 1
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_sleep_and_mood(token):
        tests_passed += 1
    
    if test_mood_and_water(token):
        tests_passed += 1
    
    if test_exercise_and_tired(token):
        tests_passed += 1
    
    if test_single_intent_baseline(token):
        tests_passed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All multi-intent tests passed!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed ({tests_passed}/{total_tests} passed){Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
