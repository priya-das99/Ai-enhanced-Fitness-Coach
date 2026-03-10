#!/usr/bin/env python3
"""
Fix Demo User Password
Updates the demo user password to use bcrypt hashing instead of SHA256
"""

import os
import sys
import sqlite3

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.security import get_password_hash

def get_db_path():
    """Get database path"""
    return os.path.join(backend_dir, 'mood_capture.db')

def fix_demo_password():
    """Update demo user password to use bcrypt"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🔧 Fixing demo user password...")
    
    # Generate bcrypt hash for 'demo123'
    bcrypt_hash = get_password_hash('demo123')
    
    # Update demo user password
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE username = 'demo'
    """, (bcrypt_hash,))
    
    if cursor.rowcount > 0:
        print("✅ Demo user password updated to bcrypt")
        print("🔑 Login credentials:")
        print("   Username: demo")
        print("   Password: demo123")
    else:
        print("❌ Demo user not found")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    fix_demo_password()