import sqlite3
import os

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'mood_capture.db')

def get_connection():
    """
    Get a database connection with timeout.
    
    Timeout prevents immediate lock failures when multiple requests
    try to write to SQLite simultaneously.
    """
    conn = sqlite3.connect(DATABASE, timeout=10.0)  # 10 second timeout
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