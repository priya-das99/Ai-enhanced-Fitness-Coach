#!/usr/bin/env python3
"""
Run database migrations for MoodCapture
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings

def run_sqlite_migrations():
    """Run SQLite migrations"""
    db_path = settings.DATABASE_PATH
    print(f"Running migrations on SQLite database: {db_path}")

    # Import and run migration scripts
    migrations_dir = backend_dir / "migrations"
    if migrations_dir.exists():
        for migration_file in sorted(migrations_dir.glob("*.py")):
            if migration_file.name.startswith("00"):
                print(f"Running migration: {migration_file.name}")
                # Execute the migration
                exec(open(migration_file).read())

    print("SQLite migrations completed")

def run_postgresql_migrations():
    """Run PostgreSQL migrations using alembic or raw SQL"""
    print("PostgreSQL migrations not implemented yet")
    # TODO: Implement PostgreSQL migrations
    pass

def main():
    if settings.is_postgresql:
        run_postgresql_migrations()
    else:
        run_sqlite_migrations()

if __name__ == "__main__":
    main()