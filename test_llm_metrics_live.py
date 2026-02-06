#!/usr/bin/env python3
"""
Live LLM metrics tracker - tracks actual token usage from OpenAI API
This script monkey-patches the OpenAI API to capture real usage data
"""

import json
import time
from datetime import datetime
import openai
from config import OPENAI_API_KEY, LLM_MODEL, ENABLE_LLM

# Storage for metrics
metrics = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "total_tokens": 0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "calls": []
}

# Store original create method
_original_create = openai.ChatCompletion.create

def tracked_create(*args, **kwargs):
    """Wrapper around OpenAI API to track usage"""
    call_start = time.time()
    call_data = {
        "timestamp": datetime.now().isoformat(),
        "model": kwargs.get('model', 'unknown'),
        "success": False,
        "tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "duration_ms": 0,
        "error": None
    }
    
    try:
        # Make the actual API call
        response = _original_create(*args, **kwargs)
        
        call_duration = (time.time() - call_start) * 1000
        call_data["duration_ms"] = round(call_duration, 2)
        call_data["success"] = True
        
        # Extract token usage from response
        if hasattr(response, 'usage'):
            usage = response.usage
            call_data["prompt_tokens"] = usage.prompt_tokens
            call_data["completion_tokens"] = usage.completion_tokens
            call_data["tokens"] = usage.total_tokens
            
            metrics["total_prompt_tokens"] += usage.prompt_tokens
            metrics["total_completion_tokens"] += usage.completion_tokens
            metrics["total_tokens"] += usage.total_tokens
        
        metrics["successful_calls"] += 1
        metrics["total_calls"] += 1
        metrics["calls"].append(call_data)
        
        print(f"\n✓ OpenAI API Call #{metrics['total_calls']}")
        print(f"  Model: {call_data['model']}")
        print(f"  Tokens: {call_data['tokens']} (prompt: {call_data['prompt_tokens']}, completion: {call_data['completion_tokens']})")
        print(f"  Duration: {call_data['duration_ms']}ms")
        
        return response
        
    except Exception as e:
        call_duration = (time.time() - call_start) * 1000
        call_data["duration_ms"] = round(call_duration, 2)
        call_data["error"] = str(e)
        
        metrics["failed_calls"] += 1
        metrics["total_calls"] += 1
        metrics["calls"].append(call_data)
        
        print(f"\n✗ OpenAI API Call #{metrics['total_calls']} FAILED")
        print(f"  Error: {e}")
        
        raise

# Monkey-patch the OpenAI API
openai.ChatCompletion.create = tracked_create

# Now import llm_service (after patching)
from llm_service import llm_service


def print_summary():
    """Print summary of all metrics"""
    print("\n" + "=" * 70)
    print("LLM API USAGE SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal API Calls: {metrics['total_calls']}")
    print(f"  ✓ Successful: {metrics['successful_calls']}")
    print(f"  ✗ Failed: {metrics['failed_calls']}")
    
    if metrics['total_calls'] > 0:
        success_rate = (metrics['successful_calls'] / metrics['total_calls']) * 100
        print(f"  Success Rate: {success_rate:.1f}%")
    
    print(f"\nToken Usage:")
    print(f"  Total Tokens: {metrics['total_tokens']}")
    print(f"  Prompt Tokens: {metrics['total_prompt_tokens']}")
    print(f"  Completion Tokens: {metrics['total_completion_tokens']}")
    
    if metrics['successful_calls'] > 0:
        avg_tokens = metrics['total_tokens'] / metrics['successful_calls']
        avg_prompt = metrics['total_prompt_tokens'] / metrics['successful_calls']
        avg_completion = metrics['total_completion_tokens'] / metrics['successful_calls']
        print(f"  Average per call: {avg_tokens:.1f} tokens ({avg_prompt:.1f} prompt + {avg_completion:.1f} completion)")
    
    # Cost estimation (gpt-4o-mini pricing)
    # Input: $0.150 per 1M tokens, Output: $0.600 per 1M tokens
    input_cost = (metrics['total_prompt_tokens'] / 1_000_000) * 0.150
    output_cost = (metrics['total_completion_tokens'] / 1_000_000) * 0.600
    total_cost = input_cost + output_cost
    
    print(f"\nEstimated Cost (gpt-4o-mini):")
    print(f"  Input: ${input_cost:.6f}")
    print(f"  Output: ${output_cost:.6f}")
    print(f"  Total: ${total_cost:.6f}")
    
    if metrics['successful_calls'] > 0:
        cost_per_call = total_cost / metrics['successful_calls']
        print(f"  Per call: ${cost_per_call:.6f}")
    
    print("\n" + "=" * 70)


def save_metrics(filename="llm_metrics_live.json"):
    """Save metrics to JSON file"""
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n✓ Metrics saved to {filename}")


def run_test_scenarios():
    """Run test scenarios simulating user clicking suggestions"""
    
    print("=" * 70)
    print("LIVE LLM API METRICS TRACKER")
    print("=" * 70)
    print(f"\nLLM Enabled: {ENABLE_LLM}")
    print(f"API Key: {'SET' if OPENAI_API_KEY else 'NOT SET'}")
    print(f"Model: {LLM_MODEL}")
    print("\nSimulating user clicking suggestions...\n")
    
    # Test scenarios - different moods and reasons
    scenarios = [
        ("horrible", "work_stress", "user1"),
        ("not good", "sleep", "user2"),
        ("tired", "work_stress", "user3"),
        ("horrible", "relationship", "user1"),
        ("not good", None, "user2"),
    ]
    
    for i, (mood, reason, user_id) in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(scenarios)}: User clicks suggestion")
        print(f"{'='*70}")
        print(f"Mood: {mood}")
        print(f"Reason: {reason or 'not specified'}")
        print(f"User: {user_id}")
        
        try:
            suggestion, source = llm_service.select_suggestion_with_llm(mood, reason, user_id)
            print(f"\nResult:")
            print(f"  Suggestion: {suggestion}")
            print(f"  Source: {source}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        # Delay between calls (rate limiting)
        if i < len(scenarios):
            print(f"\nWaiting 1.5s before next call...")
            time.sleep(1.5)
    
    # Print final summary
    print_summary()
    
    # Save metrics
    save_metrics()


if __name__ == "__main__":
    run_test_scenarios()
