"""
Migration: Add challenges system
Allows admins to create challenges and track employee participation
"""

import sqlite3
import os

def run_migration():
    """Add challenges tables"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mood_capture.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Challenges table (admin creates these)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            challenge_type TEXT NOT NULL,  -- 'water', 'sleep', 'exercise', 'mood', 'steps'
            target_value REAL NOT NULL,  -- e.g., 8 glasses, 7 hours, 30 minutes
            target_unit TEXT,  -- 'glasses', 'hours', 'minutes'
            duration_days INTEGER NOT NULL,  -- How many days to complete
            points INTEGER DEFAULT 100,  -- Points awarded on completion
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            created_by INTEGER,  -- Admin user ID
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # User challenge participation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',  -- 'active', 'completed', 'failed', 'abandoned'
            progress REAL DEFAULT 0,  -- Percentage (0-100)
            days_completed INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            completed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (challenge_id) REFERENCES challenges(id),
            UNIQUE(user_id, challenge_id)
        )
    ''')
    
    # Daily challenge progress tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_challenge_id INTEGER NOT NULL,
            date DATE NOT NULL,
            value_achieved REAL,  -- e.g., 6 glasses, 5 hours
            target_met BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_challenge_id) REFERENCES user_challenges(id),
            UNIQUE(user_challenge_id, date)
        )
    ''')
    
    # User points/rewards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_points INTEGER DEFAULT 0,
            challenges_completed INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,  -- Days in a row
            longest_streak INTEGER DEFAULT 0,
            last_activity_date DATE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id)
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_challenges_active ON challenges(is_active, start_date, end_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_challenges_status ON user_challenges(user_id, status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_challenge_progress_date ON challenge_progress(user_challenge_id, date)')
    
    conn.commit()
    conn.close()
    print("✓ Migration 003: Challenges system tables created")

if __name__ == '__main__':
    run_migration()
