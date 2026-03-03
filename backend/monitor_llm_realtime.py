"""
Real-time LLM Usage Monitor
Watches for new LLM calls and displays them as they happen
"""
import sqlite3
import time
from datetime import datetime
import sys

def get_connection():
    return sqlite3.connect('backend/mood_capture.db')

def get_last_call_id():
    """Get the ID of the most recent LLM call"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(id) FROM llm_usage_log')
    result = cursor.fetchone()[0]
    conn.close()
    return result or 0

def monitor_llm_calls():
    """Monitor LLM calls in real-time"""
    print("=" * 80)
    print("🔍 REAL-TIME LLM USAGE MONITOR")
    print("=" * 80)
    print("Watching for new LLM calls... (Press Ctrl+C to stop)\n")
    
    last_id = get_last_call_id()
    total_cost = 0.0
    total_tokens = 0
    call_count = 0
    
    try:
        while True:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get new calls since last check
            cursor.execute('''
                SELECT 
                    id, user_id, call_type, model, input_tokens, output_tokens,
                    total_tokens, estimated_cost, latency_ms, success,
                    error_message, timestamp
                FROM llm_usage_log
                WHERE id > ?
                ORDER BY id ASC
            ''', (last_id,))
            
            new_calls = cursor.fetchall()
            conn.close()
            
            for call in new_calls:
                call_id, user_id, call_type, model, input_tokens, output_tokens, \
                total_tokens_call, cost, latency, success, error, timestamp = call
                
                # Update counters
                call_count += 1
                total_cost += cost
                total_tokens += total_tokens_call
                
                # Display call
                status = "✅" if success else "❌"
                print(f"\n[{timestamp}] {status} LLM Call #{call_count}")
                print(f"   Type: {call_type}")
                print(f"   User: {user_id or 'System'}")
                print(f"   Tokens: {input_tokens} → {output_tokens} ({total_tokens_call} total)")
                print(f"   Cost: ${cost:.4f}")
                print(f"   Latency: {latency}ms")
                if error:
                    print(f"   ⚠️  Error: {error}")
                
                # Show running totals
                print(f"\n   📊 Session Totals: {call_count} calls | {total_tokens:,} tokens | ${total_cost:.4f}")
                print("-" * 80)
                
                last_id = call_id
            
            # Wait before checking again
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("📊 MONITORING SESSION SUMMARY")
        print("=" * 80)
        print(f"   Total Calls: {call_count}")
        print(f"   Total Tokens: {total_tokens:,}")
        print(f"   Total Cost: ${total_cost:.4f}")
        if call_count > 0:
            print(f"   Avg Tokens/Call: {total_tokens/call_count:.0f}")
            print(f"   Avg Cost/Call: ${total_cost/call_count:.4f}")
        print("=" * 80)
        print("\n👋 Monitoring stopped.")

if __name__ == "__main__":
    monitor_llm_calls()
