#!/usr/bin/env python3
"""
Debug Chat Init Issue
Test the chat init functionality directly
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_mood_handler():
    """Test mood handler functions"""
    print("🧪 Testing mood handler...")
    
    try:
        from chat_assistant.mood_handler import has_logged_mood_today
        
        # Test with user ID 1 (demo user)
        result = has_logged_mood_today(1)
        print(f"✅ has_logged_mood_today(1): {result}")
        
        # Test with string user ID
        result = has_logged_mood_today("1")
        print(f"✅ has_logged_mood_today('1'): {result}")
        
    except Exception as e:
        print(f"❌ Mood handler error: {e}")
        import traceback
        traceback.print_exc()

def test_workflow_state():
    """Test workflow state"""
    print("\n🧪 Testing workflow state...")
    
    try:
        from chat_assistant.unified_state import get_workflow_state
        
        state = get_workflow_state(1)
        print(f"✅ Workflow state for user 1: {state}")
        
        state.complete_workflow()
        print("✅ Workflow state reset successful")
        
    except Exception as e:
        print(f"❌ Workflow state error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_engine_init():
    """Test chat engine init directly"""
    print("\n🧪 Testing chat engine init...")
    
    try:
        from chat_assistant.chat_engine_workflow import init_conversation
        
        result = init_conversation("1")  # String user ID
        print(f"✅ Chat engine init (string): {result}")
        
        result = init_conversation(1)  # Integer user ID
        print(f"✅ Chat engine init (int): {result}")
        
    except Exception as e:
        print(f"❌ Chat engine init error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_service():
    """Test chat service init"""
    print("\n🧪 Testing chat service...")
    
    try:
        from app.services.chat_service import ChatService
        
        chat_service = ChatService()
        result = chat_service.init_conversation(1)
        print(f"✅ Chat service init: {result}")
        
    except Exception as e:
        print(f"❌ Chat service error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Debugging Chat Init Issue")
    print("=" * 50)
    
    test_mood_handler()
    test_workflow_state()
    test_chat_engine_init()
    test_chat_service()