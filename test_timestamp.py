#!/usr/bin/env python3
"""
Test script to verify timestamp handling
"""

from datetime import datetime
import sqlite3

def test_timestamp():
    print("🕐 Testing timestamp handling...")
    
    # Show current time
    now = datetime.now()
    print(f"Current local time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Formatted: {now.strftime('%Y-%m-%d %I:%M:%S %p')}")
    
    # Test database connection
    conn = sqlite3.connect('mood.db')
    cursor = conn.cursor()
    
    # Insert a test record with local timestamp
    local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO mood_logs (user_id, mood, timestamp) VALUES (?, ?, ?)",
        ('test_user', 'testing', local_timestamp)
    )
    
    conn.commit()
    
    # Retrieve the record
    cursor.execute("SELECT * FROM mood_logs WHERE user_id = 'test_user' ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        print(f"\n✅ Test record inserted:")
        print(f"ID: {result[0]}, User: {result[1]}, Mood: {result[2]}, Timestamp: {result[3]}")
        
        # Clean up test record
        cursor.execute("DELETE FROM mood_logs WHERE user_id = 'test_user'")
        conn.commit()
        print("🧹 Test record cleaned up")
    
    conn.close()

if __name__ == "__main__":
    test_timestamp()