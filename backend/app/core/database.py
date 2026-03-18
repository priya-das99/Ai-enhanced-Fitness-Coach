# app/core/database.py
# Database connection management

import sqlite3
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection based on environment (SQLite or PostgreSQL)"""
    db_config = settings.database_config
    
    if db_config['type'] == 'postgresql':
        # PostgreSQL connection
        try:
            conn = psycopg2.connect(
                db_config['url'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            conn.autocommit = False  # Use transactions
            logger.info("Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    else:
        # SQLite connection (default)
        conn = sqlite3.connect(
            settings.DATABASE_PATH,
            timeout=10.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        
        # Enable optimizations
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        
        logger.info("Connected to SQLite database")
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
