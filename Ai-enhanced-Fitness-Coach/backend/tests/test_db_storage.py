"""
Database Storage Verification Test
Tests that mood and activity logs are actually stored in the database
"""

import sys
import os
import requests
import sqlite3
from datetime import datetime
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mood.db")
TEST_USER_EMAIL = f"dbtest_{int(datetime.now().timestamp())}@example.com"
TEST_USER_PASSWORD = "DBTest123!"
TEST_USER_USERNAME = f"dbtest_{int(datetime.now().timestamp())}"

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

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def register_and_login():
    """Register and login, return token and user_id"""
    # Register
    payload = {
        "username": TEST_USER_USERNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "DB Test User"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code not in [200, 201]:
        print_error(f"Registration failed: {response.text}")
        return None, None
    
    user_id = response.json().get('user_id')
    print_success(f"Registered user ID: {user_id}")
    
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
        return None, None
    
    token = response.json()['access_token']
    print_success(f"Login successful")
    
    return token, user_id

def test_mood_storage(token, user_id):
    """Test that mood logs are stored in database"""
    print_step(1, "Testing Mood Storage")
    
    # Initialize chat
    requests.get(
        f"{API_BASE_URL}/chat/init",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Log a mood
    payload = {"message": "😊"}
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        print_error(f"Mood logging API failed: {response.text}")
        return False
    
    print_success("Mood logged via API")
    
    # Wait a moment for DB write
    time.sleep(0.5)
    
    # Check database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, mood, reason, timestamp 
        FROM mood_logs 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print_success(f"Mood found in database!")
        print_info(f"  ID: {row[0]}")
        print_info(f"  User ID: {row[1]}")
        print_info(f"  Mood: {row[2]}")
        print_info(f"  Reason: {row[3]}")
        print_info(f"  Timestamp: {row[4]}")
        return True
    else:
        print_error("Mood NOT found in database")
        return False

def test_activity_storage(token, user_id):
    """Test that activity logs are stored in database"""
    print_step(2, "Testing Activity Storage")
    
    # Log water activity
    payload = {"message": "log_water"}
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        print_error(f"Water logging API failed: {response.text}")
        return False
    
    # Provide quantity
    time.sleep(0.3)
    payload = {"message": "5"}
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        print_error(f"Water quantity API failed: {response.text}")
        return False
    
    print_success("Water activity logged via API")
    
    # Wait for DB write
    time.sleep(0.5)
    
    # Check database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, activity_type, value, unit, timestamp 
        FROM health_activities 
        WHERE user_id = ? AND activity_type = 'water'
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print_success(f"Activity found in database!")
        print_info(f"  ID: {row[0]}")
        print_info(f"  User ID: {row[1]}")
        print_info(f"  Activity Type: {row[2]}")
        print_info(f"  Value: {row[3]}")
        print_info(f"  Unit: {row[4]}")
        print_info(f"  Timestamp: {row[5]}")
        return True
    else:
        print_error("Activity NOT found in database")
        return False

def test_analytics_events(token, user_id):
    """Test that analytics events are stored"""
    print_step(3, "Testing Analytics Events Storage")
    
    # Check database for analytics events
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM analytics_events 
        WHERE user_id = ?
    """, (user_id,))
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        print_success(f"Found {count} analytics events in database")
        
        # Show recent events
        cursor.execute("""
            SELECT event_type, event_data, created_at 
            FROM analytics_events 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        
        rows = cursor.fetchall()
        print_info("Recent events:")
        for row in rows:
            print_info(f"  - {row[0]}: {row[1][:50]}... at {row[2]}")
        
        conn.close()
        return True
    else:
        print_error("No analytics events found in database")
        conn.close()
        return False

def check_database_tables():
    """Verify database tables exist"""
    print_step(0, "Checking Database Tables")
    
    if not os.path.exists(DB_PATH):
        print_error(f"Database not found at: {DB_PATH}")
        return False
    
    print_success(f"Database found at: {DB_PATH}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    required_tables = ['users', 'mood_logs', 'health_activities', 'analytics_events']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print_error(f"Missing tables: {', '.join(missing_tables)}")
        print_info(f"Available tables: {', '.join(tables)}")
        return False
    
    print_success(f"All required tables exist")
    print_info(f"Tables: {', '.join(tables)}")
    return True

def main():
    """Run database storage verification test"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Database Storage Verification Test{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # Check backend
    try:
        requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
    except:
        print_error("\nBackend is not running!")
        print_info("Start backend with: cd backend && python run_fastapi.py")
        return 1
    
    # Check database
    if not check_database_tables():
        return 1
    
    # Register and login
    print_step("Setup", "Register and Login")
    token, user_id = register_and_login()
    if not token or not user_id:
        print_error("Failed to setup test user")
        return 1
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_mood_storage(token, user_id):
        tests_passed += 1
    
    if test_activity_storage(token, user_id):
        tests_passed += 1
    
    if test_analytics_events(token, user_id):
        tests_passed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All database storage tests passed!{Colors.END}")
        print(f"{Colors.GREEN}Data is being correctly stored in the database.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed ({tests_passed}/{total_tests} passed){Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
