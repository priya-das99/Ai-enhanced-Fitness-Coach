# init_db.py
# Initialize database with all required tables

from db import get_connection
import hashlib

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Create all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Drop old mood_logs if exists and recreate with proper schema
    cursor.execute('DROP TABLE IF EXISTS mood_logs')
    
    # Mood logs table
    cursor.execute('''
        CREATE TABLE mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            reason_category TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Action suggestions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_log_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            action_name TEXT NOT NULL,
            accepted BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mood_log_id) REFERENCES mood_logs(id)
        )
    ''')
    
    # Chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_end DATETIME,
            messages_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # User activity history table (NEW!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            completed BOOLEAN DEFAULT 1,
            duration_minutes INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            day_of_week TEXT,
            time_of_day TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Health activities table for water, sleep, weight tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            value REAL,
            unit TEXT,
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create demo user (username: demo, password: demo123)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        ''', ('demo', 'demo@example.com', hash_password('demo123'), 'Demo User'))
        print("✅ Demo user created (username: demo, password: demo123)")
    except Exception as e:
        print(f"ℹ️  Demo user already exists or error: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - mood_logs (updated schema)")
    print("  - action_suggestions")
    print("  - chat_sessions")
    print("  - user_activity_history (NEW!)")
    print("  - health_activities (NEW!)")

if __name__ == '__main__':
    init_database()
