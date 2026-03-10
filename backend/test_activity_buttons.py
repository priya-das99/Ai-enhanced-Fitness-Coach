#!/usr/bin/env python3
"""
Test activity button logging
"""

import sys
sys.path.insert(0, '.')

from chat_assistant.chat_engine_workflow import process_message, init_conversation

def test_activity_buttons():
    """Test that activity buttons work correctly"""
    user_id = 1
    
    print("\n" + "="*60)
    print("Testing Activity Button Logging")
    print("="*60)
    
    # Test 1: Log Water
    print("\n1. Testing Log Water button...")
    response = process_message(user_id, "log_water")
    print(f"   Response: {response['message']}")
    print(f"   UI Elements: {response.get('ui_elements', [])}")
    print(f"   State: {response.get('state')}")
    
    # Provide quantity
    print("\n   Providing quantity: 8 glasses")
    response = process_message(user_id, "8")
    print(f"   Response: {response['message']}")
    print(f"   Completed: {response.get('completed')}")
    
    # Test 2: Log Sleep
    print("\n2. Testing Log Sleep button...")
    response = process_message(user_id, "log_sleep")
    print(f"   Response: {response['message']}")
    print(f"   UI Elements: {response.get('ui_elements', [])}")
    
    # Provide quantity
    print("\n   Providing quantity: 7.5 hours")
    response = process_message(user_id, "7.5")
    print(f"   Response: {response['message']}")
    print(f"   Completed: {response.get('completed')}")
    
    # Test 3: Log Exercise
    print("\n3. Testing Log Exercise button...")
    response = process_message(user_id, "log_exercise")
    print(f"   Response: {response['message']}")
    
    # Provide quantity
    print("\n   Providing quantity: 30 minutes")
    response = process_message(user_id, "30")
    print(f"   Response: {response['message']}")
    print(f"   Completed: {response.get('completed')}")
    
    # Test 4: Log Weight
    print("\n4. Testing Log Weight button...")
    response = process_message(user_id, "log_weight")
    print(f"   Response: {response['message']}")
    
    # Provide quantity
    print("\n   Providing quantity: 70 kg")
    response = process_message(user_id, "70")
    print(f"   Response: {response['message']}")
    print(f"   Completed: {response.get('completed')}")
    
    print("\n" + "="*60)
    print("✅ All activity button tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_activity_buttons()
