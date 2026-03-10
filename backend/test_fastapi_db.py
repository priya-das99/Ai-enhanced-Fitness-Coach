#!/usr/bin/env python3
"""
Test FastAPI Database Connection
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_fastapi_db_connection():
    """Test FastAPI database connection"""
    print("🧪 Testing FastAPI database connection...")
    
    try:
        from app.core.database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if chat_sessions exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
            exists = cursor.fetchone() is not None
            print(f"chat_sessions exists: {exists}")
            
            if exists:
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                count = cursor.fetchone()[0]
                print(f"chat_sessions rows: {count}")
                
                # Try to insert a test session
                cursor.execute("INSERT INTO chat_sessions (user_id, session_start) VALUES (?, CURRENT_TIMESTAMP)", (999,))
                print("✅ Test insert successful")
                
                # Check count again
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                new_count = cursor.fetchone()[0]
                print(f"chat_sessions rows after insert: {new_count}")
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"All tables ({len(tables)}): {tables}")
        
        print("✅ FastAPI database connection works")
        
    except Exception as e:
        print(f"❌ FastAPI database error: {e}")
        import traceback
        traceback.print_exc()

def test_chat_repository_direct():
    """Test chat repository directly with detailed error info"""
    print("\n🧪 Testing chat repository with detailed error info...")
    
    try:
        from app.repositories.chat_repository import ChatRepository
        
        chat_repo = ChatRepository()
        
        print("Creating session...")
        session_id = chat_repo.create_session(999)
        print(f"✅ Session created: {session_id}")
        
    except Exception as e:
        print(f"❌ Chat repository error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Testing FastAPI Database Connection")
    print("=" * 50)
    
    test_fastapi_db_connection()
    test_chat_repository_direct()