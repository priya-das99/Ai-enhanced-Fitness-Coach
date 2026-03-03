#!/usr/bin/env python3
"""Test challenge chat workflow"""

import sys
sys.path.insert(0, '.')

from chat_assistant.challenges_workflow import ChallengesWorkflow
from chat_assistant.unified_state import WorkflowState

def test_challenge_chat():
    print("\n=== Testing Challenge Chat Workflow ===\n")
    
    workflow = ChallengesWorkflow()
    state = WorkflowState(user_id=1)
    
    test_messages = [
        "How am I doing?",
        "Show my challenges",
        "What challenges do I have?"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        try:
            response = workflow.start(msg, state, user_id=1)
            print(f"Bot: {response.message[:300]}...")
            print("✓ Success!")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== All tests passed! ===\n")

if __name__ == "__main__":
    test_challenge_chat()
