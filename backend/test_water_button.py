#!/usr/bin/env python3
"""
Test Water Button Click
Test what happens when user clicks Log Water button
"""

import os
import sys
import json

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_water_button_click():
    """Test water button click processing"""
    print("🧪 Testing Log Water button click...")
    
    try:
        from chat_assistant.chat_engine_workflow import process_message
        
        # Test the exact message sent by frontend when clicking Log Water
        result = process_message(1, "I want to log_water")
        
        print("✅ Water button click test successful!")
        print(f"   Message: {result.get('message', 'N/A')}")
        print(f"   UI Elements: {result.get('ui_elements', [])}")
        print(f"   State: {result.get('state', 'N/A')}")
        print(f"   Completed: {result.get('completed', 'N/A')}")
        
        # Check all keys in response
        print(f"\n📋 All response keys:")
        for key, value in result.items():
            if key == 'message':
                continue  # Already printed above
            print(f"   {key}: {value}")
        
        # Check if there are suggestions being added
        if 'suggestions' in result:
            print(f"\n❌ FOUND SUGGESTIONS: {result['suggestions']}")
            print("   This is the bug - suggestions shouldn't be added to text input!")
        
        if 'activity_options' in result:
            print(f"\n❌ FOUND ACTIVITY_OPTIONS: {result['activity_options']}")
            print("   This is the bug - activity options shouldn't be added to text input!")
        
        return result
        
    except Exception as e:
        print(f"❌ Water button test error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_activity_workflow_direct():
    """Test activity workflow directly"""
    print("\n🧪 Testing activity workflow directly...")
    
    try:
        from chat_assistant.activity_workflow import ActivityWorkflow
        from chat_assistant.unified_state import get_workflow_state
        
        workflow = ActivityWorkflow()
        state = get_workflow_state(1)
        
        # Test with "log_water" message
        result = workflow.start("log_water", state, 1)
        
        print("✅ Direct activity workflow test successful!")
        print(f"   Message: {result.message}")
        print(f"   UI Elements: {result.ui_elements}")
        print(f"   Completed: {result.completed}")
        print(f"   Next State: {result.next_state}")
        print(f"   Extra Data: {result.extra_data}")
        
        return result
        
    except Exception as e:
        print(f"❌ Direct activity workflow error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("🔍 Testing Log Water Button Issue")
    print("=" * 50)
    
    # Test the button click
    result = test_water_button_click()
    
    # Test activity workflow directly
    test_activity_workflow_direct()
    
    print(f"\n💡 DIAGNOSIS:")
    if result:
        has_text_input = 'text_input' in result.get('ui_elements', [])
        has_suggestions = 'suggestions' in result or 'activity_options' in result
        
        if has_text_input and has_suggestions:
            print("   ❌ BUG CONFIRMED: Both text_input AND suggestions are being sent")
            print("   The frontend shows both, causing the confusing UI")
        elif has_text_input and not has_suggestions:
            print("   ✅ CORRECT: Only text_input is sent, no suggestions")
        elif not has_text_input and has_suggestions:
            print("   ❌ WRONG: Only suggestions sent, missing text_input")
        else:
            print("   ❌ BROKEN: Neither text_input nor suggestions sent")