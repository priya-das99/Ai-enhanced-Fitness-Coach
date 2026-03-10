#!/usr/bin/env python3
"""
Debug Database Paths
Check which databases are being used by different components
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def check_database_paths():
    """Check database paths used by different components"""
    print("🔍 Checking database paths...")
    
    # Check old db.py path
    try:
        from db import DATABASE
        print(f"📁 db.py database: {DATABASE}")
        print(f"   Exists: {os.path.exists(DATABASE)}")
        
        if os.path.exists(DATABASE):
            import sqlite3
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Tables: {len(tables)} - {tables[:5]}...")
            conn.close()
    except Exception as e:
        print(f"❌ db.py error: {e}")
    
    # Check FastAPI app database path
    try:
        from app.config import settings
        print(f"📁 FastAPI database: {settings.DATABASE_PATH}")
        print(f"   Exists: {os.path.exists(settings.DATABASE_PATH)}")
        
        if os.path.exists(settings.DATABASE_PATH):
            import sqlite3
            conn = sqlite3.connect(settings.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Tables: {len(tables)} - {tables[:5]}...")
            conn.close()
    except Exception as e:
        print(f"❌ FastAPI database error: {e}")
    
    # Check if they're the same file
    try:
        from db import DATABASE
        from app.config import settings
        
        abs_db_py = os.path.abspath(DATABASE)
        abs_fastapi = os.path.abspath(settings.DATABASE_PATH)
        
        print(f"\n🔍 Path comparison:")
        print(f"   db.py absolute: {abs_db_py}")
        print(f"   FastAPI absolute: {abs_fastapi}")
        print(f"   Same file: {abs_db_py == abs_fastapi}")
        
    except Exception as e:
        print(f"❌ Path comparison error: {e}")

if __name__ == '__main__':
    print("🔍 Database Path Analysis")
    print("=" * 50)
    
    check_database_paths()