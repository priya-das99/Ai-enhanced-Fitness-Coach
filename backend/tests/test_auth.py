"""
Test Authentication Endpoints
Tests login and register functionality
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = f"test_{datetime.now().timestamp()}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_USERNAME = f"testuser_{int(datetime.now().timestamp())}"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(message):
    """Print test message"""
    print(f"\n{Colors.BLUE}[TEST]{Colors.END} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def test_backend_health():
    """Test if backend is running"""
    print_test("Testing backend health...")
    
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        
        if response.status_code == 200:
            print_success("Backend is running")
            return True
        else:
            print_error(f"Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on port 8000?")
        print_info("Start backend with: cd backend && python run_fastapi.py")
        return False
    except Exception as e:
        print_error(f"Error checking backend health: {e}")
        return False

def test_register():
    """Test user registration"""
    print_test("Testing user registration...")
    
    payload = {
        "username": TEST_USER_USERNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            data = response.json()
            print_success("User registered successfully")
            # Handle both response formats
            user_id = data.get('id') or data.get('user_id')
            username = data.get('username')
            email = data.get('email')
            print_info(f"User ID: {user_id}")
            print_info(f"Username: {username}")
            if email:
                print_info(f"Email: {email}")
            return True, data
        elif response.status_code == 400:
            print_error("Registration failed: User might already exist")
            print_info(f"Response: {response.text}")
            return False, None
        else:
            print_error(f"Registration failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Error during registration: {e}")
        return False, None

def test_login():
    """Test user login"""
    print_test("Testing user login...")
    
    # Use form data for login (OAuth2 standard)
    payload = {
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=payload,  # Use data, not json for form data
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Login successful")
            print_info(f"Access Token: {data.get('access_token')[:20]}...")
            print_info(f"Token Type: {data.get('token_type')}")
            return True, data.get('access_token')
        else:
            print_error(f"Login failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Error during login: {e}")
        return False, None

def test_get_current_user(token):
    """Test getting current user info"""
    print_test("Testing get current user...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Retrieved current user info")
            print_info(f"Username: {data.get('username')}")
            print_info(f"Email: {data.get('email')}")
            print_info(f"Full Name: {data.get('full_name')}")
            return True, data
        else:
            print_error(f"Failed to get user info with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Error getting user info: {e}")
        return False, None

def test_login_with_wrong_password():
    """Test login with wrong password"""
    print_test("Testing login with wrong password...")
    
    payload = {
        "username": TEST_USER_USERNAME,
        "password": "WrongPassword123!"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print_success("Correctly rejected wrong password")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error during test: {e}")
        return False

def test_duplicate_registration():
    """Test registering with duplicate email"""
    print_test("Testing duplicate registration...")
    
    payload = {
        "username": TEST_USER_USERNAME + "_duplicate",
        "email": TEST_USER_EMAIL,  # Same email
        "password": TEST_USER_PASSWORD,
        "full_name": "Duplicate User"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print_success("Correctly rejected duplicate email")
            return True
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error during test: {e}")
        return False

def main():
    """Run all authentication tests"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Authentication Tests{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # Test 1: Backend Health
    results['total'] += 1
    if test_backend_health():
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_error("\nBackend is not running. Please start it first.")
        print_info("Run: cd backend && python run_fastapi.py")
        return 1
    
    # Test 2: Register
    results['total'] += 1
    register_success, user_data = test_register()
    if register_success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 3: Login
    results['total'] += 1
    login_success, token = test_login()
    if login_success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 4: Get Current User (only if login succeeded)
    if login_success and token:
        results['total'] += 1
        if test_get_current_user(token)[0]:
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # Test 5: Wrong Password
    results['total'] += 1
    if test_login_with_wrong_password():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 6: Duplicate Registration
    results['total'] += 1
    if test_duplicate_registration():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Print Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
