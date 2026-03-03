"""
View LLM Token Usage Statistics
Run this script to see token usage and costs
"""
from app.services.llm_token_tracker import LLMTokenTracker
from datetime import datetime
import sys

def print_separator(char="=", length=70):
    print(char * length)

def print_usage_stats(days=7):
    """Print usage statistics"""
    print_separator()
    print(f"LLM USAGE STATISTICS - Last {days} Days")
    print_separator()
    
    stats = LLMTokenTracker.get_usage_stats(days=days)
    
    # Overall stats
    print(f"\n📊 OVERALL STATS")
    print(f"   Total Calls: {stats['total_calls']:,}")
    print(f"   Total Tokens: {stats['total_tokens']:,}")
    print(f"   Total Cost: ${stats['total_cost']:.4f}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Avg Latency: {stats['avg_latency_ms']:.0f}ms")
    
    # By call type
    if stats['by_call_type']:
        print(f"\n📈 BY CALL TYPE")
        for call_type, data in stats['by_call_type'].items():
            print(f"\n   {call_type}:")
            print(f"      Calls: {data['calls']:,}")
            print(f"      Tokens: {data['tokens']:,}")
            print(f"      Cost: ${data['cost']:.4f}")
            print(f"      Avg Latency: {data['avg_latency_ms']:.0f}ms")
    
    # By day
    if stats['by_day']:
        print(f"\n📅 DAILY BREAKDOWN")
        print(f"   {'Date':<12} {'Calls':<8} {'Tokens':<10} {'Cost':<10}")
        print(f"   {'-'*12} {'-'*8} {'-'*10} {'-'*10}")
        for day in stats['by_day']:
            print(f"   {day['date']:<12} {day['calls']:<8} {day['tokens']:<10,} ${day['cost']:<9.4f}")
    
    # Projections
    if stats['total_calls'] > 0:
        print(f"\n💰 COST PROJECTIONS")
        daily_avg = stats['total_cost'] / days
        print(f"   Daily Average: ${daily_avg:.4f}")
        print(f"   Monthly Projection: ${daily_avg * 30:.2f}")
        print(f"   Yearly Projection: ${daily_avg * 365:.2f}")
    
    print_separator()

def print_recent_calls(limit=10):
    """Print recent LLM calls"""
    print_separator()
    print(f"RECENT LLM CALLS (Last {limit})")
    print_separator()
    
    calls = LLMTokenTracker.get_recent_calls(limit=limit)
    
    if not calls:
        print("\nNo LLM calls found.")
        return
    
    for i, call in enumerate(calls, 1):
        status = "✅" if call['success'] else "❌"
        print(f"\n{i}. {status} {call['call_type']} - {call['timestamp']}")
        print(f"   User ID: {call['user_id']}")
        print(f"   Tokens: {call['input_tokens']}→{call['output_tokens']} ({call['total_tokens']} total)")
        print(f"   Cost: ${call['estimated_cost']:.4f}")
        print(f"   Latency: {call['latency_ms']}ms")
        if call['error_message']:
            print(f"   Error: {call['error_message']}")
    
    print_separator()

def print_user_usage(user_id, days=30):
    """Print usage for specific user"""
    print_separator()
    print(f"LLM USAGE FOR USER {user_id} - Last {days} Days")
    print_separator()
    
    usage = LLMTokenTracker.get_user_usage(user_id, days=days)
    
    print(f"\n   Total Calls: {usage['total_calls']:,}")
    print(f"   Total Tokens: {usage['total_tokens']:,}")
    print(f"   Total Cost: ${usage['total_cost']:.4f}")
    
    if usage['total_calls'] > 0:
        avg_tokens = usage['total_tokens'] / usage['total_calls']
        avg_cost = usage['total_cost'] / usage['total_calls']
        print(f"\n   Avg Tokens per Call: {avg_tokens:.0f}")
        print(f"   Avg Cost per Call: ${avg_cost:.4f}")
    
    print_separator()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            print_usage_stats(days=days)
        
        elif command == "recent":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print_recent_calls(limit=limit)
        
        elif command == "user":
            if len(sys.argv) < 3:
                print("Usage: python view_llm_usage.py user <user_id> [days]")
                return
            user_id = int(sys.argv[2])
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            print_user_usage(user_id, days=days)
        
        else:
            print("Unknown command. Use: stats, recent, or user")
    
    else:
        # Default: show everything
        print_usage_stats(days=7)
        print("\n")
        print_recent_calls(limit=5)
        print("\n💡 TIP: Use 'python view_llm_usage.py stats 30' for 30-day stats")
        print("💡 TIP: Use 'python view_llm_usage.py recent 20' for last 20 calls")
        print("💡 TIP: Use 'python view_llm_usage.py user 18' for user-specific stats")

if __name__ == "__main__":
    main()
