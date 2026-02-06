#!/usr/bin/env python3
"""
Database migration script to add the reason column to existing mood_logs table
"""

import sqlite3

def migrate_database():
    print("🔄 Starting database migration...")
    
    try:
        conn = sqlite3.connect('mood.db')
        cursor = conn.cursor()
        
        # Check if reason column already exists
        cursor.execute("PRAGMA table_info(mood_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'reason' in columns:
            print("✅ Reason column already exists. No migration needed.")
            conn.close()
            return
        
        # Add the reason column
        print("📝 Adding 'reason' column to mood_logs table...")
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN reason TEXT")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        print("The 'reason' column has been added to the mood_logs table.")
        
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    migrate_database()