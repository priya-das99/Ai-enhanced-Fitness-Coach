#!/usr/bin/env python3
"""
Test the full conversation flow with Ankur's actual queries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_assistant.chat_engine_workflow import get_chat_engine

def test_conversation():
    """Simulate the exact conversation from the user"""
    
    engine = get_chat_engine()
    user_id = 1  # Ankur
    
    print("=" * 80)
    print("SIMULATING ANKUR'S CONVERSATION")
    print("=" * 80)
    
    conversation = [
        "1",  # Log 1 glass of water
        "Did I meet my goals for water intake till now?",
        "How many glasses do I need to drink more today to complete today's challenge?",
        "What are the current challenges?",
        "what are the five challenges",
        "what is my progress"
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"\n{'=' * 80}")
        print(f"MESSAGE {i}: '{message}'")
        print('=' * 80)
        
        try:
            response = engine.process_message(user_id, message)
            
            print(f"\nBot Response:")
            print(f"   {response['message'][:300]}...")
            print(f"\n   State: {response.get('state', 'unknown')}")
            print(f"   Completed: {response.get('completed', False)}")
            print(f"   UI Elements: {len(response.get('ui_elements', []))}")
            
            # Check if response is generic/wrong
            if "challenge(s) available to join" in response['message'] and i > 1:
                print(f"\nPROBLEM DETECTED: Generic 'available challenges' response")
                print(f"   Expected: Specific answer to user's question")
                print(f"   Got: Generic suggestion to join challenges")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    test_conversation()
