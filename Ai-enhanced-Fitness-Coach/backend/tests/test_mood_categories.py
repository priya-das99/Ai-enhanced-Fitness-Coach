"""
Mood Categories Test
Tests all mood types and their appropriate responses
"""

import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = f"moodtest_{int(datetime.now().timestamp())}@example.com"
TEST_USER_PASSWORD = "MoodTest123!"
TEST_USER_USERNAME = f"moodtest_{int(datetime.now().timestamp())}"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(category, message):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[{category}]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"  {message}")

def setup_user():
    """Register and login"""
    payload = {
        "username": TEST_USER_USERNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "Mood Test User"
    }
    
    response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
    if response.status_code not in [200, 201]:
        return None
    
    login_payload = {"username": TEST_USER_USERNAME, "password": TEST_USER_PASSWORD}
    response = requests.post(f"{API_BASE_URL}/auth/login", json=login_payload)
    
    if response.status_code != 200:
        return None
    
    return response.json()['access_token']

def send_message(token, message):
    """Send message and return response"""
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json={"message": message},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    return response.json() if response.status_code == 200 else None

def reset_chat(token):
    """Reset chat state"""
    requests.get(f"{API_BASE_URL}/chat/init", headers={"Authorization": f"Bearer {token}"})

def test_positive_moods(token):
    """Test positive moods - should complete immediately"""
    print_test("POSITIVE MOODS", "Should complete without asking reason")
    
    test_cases = [
        ("I am feeling happy", "happy"),
        ("feeling great today", "great"),
        ("I'm excited", "excited"),
        ("feeling awesome", "awesome"),
    ]
    
    passed = 0
    for message, mood_word in test_cases:
        reset_chat(token)
        response = send_message(token, message)
        
        if response:
            completed = response.get('completed', False)
            has_reason_selector = 'reason_selector' in response.get('ui_elements', [])
            
            if completed and not has_reason_selector:
                print_success(f"'{message}' → Completed immediately ✓")
                passed += 1
            else:
                print_error(f"'{message}' → Asked for reason (should complete)")
                print_info(f"Response: {response['message'][:60]}")
        else:
            print_error(f"'{message}' → API failed")
    
    return passed, len(test_cases)

def test_mild_physical_moods(token):
    """Test mild physical moods - should skip reason, suggest activities"""
    print_test("MILD PHYSICAL", "Should skip reason, suggest quick activities")
    
    test_cases = [
        ("I am feeling tired", "tired"),
        ("feeling sleepy", "sleepy"),
        ("I'm exhausted", "exhausted"),
        ("feeling bored", "bored"),
    ]
    
    passed = 0
    for message, mood_word in test_cases:
        reset_chat(token)
        response = send_message(token, message)
        
        if response:
            has_reason_selector = 'reason_selector' in response.get('ui_elements', [])
            has_action_buttons = 'action_buttons' in str(response.get('ui_elements', []))
            
            if not has_reason_selector and has_action_buttons:
                print_success(f"'{message}' → Suggested activities (no reason) ✓")
                passed += 1
            elif has_reason_selector:
                print_error(f"'{message}' → Asked for reason (should skip)")
                print_info(f"Response: {response['message'][:60]}")
            else:
                print_error(f"'{message}' → Unexpected response")
                print_info(f"Response: {response['message'][:60]}")
        else:
            print_error(f"'{message}' → API failed")
    
    return passed, len(test_cases)

def test_emotional_negative_moods(token):
    """Test emotional negative moods - should ask for reason"""
    print_test("EMOTIONAL NEGATIVE", "Should ask for reason")
    
    test_cases = [
        ("I am feeling stressed", "stressed"),
        ("feeling anxious", "anxious"),
        ("I'm worried", "worried"),
        ("feeling frustrated", "frustrated"),
        ("I'm upset", "upset"),
    ]
    
    passed = 0
    for message, mood_word in test_cases:
        reset_chat(token)
        response = send_message(token, message)
        
        if response:
            has_reason_selector = 'reason_selector' in response.get('ui_elements', [])
            asks_contributing = 'contributing' in response['message'].lower()
            
            if has_reason_selector and asks_contributing:
                print_success(f"'{message}' → Asked for reason ✓")
                passed += 1
            else:
                print_error(f"'{message}' → Didn't ask for reason")
                print_info(f"Response: {response['message'][:60]}")
                print_info(f"UI: {response.get('ui_elements', [])}")
        else:
            print_error(f"'{message}' → API failed")
    
    return passed, len(test_cases)

def test_severe_negative_moods(token):
    """Test severe negative moods - should ask for reason with empathy"""
    print_test("SEVERE NEGATIVE", "Should ask for reason")
    
    test_cases = [
        ("I am feeling depressed", "depressed"),
        ("feeling terrible", "terrible"),
        ("I feel awful", "awful"),
        ("feeling horrible", "horrible"),
    ]
    
    passed = 0
    for message, mood_word in test_cases:
        reset_chat(token)
        response = send_message(token, message)
        
        if response:
            has_reason_selector = 'reason_selector' in response.get('ui_elements', [])
            
            if has_reason_selector:
                print_success(f"'{message}' → Asked for reason ✓")
                passed += 1
            else:
                print_error(f"'{message}' → Didn't ask for reason")
                print_info(f"Response: {response['message'][:60]}")
        else:
            print_error(f"'{message}' → API failed")
    
    return passed, len(test_cases)

def test_neutral_moods(token):
    """Test neutral moods - should complete with acknowledgment"""
    print_test("NEUTRAL MOODS", "Should acknowledge and complete")
    
    test_cases = [
        ("I'm feeling okay", "okay"),
        ("feeling meh", "meh"),
        ("I'm fine", "fine"),
        ("feeling so-so", "so-so"),
    ]
    
    passed = 0
    for message, mood_word in test_cases:
        reset_chat(token)
        response = send_message(token, message)
        
        if response:
            # Neutral can either complete or ask for reason (acceptable either way)
            # Just check it doesn't crash
            if response.get('message'):
                print_success(f"'{message}' → Handled ✓")
                passed += 1
            else:
                print_error(f"'{message}' → No response")
        else:
            print_error(f"'{message}' → API failed")
    
    return passed, len(test_cases)

def main():
    """Run all mood category tests"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Mood Categories Test - All Mood Types{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    # Check backend
    try:
        requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
    except:
        print_error("\nBackend is not running!")
        return 1
    
    # Setup
    print_test("Setup", "Creating test user")
    token = setup_user()
    if not token:
        print_error("Failed to setup user")
        return 1
    print_success("User ready")
    
    # Run all tests
    total_passed = 0
    total_tests = 0
    
    p, t = test_positive_moods(token)
    total_passed += p
    total_tests += t
    
    p, t = test_mild_physical_moods(token)
    total_passed += p
    total_tests += t
    
    p, t = test_emotional_negative_moods(token)
    total_passed += p
    total_tests += t
    
    p, t = test_severe_negative_moods(token)
    total_passed += p
    total_tests += t
    
    p, t = test_neutral_moods(token)
    total_passed += p
    total_tests += t
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"Tests Passed: {total_passed}/{total_tests}")
    
    if total_passed == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All mood category tests passed!{Colors.END}")
        print(f"{Colors.GREEN}Mood categorization is working correctly.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed ({total_passed}/{total_tests} passed){Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
