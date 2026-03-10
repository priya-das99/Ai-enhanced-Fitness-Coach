#!/usr/bin/env python3
"""
Debug Database Connection Issue
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_app_database():
    """Test the FastAPI app database connection"""
    print("🧪 Testing FastAPI app database...")
    
    try:
        from app.core.database import get_db
        from app.config import settings
        
        print(f"Database path: {settings.DATABASE_PATH}")
        print(f"Database exists: {os.path.exists(settings.DATABASE_PATH)}")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if chat_sessions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
            exists = cursor.fetchone() is not None
            print(f"chat_sessions table exists: {exists}")
            
            if exists:
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                count = cursor.fetchone()[0]
                print(f"chat_sessions rows: {count}")
            
        print("✅ FastAPI database connection works")
        
    except Exception as e:
        print(f"❌ FastAPI database error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_repository():
    """Test chat repository directly"""
    print("\n🧪 Testing chat repository...")
    
    try:
        from app.repositories.chat_repository import ChatRepository
        
        chat_repo = ChatRepository()
        
        # Try to create a session
        session_id = chat_repo.create_session(1)
        print(f"✅ Created session: {session_id}")
        
    except Exception as e:
        print(f"❌ Chat repository error: {e}")
        import traceback
        traceback.print_exc()

def test_old_db():
    """Test the old db.py connection"""
    print("\n🧪 Testing old db.py connection...")
    
    try:
        from db import get_connection, DATABASE
        
        print(f"Old database path: {DATABASE}")
        print(f"Old database exists: {os.path.exists(DATABASE)}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
        exists = cursor.fetchone() is not None
        print(f"chat_sessions in old db: {exists}")
        
        conn.close()
        print("✅ Old database connection works")
        
    except Exception as e:
        print(f"❌ Old database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Debugging Database Connection Issue")
    print("=" * 50)
    
    test_app_database()
    test_chat_repository()
    test_old_db()