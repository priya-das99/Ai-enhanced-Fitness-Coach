#!/usr/bin/env python3
"""
Test mood logging button
"""

import sys
sys.path.insert(0, '.')

from chat_assistant.chat_engine_workflow import process_message

def test_mood_button():
    """Test that mood button works correctly"""
    user_id = 2
    
    print("\n" + "="*60)
    print("Testing Mood Logging Button")
    print("="*60)
    
    # Test: Log Mood button
    print("\n1. Testing Log Mood button...")
    response = process_message(user_id, "log_mood")
    print(f"   Response: {response['message']}")
    print(f"   UI Elements: {response.get('ui_elements', [])}")
    print(f"   State: {response.get('state')}")
    print(f"   Completed: {response.get('completed')}")
    
    # Select a mood
    print("\n2. Selecting mood emoji...")
    response = process_message(user_id, "😊")
    print(f"   Response: {response['message']}")
    print(f"   Completed: {response.get('completed')}")
    
    print("\n" + "="*60)
    print("✅ Mood button test completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_mood_button()
