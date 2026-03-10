#!/usr/bin/env python3
"""
Test how the system handles tired/sleepy queries
"""

import sys
sys.path.insert(0, '.')

from chat_assistant.chat_engine_workflow import process_message

def test_tired_queries():
    """Test various ways users might express being tired"""
    user_id = 3
    
    queries = [
        "I am tired",
        "I am sleepy",
        "what should I do?",
        "I am feeling sleepy",
        "I'm exhausted",
        "feeling tired",
    ]
    
    print("\n" + "="*80)
    print("TESTING TIRED/SLEEPY QUERIES")
    print("="*80 + "\n")
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"{'='*80}")
        
        try:
            response = process_message(user_id, query)
            
            print(f"\nResponse: {response.get('message', 'No message')[:200]}...")
            print(f"\nUI Elements: {response.get('ui_elements', [])}")
            print(f"State: {response.get('state', 'unknown')}")
            
            # Check if suggestions were provided
            if 'suggestions' in response:
                print(f"\nSuggestions provided: {len(response['suggestions'])}")
                for i, sugg in enumerate(response['suggestions'][:3], 1):
                    print(f"  {i}. {sugg.get('name', 'Unknown')}")
            
            # Check for action buttons
            if 'actions' in response:
                print(f"\nActions provided: {len(response['actions'])}")
                for i, action in enumerate(response['actions'][:3], 1):
                    print(f"  {i}. {action.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_tired_queries()
