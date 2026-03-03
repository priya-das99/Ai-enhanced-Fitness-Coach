#!/usr/bin/env python
"""
Migrate passwords from SHA256 to bcrypt
Run this once to update existing user passwords
"""

import sys
import os
import sqlite3
from passlib.context import CryptContext

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def migrate_passwords():
    """Migrate all SHA256 passwords to bcrypt"""
    
    print("=" * 60)
    print("🔐 Password Migration: SHA256 → bcrypt")
    print("=" * 60)
    print()
    
    db_path = os.path.join(current_dir, 'mood.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, password_hash FROM users")
    users = cursor.fetchall()
    
    print(f"Found {len(users)} users")
    print()
    
    # Known passwords for demo users (you can add more)
    known_passwords = {
        'demo': 'demo123',
        'priya123': 'priya123',  # Assuming username = password
        'Ankur123': 'Ankur123',  # Assuming username = password
    }
    
    migrated = 0
    skipped = 0
    
    for user in users:
        user_id = user['id']
        username = user['username']
        old_hash = user['password_hash']
        
        # Check if already bcrypt (starts with $2b$)
        if old_hash.startswith('$2b$') or old_hash.startswith('$2a$'):
            print(f"⏭️  {username}: Already using bcrypt, skipping")
            skipped += 1
            continue
        
        # Check if we know the password
        if username in known_passwords:
            password = known_passwords[username]
            new_hash = pwd_context.hash(password)
            
            # Update in database
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
            
            print(f"✅ {username}: Migrated to bcrypt")
            migrated += 1
        else:
            print(f"⚠️  {username}: Password unknown, cannot migrate")
            print(f"   Add to known_passwords dict or reset manually")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Migrated: {migrated}")
    print(f"   Skipped: {skipped}")
    print("=" * 60)
    print()
    
    if migrated > 0:
        print("You can now login with:")
        for username, password in known_passwords.items():
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print()

if __name__ == "__main__":
    try:
        migrate_passwords()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
