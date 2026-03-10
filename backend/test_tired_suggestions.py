#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import get_smart_suggestions
from chat_assistant.context_builder_simple import build_context

user_id = 3
context = build_context(user_id)

print("\n=== Testing 'tired' reason ===\n")

suggestions = get_smart_suggestions(
    mood_emoji="😴",
    reason="tired",
    context=context,
    count=5
)

print(f"Got {len(suggestions)} suggestions:\n")

for i, sugg in enumerate(suggestions, 1):
    print(f"{i}. {sugg['name']}")
    print(f"   ID: {sugg['id']}")
    print(f"   Category: {sugg.get('category', 'N/A')}")
    print(f"   Tags: {sugg.get('best_for', [])}")
    is_content = sugg.get('action_type') == 'open_external'
    print(f"   Type: {'Content' if is_content else 'Activity'}\n")
