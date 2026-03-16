#!/usr/bin/env python3
"""
Migration 009: Fix Database Schema Errors
Addresses multiple missing columns and table issues
"""

import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    """Fix all database schema errors"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'mood_capture.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("MIGRATION 009: Fix Database Schema Errors")
    print("="*80 + "\n")
    
    try:
        # 1. Fix activities table - add best_for column
        print("1. Checking activities table for best_for column...")
        cursor.execute("PRAGMA table_info(activities)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'best_for' not in columns:
            print("   Adding best_for column to activities table...")
            cursor.execute("ALTER TABLE activities ADD COLUMN best_for TEXT")
            print("   ✓ Added best_for column to activities")
        else:
            print("   ✓ best_for column already exists in activities")
        
        # 2. Fix suggestions table - add best_for column if it exists
        print("\n2. Checking suggestions table for best_for column...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='suggestions'
        """)
        
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(suggestions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'best_for' not in columns:
                print("   Adding best_for column to suggestions table...")
                cursor.execute("ALTER TABLE suggestions ADD COLUMN best_for TEXT")
                print("   ✓ Added best_for column to suggestions")
            else:
                print("   ✓ best_for column already exists in suggestions")
        else:
            print("   ✓ suggestions table does not exist (skipping)")
        
        # 3. Fix suggestion_ranking_context table - add ranking_timestamp column
        print("\n3. Checking suggestion_ranking_context table for ranking_timestamp column...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='suggestion_ranking_context'
        """)
        
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(suggestion_ranking_context)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'ranking_timestamp' not in columns:
                print("   Adding ranking_timestamp column to suggestion_ranking_context table...")
                cursor.execute("ALTER TABLE suggestion_ranking_context ADD COLUMN ranking_timestamp DATETIME")
                print("   ✓ Added ranking_timestamp column")
            else:
                print("   ✓ ranking_timestamp column already exists")
        else:
            print("   ✓ suggestion_ranking_context table does not exist (skipping)")
        
        # 4. Fix user_activity_history table - add completion_percentage column
        print("\n4. Checking user_activity_history table for completion_percentage column...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_activity_history'
        """)
        
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(user_activity_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'completion_percentage' not in columns:
                print("   Adding completion_percentage column to user_activity_history table...")
                cursor.execute("ALTER TABLE user_activity_history ADD COLUMN completion_percentage FLOAT DEFAULT 0")
                print("   ✓ Added completion_percentage column with default value 0")
            else:
                print("   ✓ completion_percentage column already exists")
        else:
            print("   ✓ user_activity_history table does not exist (skipping)")
        
        # 5. Check smart_suggestions table exists and has best_for column
        print("\n5. Checking smart_suggestions table...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='smart_suggestions'
        """)
        
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(smart_suggestions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'best_for' not in columns:
                print("   Adding best_for column to smart_suggestions table...")
                cursor.execute("ALTER TABLE smart_suggestions ADD COLUMN best_for TEXT")
                print("   ✓ Added best_for column to smart_suggestions")
            else:
                print("   ✓ best_for column already exists in smart_suggestions")
        else:
            print("   ✓ smart_suggestions table does not exist (skipping)")
        
        conn.commit()
        print("\n✅ Migration 009 completed successfully!")
        print("\nSummary of changes:")
        print("- Added best_for column to activities table (if missing)")
        print("- Added best_for column to suggestions table (if exists and missing)")
        print("- Added ranking_timestamp column to suggestion_ranking_context table (if missing)")
        print("- Added completion_percentage column to user_activity_history table (if missing)")
        print("- Added best_for column to smart_suggestions table (if missing)")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()