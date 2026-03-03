# Test Suite

Comprehensive tests for the AI Fitness Chat Assistant backend.

## Prerequisites

1. **Backend must be running** on port 8000
2. **Python requests library** must be installed

```bash
pip install requests
```

## Running Tests

### Run All Tests
```bash
cd backend/tests
python run_all_tests.py
```

### Run Individual Test Suites

#### Authentication Tests
Tests login and register functionality:
```bash
cd backend/tests
python test_auth.py
```

Tests include:
- Backend health check
- User registration
- User login
- Get current user info
- Login with wrong password (should fail)
- Duplicate registration (should fail)

#### Complete Flow Test
Tests the entire user journey:
```bash
cd backend/tests
python test_complete_flow.py
```

Flow includes:
1. Register new user
2. Login
3. Initialize chat
4. Log mood (negative)
5. Provide reason
6. Log water activity
7. Check analytics

## Test Output

Tests use color-coded output:
- 🟢 Green: Success
- 🔴 Red: Failure
- 🔵 Blue: Test step
- 🟡 Yellow: Info/Warning

## What Tests Verify

### Authentication Tests
- ✅ Backend is running and accessible
- ✅ User registration works
- ✅ User login returns JWT token
- ✅ JWT token can access protected endpoints
- ✅ Wrong password is rejected
- ✅ Duplicate email is rejected

### Complete Flow Tests
- ✅ End-to-end user journey works
- ✅ Chat initialization works
- ✅ Mood logging workflow works
- ✅ Activity logging workflow works
- ✅ Analytics endpoints work
- ✅ JWT authentication works throughout

## Troubleshooting

### "Cannot connect to backend"
Make sure backend is running:
```bash
cd backend
python run_fastapi.py
```

Backend should be accessible at: http://localhost:8000

### "Module not found"
Install required dependencies:
```bash
pip install requests
```

### Tests fail with 401 Unauthorized
- Check that JWT token is being generated correctly
- Verify backend authentication is working
- Check database has users table

### Tests fail with 500 Internal Server Error
- Check backend logs for errors
- Verify database is initialized
- Run migration: `python migrations/001_add_analytics_tables.py`

## Adding New Tests

To add a new test file:

1. Create `test_<name>.py` in the tests folder
2. Follow the pattern from existing tests
3. Add to `run_all_tests.py` if you want it in the suite

Example test structure:
```python
import sys
import os
import requests

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000/api/v1"

def test_something():
    response = requests.get(f"{API_BASE_URL}/endpoint")
    assert response.status_code == 200
    return True

def main():
    if test_something():
        print("✓ Test passed")
        return 0
    else:
        print("✗ Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    cd backend
    python run_fastapi.py &
    sleep 5
    cd tests
    python run_all_tests.py
```

## Test Data

Tests create temporary users with timestamps to avoid conflicts:
- Username: `testuser_<timestamp>`
- Email: `test_<timestamp>@example.com`
- Password: `TestPassword123!`

Test data is NOT automatically cleaned up. You can manually clean the database if needed.

## Expected Results

When all tests pass, you should see:
```
✓ All test suites passed!
```

This confirms:
- Backend is running correctly
- Authentication works
- Chat workflows work
- Database operations work
- Analytics endpoints work
- The application is ready for use

---

**Last Updated**: 2026-02-18  
**Test Coverage**: Authentication, Chat, Mood Logging, Activity Logging, Analytics
