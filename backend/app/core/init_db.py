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

def migrate_existing_database(cursor):
    """Migrate existing database to add missing columns"""
    try:
        # Check if chat_sessions table exists
        if not table_exists(cursor, 'chat_sessions'):
            logger.info("Creating chat_sessions table...")
            cursor.execute('''
                CREATE TABLE chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        # Check if session_id column exists in chat_messages
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'session_id' not in columns:
            logger.info("Adding session_id column to chat_messages...")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER")
        
        # Check mood_logs columns
        cursor.execute("PRAGMA table_info(mood_logs)")
        mood_columns = [row[1] for row in cursor.fetchall()]
        
        missing_mood_columns = [
            ('mood_intensity', 'INTEGER'),
            ('stress_level', 'INTEGER'),
            ('energy_level', 'INTEGER'),
            ('confidence_level', 'INTEGER'),
            ('tags', 'TEXT')
        ]
        
        for col_name, col_type in missing_mood_columns:
            if col_name not in mood_columns:
                logger.info(f"Adding {col_name} column to mood_logs...")
                cursor.execute(f"ALTER TABLE mood_logs ADD COLUMN {col_name} {col_type}")
        
        logger.info("Database migration completed")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise

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
            ('chat_sessions', '''
                CREATE TABLE chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            '''),
            ('mood_logs', '''
                CREATE TABLE mood_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mood TEXT NOT NULL,
                    mood_emoji TEXT,
                    reason TEXT,
                    reason_category TEXT,
                    mood_intensity INTEGER,
                    stress_level INTEGER,
                    energy_level INTEGER,
                    confidence_level INTEGER,
                    tags TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            '''),
            ('chat_messages', '''
                CREATE TABLE chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id INTEGER,
                    message TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
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
        
        # Run migration for existing databases
        migrate_existing_database(cursor)
        
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