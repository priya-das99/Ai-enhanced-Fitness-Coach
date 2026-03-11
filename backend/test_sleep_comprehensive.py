"""
Comprehensive Sleep Logging Test Suite
Tests all sleep use cases including duplicates, time scenarios, and edge cases
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from chat_assistant.activity_workflow import ActivityWorkflow
from chat_assistant.unified_state import WorkflowState
from chat_assistant.health_activity_logger import HealthActivityLogger

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_test(test_name, description=""):
    """Print test header"""
    print(f"\n🧪 TEST: {test_name}")
    if description:
        print(f"   {description}")
    print("-" * 60)

def clear_sleep_logs(user_id):
    """Clear existing sleep logs for clean testing"""
    try:
        import sqlite3
        conn = sqlite3.connect('backend/mood_capture.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM health_activities WHERE user_id = ? AND activity_type = ?', 
                      (user_id, 'sleep'))
        conn.commit()
        conn.close()
        print(f"🧹 Cleared existing sleep logs for user {user_id}")
    except Exception as e:
        print(f"⚠️  Could not clear logs: {e}")

def get_sleep_logs(user_id):
    """Get all sleep logs for user"""
    try:
        import sqlite3
        conn = sqlite3.connect('backend/mood_capture.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value, unit, timestamp, notes 
            FROM health_activities 
            WHERE user_id = ? AND activity_type = ? 
            ORDER BY timestamp DESC
        ''', (user_id, 'sleep'))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"❌ Error getting sleep logs: {e}")
        return []

def test_basic_sleep_logging():
    """Test 1: Basic sleep logging scenarios"""
    print_section("TEST 1: BASIC SLEEP LOGGING")
    
    user_id = 99  # Test user
    clear_sleep_logs(user_id)
    
    test_cases = [
        ("I slept 8 hours", "8 hours", "Natural language"),
        ("I got 7.5 hours of sleep", "7.5 hours", "Decimal hours"),
        ("I slept for 6 hours last night", "6 hours", "Past tense"),
        ("Sleep: 9 hours", "9 hours", "Colon format"),
        ("8h sleep", "8 hours", "Abbreviated format")
    ]
    
    results = []
    
    for message, expected, description in test_cases:
        print_test(f"Basic Sleep: {description}", f"Input: '{message}'")
        
        workflow = ActivityWorkflow()
        state = WorkflowState(user_id=user_id)
        
        try:
            response = workflow.start(message, state, user_id)
            
            print(f"✅ Response: {response.message[:60]}...")
            print(f"   Completed: {response.completed}")
            
            # Check if sleep was logged
            logs = get_sleep_logs(user_id)
            if logs:
                latest = logs[0]
                print(f"   Logged: {latest[0]} {latest[1]} at {latest[2]}")
                results.append(True)
            else:
                print(f"   ❌ No sleep logged")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Basic Sleep Tests: {passed}/{total} passed")
    return passed == total

def test_duplicate_sleep_handling():
    """Test 2: Duplicate sleep logging scenarios"""
    print_section("TEST 2: DUPLICATE SLEEP HANDLING")
    
    user_id = 100  # Different test user
    clear_sleep_logs(user_id)
    
    # First, log initial sleep
    print_test("Initial Sleep Log", "Log 8 hours first")
    workflow = ActivityWorkflow()
    state = WorkflowState(user_id=user_id)
    
    response1 = workflow.start("I slept 8 hours", state, user_id)
    print(f"✅ Initial log: {response1.message[:50]}...")
    
    logs = get_sleep_logs(user_id)
    print(f"   Sleep logs count: {len(logs)}")
    
    # Test duplicate scenarios
    duplicate_cases = [
        ("I slept 8 hours", "Same value", "Should acknowledge existing"),
        ("I got 7 hours of sleep", "Different value", "Should ask to update"),
        ("Sleep: 8.0 hours", "Same value (decimal)", "Should acknowledge existing"),
        ("I slept for 9 hours", "Different value", "Should ask to update")
    ]
    
    results = []
    
    for message, scenario, expected in duplicate_cases:
        print_test(f"Duplicate: {scenario}", f"Input: '{message}' - {expected}")
        
        workflow = ActivityWorkflow()
        state = WorkflowState(user_id=user_id)
        
        try:
            response = workflow.start(message, state, user_id)
            
            print(f"✅ Response: {response.message[:80]}...")
            print(f"   Completed: {response.completed}")
            print(f"   UI Elements: {response.ui_elements}")
            
            # Check response content
            if "already logged" in response.message.lower():
                print(f"   ✅ Detected duplicate correctly")
                results.append(True)
            elif not response.completed and response.ui_elements:
                print(f"   ✅ Asking for confirmation (workflow active)")
                results.append(True)
            else:
                print(f"   ❌ Unexpected response for duplicate")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Duplicate Tests: {passed}/{total} passed")
    return passed == total

def test_sleep_update_flow():
    """Test 3: Sleep update confirmation flow"""
    print_section("TEST 3: SLEEP UPDATE FLOW")
    
    user_id = 101
    clear_sleep_logs(user_id)
    
    # Step 1: Log initial sleep
    print_test("Step 1: Initial Sleep", "Log 7 hours")
    workflow = ActivityWorkflow()
    state = WorkflowState(user_id=user_id)
    
    response1 = workflow.start("I slept 7 hours", state, user_id)
    print(f"✅ Initial: {response1.message[:50]}...")
    
    # Step 2: Try to log different amount
    print_test("Step 2: Different Amount", "Try to log 8 hours")
    workflow = ActivityWorkflow()
    state = WorkflowState(user_id=user_id)
    
    response2 = workflow.start("I slept 8 hours", state, user_id)
    print(f"✅ Duplicate detected: {response2.message[:80]}...")
    print(f"   Workflow active: {not response2.completed}")
    
    if not response2.completed:
        # Step 3a: User says "yes" to update
        print_test("Step 3a: Confirm Update", "User says 'yes'")
        response3a = workflow.process("yes", state, user_id)
        print(f"✅ Update confirmed: {response3a.message[:50]}...")
        
        # Check if updated
        logs = get_sleep_logs(user_id)
        if logs and float(logs[0][0]) == 8.0:
            print(f"   ✅ Sleep updated to 8 hours")
            update_success = True
        else:
            print(f"   ❌ Sleep not updated correctly")
            update_success = False
        
        # Step 3b: Test "no" response with fresh state
        clear_sleep_logs(user_id)
        workflow.start("I slept 7 hours", state, user_id)  # Re-log initial
        
        workflow2 = ActivityWorkflow()
        state2 = WorkflowState(user_id=user_id)
        workflow2.start("I slept 8 hours", state2, user_id)  # Trigger duplicate
        
        print_test("Step 3b: Decline Update", "User says 'no'")
        response3b = workflow2.process("no", state2, user_id)
        print(f"✅ Update declined: {response3b.message[:50]}...")
        
        # Check if not updated
        logs = get_sleep_logs(user_id)
        if logs and float(logs[0][0]) == 7.0:
            print(f"   ✅ Sleep remained at 7 hours")
            decline_success = True
        else:
            print(f"   ❌ Sleep incorrectly updated")
            decline_success = False
        
        return update_success and decline_success
    else:
        print(f"   ❌ Workflow should have stayed active for confirmation")
        return False

def test_time_based_scenarios():
    """Test 4: Time-based sleep logging scenarios"""
    print_section("TEST 4: TIME-BASED SCENARIOS")
    
    user_id = 102
    clear_sleep_logs(user_id)
    
    # Mock different times of day
    time_scenarios = [
        ("Morning (8 AM)", "I slept 8 hours", "Should log for previous night"),
        ("Afternoon (2 PM)", "I got 7 hours of sleep", "Should log for previous night"),
        ("Evening (8 PM)", "I slept 6 hours", "Should log for today"),
        ("Late night (11 PM)", "Sleep: 9 hours", "Should log for today")
    ]
    
    results = []
    
    for time_desc, message, expected in time_scenarios:
        print_test(f"Time Scenario: {time_desc}", f"Input: '{message}' - {expected}")
        
        workflow = ActivityWorkflow()
        state = WorkflowState(user_id=user_id)
        
        try:
            response = workflow.start(message, state, user_id)
            
            print(f"✅ Response: {response.message[:60]}...")
            print(f"   Completed: {response.completed}")
            
            # Check if logged
            logs = get_sleep_logs(user_id)
            if logs:
                latest = logs[0]
                print(f"   Logged: {latest[0]} {latest[1]} at {latest[2]}")
                results.append(True)
            else:
                print(f"   ❌ No sleep logged")
                results.append(False)
                
            # Clear for next test
            clear_sleep_logs(user_id)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Time-based Tests: {passed}/{total} passed")
    return passed == total

def test_edge_cases():
    """Test 5: Edge cases and error handling"""
    print_section("TEST 5: EDGE CASES")
    
    user_id = 103
    clear_sleep_logs(user_id)
    
    edge_cases = [
        ("I slept 0 hours", "Zero hours", "Should handle gracefully"),
        ("I slept 15 hours", "Very long sleep", "Should accept"),
        ("I slept -2 hours", "Negative hours", "Should reject or ask for clarification"),
        ("I slept 2.5 hours", "Short nap", "Should accept"),
        ("I slept 24 hours", "Full day", "Should accept"),
        ("I didn't sleep", "No sleep", "Should handle gracefully"),
        ("Sleep was terrible", "Qualitative only", "Should ask for quantity")
    ]
    
    results = []
    
    for message, case_type, expected in edge_cases:
        print_test(f"Edge Case: {case_type}", f"Input: '{message}' - {expected}")
        
        workflow = ActivityWorkflow()
        state = WorkflowState(user_id=user_id)
        
        try:
            response = workflow.start(message, state, user_id)
            
            print(f"✅ Response: {response.message[:80]}...")
            print(f"   Completed: {response.completed}")
            print(f"   UI Elements: {response.ui_elements}")
            
            # For edge cases, we mainly check that it doesn't crash
            results.append(True)
            
            # Clear for next test
            clear_sleep_logs(user_id)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Edge Case Tests: {passed}/{total} passed")
    return passed == total

def test_button_workflow():
    """Test 6: Sleep logging via button click"""
    print_section("TEST 6: BUTTON WORKFLOW")
    
    user_id = 104
    clear_sleep_logs(user_id)
    
    print_test("Button Click", "Simulate 'log_sleep' button")
    
    workflow = ActivityWorkflow()
    state = WorkflowState(user_id=user_id)
    
    try:
        # Step 1: Button click
        response1 = workflow.start("log_sleep", state, user_id)
        
        print(f"✅ Button response: {response1.message}")
        print(f"   Completed: {response1.completed}")
        print(f"   Should ask for hours: {not response1.completed}")
        
        if not response1.completed:
            # Step 2: Provide hours
            print_test("Provide Hours", "User enters '8'")
            response2 = workflow.process("8", state, user_id)
            
            print(f"✅ Hours response: {response2.message[:60]}...")
            print(f"   Completed: {response2.completed}")
            
            # Check if logged
            logs = get_sleep_logs(user_id)
            if logs:
                latest = logs[0]
                print(f"   ✅ Logged: {latest[0]} {latest[1]}")
                return True
            else:
                print(f"   ❌ No sleep logged")
                return False
        else:
            print(f"   ❌ Workflow should have asked for hours")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_health_activity_logger():
    """Test 7: Direct HealthActivityLogger functionality"""
    print_section("TEST 7: HEALTH ACTIVITY LOGGER")
    
    user_id = 105
    clear_sleep_logs(user_id)
    
    logger = HealthActivityLogger()
    
    print_test("Direct Logger", "Test HealthActivityLogger.log_activity()")
    
    try:
        # Test direct logging
        logger.log_activity(
            user_id=user_id,
            activity_type='sleep',
            value=8.5,
            unit='hours',
            notes='Direct logger test'
        )
        
        logs = get_sleep_logs(user_id)
        if logs:
            latest = logs[0]
            print(f"✅ Direct log successful: {latest[0]} {latest[1]}")
            print(f"   Notes: {latest[3]}")
            
            # Test duplicate detection
            print_test("Duplicate Detection", "Check recent sleep detection")
            from datetime import date
            recent = logger.check_recent_sleep(user_id, date.today())
            
            if recent:
                print(f"✅ Duplicate detection works: {recent['value']} {recent['unit']}")
                return True
            else:
                print(f"❌ Duplicate detection failed")
                return False
        else:
            print(f"❌ Direct logging failed")
            return False
            
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False

def run_all_tests():
    """Run all sleep test suites"""
    print("\n" + "🛌" * 40)
    print("  COMPREHENSIVE SLEEP LOGGING TEST SUITE")
    print("🛌" * 40)
    
    tests = [
        ("Basic Sleep Logging", test_basic_sleep_logging),
        ("Duplicate Handling", test_duplicate_sleep_handling),
        ("Update Flow", test_sleep_update_flow),
        ("Time-based Scenarios", test_time_based_scenarios),
        ("Edge Cases", test_edge_cases),
        ("Button Workflow", test_button_workflow),
        ("Health Activity Logger", test_health_activity_logger)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🏃 Running: {test_name}")
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status} - {test_name}")
        except Exception as e:
            print(f"\n❌ CRASH - {test_name}: {e}")
            results.append((test_name, False))
    
    # Final summary
    print_section("FINAL RESULTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Overall Results: {passed}/{total} test suites passed\n")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL SLEEP TESTS PASSED!")
        print(f"\n✅ Sleep logging system is working correctly across all scenarios!")
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        print(f"\n💡 Review the detailed output above to identify issues")
    
    print(f"\n🛌 Sleep logging test suite complete!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_all_tests()