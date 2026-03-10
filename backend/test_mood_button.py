#!/usr/bin/env python3
"""
Test Mood Button Click
Test what happens when user clicks Log Mood button
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_mood_button_click():
    """Test mood button click processing"""
    print("🧪 Testing Log Mood button click...")
    
    try:
        from chat_assistant.chat_engine_workflow import process_message
        
        # Test the exact message sent by frontend when clicking Log Mood
        result = process_message(1, "I want to log_mood")
        
        print("✅ Mood button click test successful!")
        print(f"   Message: {result.get('message', 'N/A')[:100]}...")
        print(f"   UI Elements: {result.get('ui_elements', [])}")
        print(f"   State: {result.get('state', 'N/A')}")
        print(f"   Completed: {result.get('completed', 'N/A')}")
        
        # Check if emoji selector is shown
        if 'emoji_selector' in result.get('ui_elements', []):
            print("✅ Emoji selector is correctly shown!")
        else:
            print("❌ Emoji selector is NOT shown - this is the bug!")
            print(f"   Instead showing: {result.get('ui_elements', [])}")
        
        return result
        
    except Exception as e:
        print(f"❌ Mood button test error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_mood_workflow_direct():
    """Test mood workflow directly"""
    print("\n🧪 Testing mood workflow directly...")
    
    try:
        from chat_assistant.mood_workflow import MoodWorkflow
        from chat_assistant.unified_state import get_workflow_state
        
        workflow = MoodWorkflow()
        state = get_workflow_state(1)
        
        # Test with "Log Mood" message
        result = workflow.start("Log Mood", state, 1)
        
        print("✅ Direct mood workflow test successful!")
        print(f"   Message: {result.message[:100]}...")
        print(f"   UI Elements: {result.ui_elements}")
        print(f"   Completed: {result.completed}")
        print(f"   Next State: {result.next_state}")
        
        return result
        
    except Exception as e:
        print(f"❌ Direct mood workflow error: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_mood_logged_today():
    """Check if demo user has logged mood today"""
    print("\n🔍 Checking if demo user logged mood today...")
    
    try:
        from chat_assistant.mood_handler import has_logged_mood_today
        
        result = has_logged_mood_today(1)
        print(f"   Demo user logged mood today: {result}")
        
        if result:
            print("   This explains why 'already logged' message appears!")
            
            # Show recent mood logs
            import sqlite3
            conn = sqlite3.connect(os.path.join(backend_dir, 'mood_capture.db'))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT mood_emoji, mood, timestamp 
                FROM mood_logs 
                WHERE user_id = 1 AND DATE(timestamp) = DATE('now')
                ORDER BY timestamp DESC LIMIT 3
            """)
            
            today_moods = cursor.fetchall()
            print(f"   Today's mood logs ({len(today_moods)}):")
            for emoji, mood, timestamp in today_moods:
                print(f"     • {emoji} {mood} at {timestamp}")
            
            conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Error checking mood logs: {e}")
        return None

if __name__ == '__main__':
    print("🔍 Testing Log Mood Button Issue")
    print("=" * 50)
    
    # Check if user has logged mood today
    has_logged = check_mood_logged_today()
    
    # Test the button click
    test_mood_button_click()
    
    # Test mood workflow directly
    test_mood_workflow_direct()
    
    print(f"\n💡 DIAGNOSIS:")
    if has_logged:
        print("   The demo user has already logged moods today, so the system")
        print("   shows 'already logged' message but should still show emoji selector.")
        print("   The fix should keep the workflow active to handle emoji selection.")
    else:
        print("   The demo user hasn't logged mood today, so should show emoji selector.")