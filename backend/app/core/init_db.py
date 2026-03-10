# app/core/init_db.py
# Database initialization for production

import os
import sqlite3
from app.core.security import get_password_hash
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def init_database():
    """Initialize database with all required tables"""
    try:
        # Ensure database directory exists
        db_path = settings.DATABASE_PATH
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Initializing database...")
        
        # Create users table
        if not table_exists(cursor, 'users'):
            logger.info("Creating users table...")
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')
        
        # Create other essential tables
        tables = [
            ('mood_logs', '''
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
            '''),
            ('chat_messages', '''
                CREATE TABLE chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            '''),
            ('health_activities', '''
                CREATE TABLE health_activities (
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
        ]
        
        for table_name, create_sql in tables:
            if not table_exists(cursor, table_name):
                logger.info(f"Creating {table_name} table...")
                cursor.execute(create_sql)
        
        # Create demo user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.info("Creating demo user...")
            demo_password_hash = get_password_hash('demo123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            ''', ('demo', 'demo@example.com', demo_password_hash, 'Demo User'))
            logger.info("Demo user created (username: demo, password: demo123)")
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise