#!/usr/bin/env python3
"""
Migration 010: Add best_for column to suggestion_master table
This column stores JSON array of keywords for better activity matching
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_connection

def upgrade(conn):
    """Add best_for column to suggestion_master table"""
    cursor = conn.cursor()
    
    try:
        print("Migration 010: Adding best_for column to suggestion_master...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(suggestion_master)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'best_for' in columns:
            print("  ✓ best_for column already exists")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE suggestion_master 
                ADD COLUMN best_for TEXT
            """)
            print("  ✓ Added best_for column")
        
        # Don't close connection - let migration runner handle it
        print("Migration 010 completed successfully!")
        
    except Exception as e:
        print(f"Migration 010 failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
