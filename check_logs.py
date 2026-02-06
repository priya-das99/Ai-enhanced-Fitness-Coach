#!/usr/bin/env python3
"""
Simple script to check mood logs in the database
Usage: python check_logs.py
"""

import sqlite3
from datetime import datetime
import pytz

def check_logs():
    try:
        # Connect to database
        conn = sqlite3.connect('mood.db')
        cursor = conn.cursor()
        
        # Get all logs
        cursor.execute("SELECT * FROM mood_logs ORDER BY timestamp DESC")
        logs = cursor.fetchall()
        
        if not logs:
            print("📝 No mood logs found in the database.")
            return
        
        print(f"📊 Found {len(logs)} mood logs:")
        print("-" * 80)
        print(f"{'ID':<5} {'User ID':<15} {'Mood':<12} {'Reason':<15} {'Timestamp'}")
        print("-" * 80)
        
        for log in logs:
            log_id, user_id, mood, reason, timestamp = log
            # Handle None reason
            reason_display = reason if reason else "N/A"
            # Try to parse and format timestamp better
            try:
                # Parse the timestamp and format it nicely
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %I:%M:%S %p')
            except:
                formatted_time = timestamp
            
            print(f"{log_id:<5} {user_id:<15} {mood:<12} {reason_display:<15} {formatted_time}")
        
        # Show some stats
        print("\n📈 Mood Statistics:")
        cursor.execute("SELECT mood, COUNT(*) as count FROM mood_logs GROUP BY mood ORDER BY count DESC")
        mood_stats = cursor.fetchall()
        
        for mood, count in mood_stats:
            print(f"  {mood}: {count} times")
        
        # Show current time for reference
        print(f"\n🕐 Current time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_logs()