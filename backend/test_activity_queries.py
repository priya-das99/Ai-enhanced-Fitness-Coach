#!/usr/bin/env python3
"""
Test activity summary queries through the chat engine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_assistant.chat_engine_workflow import get_chat_engine

def test_activity_queries():
    """Test activity summary queries for Ankur (user_id=1)"""
    
    engine = get_chat_engine()
    user_id = 1  # Ankur
    
    test_queries = [
        "What did I do today?",
        "How much water did I drink?",
        "Did I exercise today?",
        "What's my progress?",
        "Show me my activities"
    ]
    
    print("=" * 80)
    print("TESTING ACTIVITY SUMMARY QUERIES")
    print(f"User: Ankur (ID: {user_id})")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 80)
        
        try:
            response = engine.process_message(user_id, query)
            
            # Remove emojis for Windows console
            message = response['message'].encode('ascii', 'ignore').decode('ascii')
            
            print(f"Response:\n{message}\n")
            print(f"State: {response.get('state')}")
            print(f"Completed: {response.get('completed')}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_activity_queries()
