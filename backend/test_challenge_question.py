#!/usr/bin/env python3
"""
Test the exact question from user
"""

import sys
sys.path.insert(0, '.')
from chat_assistant.chat_engine_workflow import get_chat_engine

engine = get_chat_engine()
user_id = 1  # Ankur

query = "what more glass required to complete hydration challenge"

print("=" * 80)
print(f"Testing query: '{query}'")
print("=" * 80)

response = engine.process_message(user_id, query)

print(f"\nResponse:")
message = response['message'].encode('ascii', 'ignore').decode('ascii')
print(message)

print(f"\nState: {response.get('state')}")
print(f"Completed: {response.get('completed')}")
