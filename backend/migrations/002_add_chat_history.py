"""
Migration: Add chat history table
Stores all chat messages for conversation persistence
"""

import sqlite3
import os

def run_migration():
    """Add chat_messages table"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mood.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create chat_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            sender TEXT NOT NULL,  -- 'user' or 'bot'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,  -- JSON for additional data (ui_elements, etc.)
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_user_timestamp 
        ON chat_messages(user_id, timestamp DESC)
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Migration 002: chat_messages table created")

if __name__ == '__main__':
    run_migration()
