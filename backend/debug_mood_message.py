#!/usr/bin/env python3
"""
Debug Mood Message Processing
Test the mood workflow specifically
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_mood_workflow_direct():
    """Test mood workflow directly"""
    print("🧪 Testing mood workflow directly...")
    
    try:
        from chat_assistant.mood_workflow import MoodWorkflow
        
        workflow = MoodWorkflow()
        
        # Test processing a mood emoji
        result = workflow.process_message(1, "🙂")
        
        print("✅ Mood workflow direct test successful!")
        print(f"   Message: {result.get('message', 'N/A')[:100]}...")
        print(f"   State: {result.get('state', 'N/A')}")
        print(f"   Completed: {result.get('completed', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Mood workflow error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_mood_handler():
    """Test mood handler save function"""
    print("\n🧪 Testing mood handler save...")
    
    try:
        from chat_assistant.mood_handler import save_mood_log
        
        # Test saving a mood log
        result = save_mood_log(
            user_id=1,
            mood_emoji="😊",
            reason="Testing mood save"
        )
        
        print(f"✅ Mood save successful! ID: {result}")
        
    except Exception as e:
        print(f"❌ Mood save error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_service_message():
    """Test chat service message processing"""
    print("\n🧪 Testing chat service message processing...")
    
    try:
        from app.services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # Test processing a mood message
        result = chat_service.process_message(1, "🙂")
        
        print("✅ Chat service message test successful!")
        print(f"   Message: {result.get('message', 'N/A')[:100]}...")
        print(f"   State: {result.get('state', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Chat service message error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_engine_message():
    """Test chat engine message processing"""
    print("\n🧪 Testing chat engine message processing...")
    
    try:
        from chat_assistant.chat_engine_workflow import process_message
        
        # Test processing a mood message
        result = process_message(1, "🙂")
        
        print("✅ Chat engine message test successful!")
        print(f"   Message: {result.get('message', 'N/A')[:100]}...")
        print(f"   State: {result.get('state', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Chat engine message error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Debugging Mood Message Processing")
    print("=" * 50)
    
    test_mood_workflow_direct()
    test_mood_handler()
    test_chat_service_message()
    test_chat_engine_message()