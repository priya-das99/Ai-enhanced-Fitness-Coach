#!/usr/bin/env python3
"""
Migration 008: Add suggestion_ranking_context table
For logging ranking decisions and optimizing weights
"""

import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade(conn):
    """Create suggestion_ranking_context table"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("MIGRATION 008: Add suggestion_ranking_context table")
    print("="*80 + "\n")
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='suggestion_ranking_context'
        """)
        
        if cursor.fetchone():
            print("✓ Table suggestion_ranking_context already exists")
            return
        
        # Create table
        print("Creating suggestion_ranking_context table...")
        cursor.execute("""
            CREATE TABLE suggestion_ranking_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mood_emoji TEXT,
                reason TEXT,
                algorithm_name TEXT,
                ranked_suggestions TEXT,
                user_context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        print("✓ Created suggestion_ranking_context table")
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX idx_ranking_context_user_timestamp 
            ON suggestion_ranking_context(user_id, timestamp)
        """)
        
        print("✓ Created index on user_id and timestamp")
        
        # Don't close connection - let migration runner handle it
        print("\n✅ Migration 008 completed successfully!\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}\n")
        raise

if __name__ == "__main__":
    migrate()
