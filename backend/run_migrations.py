#!/usr/bin/env python3
"""
Migration runner for production deployment
Runs all migration files in order during startup
"""

import os
import sys
import sqlite3
import importlib.util
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings

logger = logging.getLogger(__name__)

def get_migration_files():
    """Get all migration files in order"""
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return []
    
    migration_files = []
    for file_path in migrations_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue
        migration_files.append(file_path)
    
    # Sort by filename to ensure proper order
    migration_files.sort(key=lambda x: x.name)
    return migration_files

def create_migration_table(cursor):
    """Create table to track applied migrations"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

def is_migration_applied(cursor, migration_name):
    """Check if migration has been applied"""
    cursor.execute(
        "SELECT COUNT(*) FROM applied_migrations WHERE migration_name = ?",
        (migration_name,)
    )
    return cursor.fetchone()[0] > 0

def mark_migration_applied(cursor, migration_name):
    """Mark migration as applied"""
    cursor.execute(
        "INSERT INTO applied_migrations (migration_name) VALUES (?)",
        (migration_name,)
    )

def run_migration_file(file_path, cursor):
    """Run a single migration file"""
    try:
        # Load the migration module
        spec = importlib.util.spec_from_file_location("migration", file_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Run the migration - check for different function names
        if hasattr(migration_module, 'run_migration'):
            logger.info(f"Running migration: {file_path.name}")
            migration_module.run_migration(cursor)
            return True
        elif hasattr(migration_module, 'upgrade'):
            logger.info(f"Running migration: {file_path.name}")
            # Create a connection object from cursor for upgrade function
            conn = cursor.connection
            migration_module.upgrade(conn)
            return True
        else:
            logger.warning(f"Migration {file_path.name} has no run_migration or upgrade function")
            return False
            
    except Exception as e:
        logger.error(f"Failed to run migration {file_path.name}: {e}")
        raise

def run_all_migrations():
    """Run all pending migrations"""
    try:
        # Ensure database directory exists
        db_path = settings.DATABASE_PATH
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create migration tracking table
        create_migration_table(cursor)
        
        # Get all migration files
        migration_files = get_migration_files()
        
        if not migration_files:
            logger.info("No migration files found")
            return
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run each migration
        applied_count = 0
        for migration_file in migration_files:
            migration_name = migration_file.name
            
            if is_migration_applied(cursor, migration_name):
                logger.info(f"Migration {migration_name} already applied, skipping")
                continue
            
            try:
                if run_migration_file(migration_file, cursor):
                    mark_migration_applied(cursor, migration_name)
                    applied_count += 1
                    logger.info(f"✅ Applied migration: {migration_name}")
                else:
                    logger.warning(f"⚠️ Skipped migration: {migration_name}")
                
                # Commit after each migration
                conn.commit()
                
            except Exception as e:
                logger.error(f"❌ Failed to apply migration {migration_name}: {e}")
                conn.rollback()
                raise
        
        conn.close()
        
        if applied_count > 0:
            logger.info(f"✅ Successfully applied {applied_count} migrations")
        else:
            logger.info("✅ All migrations already applied")
            
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_migrations()