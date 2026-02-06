import sqlite3
import os

DATABASE = 'mood.db'

def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create mood_logs table if it doesn't exist
    cursor.execute("CREATE TABLE IF NOT EXISTS mood_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, mood TEXT NOT NULL, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()