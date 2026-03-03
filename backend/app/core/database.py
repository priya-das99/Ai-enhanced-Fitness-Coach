# app/core/database.py
# Database connection management

import sqlite3
from contextlib import contextmanager
from app.config import settings

def get_db_connection():
    """Get SQLite database connection with optimized settings"""
    # Use timeout and check_same_thread=False for better concurrency
    conn = sqlite3.connect(
        settings.DATABASE_PATH,
        timeout=10.0,  # Wait up to 10 seconds if database is locked
        check_same_thread=False  # Allow connection to be used across threads
    )
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    
    # Enable optimizations
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA busy_timeout=5000")  # Wait 5 seconds if locked
    
    return conn

@contextmanager
def get_db():
    """Context manager for database connection with auto-commit/rollback"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
