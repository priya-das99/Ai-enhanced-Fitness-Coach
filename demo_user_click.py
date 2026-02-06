#!/usr/bin/env python3
"""
Simple demo showing exactly what happens when a user clicks for a suggestion.
This simulates the real user flow step-by-step.
"""

import openai
from datetime import datetime

# Track API calls
api_calls = []

# Intercept OpenAI calls
_original_create = openai.ChatCompletion.create

def tracked_create(*args, **kwargs):
    """Track when OpenAI API is called"""
    print("\n    🌐 Making OpenAI API call...")
    try:
        response = _original_create(*args, **kwargs)
        usage = response.usage
        
        call_info = {
            "tokens": usage.total_tokens,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "model": kwargs.get('model', 'unknown')
        }
        api_calls.append(call_info)
        
        print(f"    ✓ API responded successfully")
        print(f"    📊 Tokens used: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        return response
    except Exception as e:
        print(f"    ✗ API call failed: {e}")
        api_calls.append({"error": str(e)})
        raise

openai.ChatCompletion.create = tracked_create

# Import after patching
from llm_service import llm_service


def simulate_user_click(user_id, mood, reason):
    """Simulate what happens when user clicks for a suggestion"""
    
    print("\n" + "="*70)
    print(f"👤 USER ACTION: User '{user_id}' clicks 'Get Suggestion' button")
    print("="*70)
    print(f"📝 User Input:")
    print(f"   - Mood: {mood}")
    print(f"   - Reason: {reason or 'not specified'}")
    print(f"   - Time: {datetime.now().strftime('%I:%M %p')}")
    
    print(f"\n🔄 Processing...")
    
    # This is what happens in your backend when user clicks
    suggestion, source = llm_service.select_suggestion_with_llm(mood, reason, user_id)
    
    print(f"\n✅ RESPONSE TO USER:")
    print(f"   - Suggestion: {suggestion}")
    print(f"   - Source: {source}")
    
    if source == "openai_llm":
        print(f"   - 💰 OpenAI API was used (costs money)")
    else:
        print(f"   - 🆓 Fallback rules used (free)")
    
    return suggestion, source


def main():
    print("\n" + "="*70)
    print("DEMO: What Happens When User Clicks for Suggestion")
    print("="*70)
    print("\nThis simulates the exact flow in your app:")
    print("1. User fills mood form")
    print("2. User clicks 'Get Suggestion' button")
    print("3. Backend processes request")
    print("4. OpenAI API may be called (costs tokens)")
    print("5. User receives suggestion")
    
    # Simulate 3 different users clicking
    scenarios = [
        ("Alice", "horrible", "work_stress"),
        ("Bob", "tired", "sleep"),
        ("Carol", "not good", None),
    ]
    
    for user_id, mood, reason in scenarios:
        simulate_user_click(user_id, mood, reason)
        print()
    
    # Summary
    print("\n" + "="*70)
    print("📊 SESSION SUMMARY")
    print("="*70)
    
    successful_calls = [c for c in api_calls if 'error' not in c]
    failed_calls = [c for c in api_calls if 'error' in c]
    
    print(f"\n👥 Total user clicks: {len(scenarios)}")
    print(f"🌐 OpenAI API calls made: {len(api_calls)}")
    print(f"   ✓ Successful: {len(successful_calls)}")
    print(f"   ✗ Failed: {len(failed_calls)}")
    
    if successful_calls:
        total_tokens = sum(c['tokens'] for c in successful_calls)
        total_prompt = sum(c['prompt_tokens'] for c in successful_calls)
        total_completion = sum(c['completion_tokens'] for c in successful_calls)
        
        print(f"\n📊 Token Usage:")
        print(f"   Total: {total_tokens} tokens")
        print(f"   Prompt: {total_prompt} tokens")
        print(f"   Completion: {total_completion} tokens")
        print(f"   Average per call: {total_tokens/len(successful_calls):.1f} tokens")
        
        # Cost calculation (gpt-4o-mini pricing)
        input_cost = (total_prompt / 1_000_000) * 0.150
        output_cost = (total_completion / 1_000_000) * 0.600
        total_cost = input_cost + output_cost
        
        print(f"\n💰 Cost for this session:")
        print(f"   ${total_cost:.6f} (${total_cost/len(successful_calls):.6f} per user)")
        
        print(f"\n📈 Projected costs:")
        print(f"   100 users/day: ${total_cost * 100 / len(scenarios):.4f}/day")
        print(f"   1,000 users/day: ${total_cost * 1000 / len(scenarios):.4f}/day")
        print(f"   10,000 users/day: ${total_cost * 10000 / len(scenarios):.2f}/day")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
