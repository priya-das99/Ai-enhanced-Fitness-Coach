#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import get_smart_suggestions
from chat_assistant.context_builder_simple import build_context

user_id = 1
context = build_context(user_id)

scenarios = [
    ("😢", "work"),
    ("😟", "relationship"),
    ("😡", "traffic"),
]

for mood, reason in scenarios:
    print(f"\n{mood} {reason}:")
    suggestions = get_smart_suggestions(mood, reason, context, count=5)
    for i, s in enumerate(suggestions[:5], 1):
        print(f"  {i}. {s['id']}")
