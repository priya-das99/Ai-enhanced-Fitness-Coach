#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_assistant.activity_validator import ActivityValidator

def test_validation_fixes():
    """Test the validation fixes"""
    validator = ActivityValidator()
    
    print("🧪 TESTING VALIDATION FIXES")
    print("=" * 50)
    
    # Test exercise validation
    result = validator.validate_activity_input('exercise', 300)
    print(f"Exercise 300 minutes: {result}")
    expected_invalid = not result['valid']
    print(f"✅ Expected invalid: {expected_invalid}")
    
    # Test exercise warning threshold
    result = validator.validate_activity_input('exercise', 150)
    print(f"Exercise 150 minutes: {result}")
    expected_warning = result.get('needs_confirmation', False)
    print(f"✅ Expected warning: {expected_warning}")
    
    # Test normal exercise
    result = validator.validate_activity_input('exercise', 30)
    print(f"Exercise 30 minutes: {result}")
    expected_valid = result['valid'] and not result.get('needs_confirmation', False)
    print(f"✅ Expected valid: {expected_valid}")

if __name__ == "__main__":
    test_validation_fixes()