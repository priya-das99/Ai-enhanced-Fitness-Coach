#!/usr/bin/env python3
"""
Fix Schema Issues Safely
Add missing columns without losing data
"""

import sqlite3
import os

def get_db_path():
    """Get database path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, 'mood_capture.db')

def check_and_fix_schema():
    """Check schema and add missing columns safely"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🔧 Checking and fixing schema issues...")
    
    try:
        # Check if chat_messages has session_id column
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'session_id' not in columns:
            print("➕ Adding session_id column to chat_messages...")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER")
            print("✅ Added session_id column")
        else:
            print("✅ session_id column already exists")
        
        # Check other potential missing columns
        missing_fixes = []
        
        # Check if users table has all required columns
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        required_user_columns = ['id', 'username', 'email', 'password_hash', 'full_name', 'created_at', 'last_login']
        for col in required_user_columns:
            if col not in user_columns:
                missing_fixes.append(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        
        # Apply fixes
        for fix in missing_fixes:
            print(f"➕ Applying: {fix}")
            cursor.execute(fix)
        
        conn.commit()
        print("✅ Schema fixes applied successfully")
        
        # Show current row counts to confirm data is preserved
        print("\n📊 Current data (preserved):")
        tables_to_check = ['users', 'mood_logs', 'chat_messages', 'user_activity_history']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📋 {table}: {count} rows")
            except:
                print(f"  ❌ {table}: table not found")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error fixing schema: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔒 Safe Schema Fix")
    print("=" * 50)
    print("This will PRESERVE all your existing data")
    print("and only add missing columns.")
    print()
    
    check_and_fix_schema()