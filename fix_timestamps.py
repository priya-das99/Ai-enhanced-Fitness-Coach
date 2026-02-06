#!/usr/bin/env python3
"""
Script to fix existing timestamps in the database
This will convert UTC timestamps to local time
"""

import sqlite3
from datetime import datetime, timezone, timedelta

def fix_timestamps():
    print("🔧 Fixing existing timestamps in database...")
    
    conn = sqlite3.connect('mood.db')
    cursor = conn.cursor()
    
    # Get all existing records
    cursor.execute("SELECT id, timestamp FROM mood_logs")
    records = cursor.fetchall()
    
    if not records:
        print("No records found to fix.")
        return
    
    print(f"Found {len(records)} records to fix:")
    
    # Assuming your timezone is about 5-6 hours ahead of UTC
    # You can adjust this offset based on your actual timezone
    timezone_offset_hours = 6  # Change this to match your timezone offset
    
    for record_id, old_timestamp in records:
        try:
            # Parse the old timestamp
            dt = datetime.fromisoformat(old_timestamp)
            
            # Add timezone offset to convert from UTC to local time
            local_dt = dt + timedelta(hours=timezone_offset_hours)
            new_timestamp = local_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Update the record
            cursor.execute(
                "UPDATE mood_logs SET timestamp = ? WHERE id = ?",
                (new_timestamp, record_id)
            )
            
            print(f"  ID {record_id}: {old_timestamp} → {new_timestamp}")
            
        except Exception as e:
            print(f"  ❌ Error fixing record ID {record_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ Timestamp fix completed!")
    print("\nRun 'python check_logs.py' to verify the changes.")

if __name__ == "__main__":
    # Ask for confirmation
    print("This will update all existing timestamps in your database.")
    print("Current timestamps appear to be in UTC, this will convert them to local time.")
    
    response = input("Do you want to proceed? (y/N): ").lower().strip()
    
    if response == 'y' or response == 'yes':
        fix_timestamps()
    else:
        print("Operation cancelled.")