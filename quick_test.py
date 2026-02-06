#!/usr/bin/env python3
"""
Quick test - simulate ONE user clicking for a suggestion
Run this anytime to see if OpenAI API is working and how many tokens it uses
"""

import openai
from llm_service import llm_service

# Track the API call
api_called = False
tokens_used = 0

_original = openai.ChatCompletion.create

def track(*args, **kwargs):
    global api_called, tokens_used
    api_called = True
    response = _original(*args, **kwargs)
    tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
    return response

openai.ChatCompletion.create = track

# Simulate one user click
print("\n" + "="*60)
print("Quick Test: Simulating ONE user clicking for suggestion")
print("="*60)

mood = "horrible"
reason = "work_stress"

print(f"\nUser input: mood='{mood}', reason='{reason}'")
print("Processing...\n")

try:
    suggestion, source = llm_service.select_suggestion_with_llm(mood, reason, "test_user")
    
    print("="*60)
    print("RESULT:")
    print("="*60)
    print(f"✓ Suggestion: {suggestion}")
    print(f"✓ Source: {source}")
    
    if api_called:
        print(f"✓ OpenAI API was called")
        print(f"✓ Tokens used: {tokens_used}")
        cost = (tokens_used / 1_000_000) * 0.15  # Approximate
        print(f"✓ Estimated cost: ${cost:.6f}")
    else:
        print(f"✓ No API call (used fallback rules)")
    
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n✗ Error: {e}\n")
