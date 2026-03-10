#!/usr/bin/env python3
"""
Fix Mood Logs Schema
Add missing columns to mood_logs table
"""

import sqlite3
import os

def get_db_path():
    """Get database path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, 'mood_capture.db')

def fix_mood_logs_schema():
    """Add missing columns to mood_logs table"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🔧 Fixing mood_logs schema...")
    
    try:
        # Check current columns
        cursor.execute("PRAGMA table_info(mood_logs)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {existing_columns}")
        
        # Define required columns with their types
        required_columns = {
            'mood_intensity': 'INTEGER',
            'stress_level': 'INTEGER', 
            'energy_level': 'INTEGER',
            'confidence_level': 'INTEGER',
            'tags': 'TEXT'
        }
        
        # Add missing columns
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                print(f"➕ Adding column: {column} {column_type}")
                cursor.execute(f"ALTER TABLE mood_logs ADD COLUMN {column} {column_type}")
            else:
                print(f"✅ Column {column} already exists")
        
        conn.commit()
        print("✅ mood_logs schema fixed successfully")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(mood_logs)")
        columns = cursor.fetchall()
        print("\n📊 Updated mood_logs schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error fixing schema: {e}")
        raise
    finally:
        conn.close()

def fix_chat_messages_issue():
    """Fix the chat_messages table issue"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("\n🔧 Checking chat_messages table...")
    
    try:
        # Check if chat_messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        if not cursor.fetchone():
            print("❌ chat_messages table doesn't exist - this is the real issue!")
            print("The chat engine is using the old db.py connection which points to a different database")
            return
        
        # Check if session_id column exists
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'session_id' not in columns:
            print("➕ Adding session_id column to chat_messages...")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER")
            print("✅ Added session_id column")
        else:
            print("✅ session_id column already exists")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error with chat_messages: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔒 Fixing Schema Issues")
    print("=" * 50)
    
    fix_mood_logs_schema()
    fix_chat_messages_issue()