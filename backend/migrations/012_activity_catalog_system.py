"""
Migration 012: Activity Catalog System

Creates:
1. activity_catalog table - stores all available activities
2. Adds columns to activity_completions for structured logging
3. Seeds initial activity data
"""

import sqlite3
from datetime import datetime


def upgrade(conn: sqlite3.Connection):
    """Apply migration"""
    cursor = conn.cursor()
    
    print("Creating activity_catalog table...")
    
    # Create activity_catalog table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_catalog (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            icon TEXT,
            default_duration INTEGER DEFAULT 30,
            requires_duration BOOLEAN DEFAULT 1,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("Adding columns to user_activity_history...")
    
    # Add new columns to user_activity_history (if they don't exist)
    try:
        cursor.execute('ALTER TABLE user_activity_history ADD COLUMN activity_type TEXT')
        print("  ✅ Added activity_type column")
    except sqlite3.OperationalError:
        print("  activity_type column already exists")
    
    try:
        cursor.execute('ALTER TABLE user_activity_history ADD COLUMN start_time DATETIME')
        print("  ✅ Added start_time column")
    except sqlite3.OperationalError:
        print("  start_time column already exists")
    
    try:
        cursor.execute('ALTER TABLE user_activity_history ADD COLUMN end_time DATETIME')
        print("  ✅ Added end_time column")
    except sqlite3.OperationalError:
        print("  end_time column already exists")
    
    try:
        cursor.execute('ALTER TABLE user_activity_history ADD COLUMN notes TEXT')
        print("  ✅ Added notes column")
    except sqlite3.OperationalError:
        print("  notes column already exists")
    
    print("Seeding activity catalog...")
    
    # Seed activity catalog
    activities = [
        # Well-being activities
        ('book_reading', 'Book Reading', 'wellbeing', '📚', 30, 1, 'Reading books for relaxation and learning'),
        ('meditation', 'Meditation', 'wellbeing', '🧘', 15, 1, 'Mindfulness and meditation practice'),
        ('journaling', 'Journaling', 'wellbeing', '📝', 20, 1, 'Writing thoughts and reflections'),
        ('breathing', 'Breathing Exercise', 'wellbeing', '🌬️', 5, 1, 'Deep breathing exercises'),
        
        # Popular activities
        ('hiking', 'Hiking', 'popular', '🥾', 60, 1, 'Outdoor hiking and nature walks'),
        ('swimming', 'Swimming', 'popular', '🏊', 45, 1, 'Swimming for fitness and fun'),
        ('badminton', 'Badminton', 'popular', '🏸', 60, 1, 'Playing badminton'),
        ('football', 'Football', 'popular', '⚽', 90, 1, 'Playing football/soccer'),
        ('calisthenics', 'Calisthenics', 'popular', '💪', 30, 1, 'Bodyweight exercises'),
        
        # Exercise activities
        ('running', 'Running', 'exercise', '🏃', 30, 1, 'Running or jogging'),
        ('gym', 'Gym Workout', 'exercise', '🏋️', 60, 1, 'Gym training session'),
        ('yoga', 'Yoga', 'exercise', '🧘', 45, 1, 'Yoga practice'),
        ('cycling', 'Cycling', 'exercise', '🚴', 45, 1, 'Cycling or biking'),
        ('walking', 'Walking', 'exercise', '🚶', 30, 1, 'Walking for exercise'),
    ]
    
    for activity in activities:
        cursor.execute('''
            INSERT OR IGNORE INTO activity_catalog 
            (id, name, category, icon, default_duration, requires_duration, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', activity)
    
    conn.commit()
    print(f"✅ Migration 012 complete! Added {len(activities)} activities to catalog.")


def downgrade(conn: sqlite3.Connection):
    """Revert migration"""
    cursor = conn.cursor()
    
    print("Dropping activity_catalog table...")
    cursor.execute('DROP TABLE IF EXISTS activity_catalog')
    
    # Note: We don't drop columns from user_activity_history as SQLite doesn't support it easily
    print("⚠️  Note: Columns added to user_activity_history remain (SQLite limitation)")
    
    conn.commit()
    print("✅ Migration 012 reverted.")


if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.core.database import get_db_connection
    
    conn = get_db_connection()
    
    try:
        upgrade(conn)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()
