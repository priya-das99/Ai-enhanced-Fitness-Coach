#!/usr/bin/env python3
"""
Simple script to track LLM API usage when users click suggestions.
Run this to see how many API calls are made and tokens used.

Usage:
    python track_llm_usage.py [number_of_tests]
    
Example:
    python track_llm_usage.py 10
"""

import sys
import json
import time
from datetime import datetime
import openai

# Metrics storage
metrics = {
    "session_start": datetime.now().isoformat(),
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "total_tokens": 0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "calls": []
}

# Monkey-patch OpenAI to track usage
_original_create = openai.ChatCompletion.create

def tracked_create(*args, **kwargs):
    """Track OpenAI API calls"""
    start = time.time()
    
    try:
        response = _original_create(*args, **kwargs)
        duration = (time.time() - start) * 1000
        
        # Extract usage
        usage = response.usage if hasattr(response, 'usage') else None
        tokens = usage.total_tokens if usage else 0
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        
        # Update metrics
        metrics["successful_calls"] += 1
        metrics["total_tokens"] += tokens
        metrics["total_prompt_tokens"] += prompt_tokens
        metrics["total_completion_tokens"] += completion_tokens
        metrics["calls"].append({
            "timestamp": datetime.now().isoformat(),
            "tokens": tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "duration_ms": round(duration, 2)
        })
        
        print(f"  ✓ API call #{metrics['successful_calls']}: {tokens} tokens ({duration:.0f}ms)")
        return response
        
    except Exception as e:
        metrics["failed_calls"] += 1
        print(f"  ✗ API call failed: {e}")
        raise
    finally:
        metrics["total_calls"] += 1

openai.ChatCompletion.create = tracked_create

# Import after patching
from llm_service import llm_service


def test_suggestion(mood, reason, user_id="test_user"):
    """Test a single suggestion"""
    try:
        suggestion, source = llm_service.select_suggestion_with_llm(mood, reason, user_id)
        return suggestion, source
    except Exception as e:
        print(f"  Error: {e}")
        return None, "error"


def main():
    num_tests = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    print("=" * 70)
    print("LLM API USAGE TRACKER")
    print("=" * 70)
    print(f"\nRunning {num_tests} test suggestions...\n")
    
    # Test scenarios
    test_cases = [
        ("horrible", "work_stress"),
        ("not good", "sleep"),
        ("tired", "work_stress"),
        ("horrible", "relationship"),
        ("not good", None),
        ("tired", "sleep"),
        ("horrible", "health"),
        ("not good", "work_stress"),
        ("tired", None),
        ("horrible", None),
    ]
    
    for i in range(num_tests):
        mood, reason = test_cases[i % len(test_cases)]
        print(f"Test {i+1}/{num_tests}: mood='{mood}', reason='{reason}'")
        
        suggestion, source = test_suggestion(mood, reason, f"user{i+1}")
        print(f"  → {suggestion} (source: {source})")
        
        if i < num_tests - 1:
            time.sleep(1.5)  # Rate limiting
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nAPI Calls:")
    print(f"  Total: {metrics['total_calls']}")
    print(f"  Successful: {metrics['successful_calls']}")
    print(f"  Failed: {metrics['failed_calls']}")
    
    if metrics['successful_calls'] > 0:
        print(f"\nTokens:")
        print(f"  Total: {metrics['total_tokens']}")
        print(f"  Prompt: {metrics['total_prompt_tokens']}")
        print(f"  Completion: {metrics['total_completion_tokens']}")
        print(f"  Average/call: {metrics['total_tokens']/metrics['successful_calls']:.1f}")
        
        # Cost (gpt-4o-mini: $0.150/1M input, $0.600/1M output)
        cost = (metrics['total_prompt_tokens']/1_000_000 * 0.150 + 
                metrics['total_completion_tokens']/1_000_000 * 0.600)
        print(f"\nEstimated Cost:")
        print(f"  Total: ${cost:.6f}")
        print(f"  Per call: ${cost/metrics['successful_calls']:.6f}")
    
    # Save to file
    filename = f"llm_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n✓ Detailed metrics saved to {filename}")
    print("=" * 70)


if __name__ == "__main__":
    main()
