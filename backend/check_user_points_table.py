#!/usr/bin/env python3
"""Check if user_points table exists"""

import sqlite3

conn = sqlite3.connect('backend/mood_capture.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_points'")
result = cursor.fetchone()

if result:
    print("✓ user_points table exists")
    
    # Check data
    cursor.execute("SELECT * FROM user_points WHERE user_id = 1")
    row = cursor.fetchone()
    if row:
        print(f"  User 1 data: {row}")
    else:
        print("  No data for user 1")
else:
    print("✗ user_points table does NOT exist")

conn.close()
