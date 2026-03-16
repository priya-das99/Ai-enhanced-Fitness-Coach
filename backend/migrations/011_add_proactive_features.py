# migrations/011_add_proactive_features.py
# Add tables for proactive features: streak celebrations and activity feedback

import sqlite3
import logging

logger = logging.getLogger(__name__)

def upgrade(db_path: str):
    """Add tables for proactive features"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Table 1: Streak Celebrations
        # Tracks when we've celebrated streak milestones to avoid duplicate celebrations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak_celebrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                streak_type TEXT NOT NULL,
                milestone INTEGER NOT NULL,
                celebrated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_streak_celebrations_user 
            ON streak_celebrations(user_id, streak_type)
        ''')
        
        # Table 2: Activity Feedback
        # Stores user feedback on activity effectiveness
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_id TEXT NOT NULL,
                mood_before TEXT,
                mood_after TEXT,
                helpful BOOLEAN NOT NULL,
                completion_id INTEGER,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (completion_id) REFERENCES activity_completions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_feedback_user_activity 
            ON activity_feedback(user_id, activity_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_feedback_completion 
            ON activity_feedback(completion_id)
        ''')
        
        conn.commit()
        logger.info("✅ Migration 011: Added proactive features tables")
        
    except Exception as e:
        logger.error(f"❌ Migration 011 failed: {e}")
        raise
    finally:
        conn.close()

def downgrade(db_path: str):
    """Remove proactive features tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS activity_feedback')
        cursor.execute('DROP TABLE IF EXISTS streak_celebrations')
        
        conn.commit()
        logger.info("✅ Migration 011: Removed proactive features tables")
        
    except Exception as e:
        logger.error(f"❌ Migration 011 downgrade failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    import sys
    import os
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.config import Settings
    
    settings = Settings()
    
    print("Running migration 011: Add proactive features...")
    upgrade(settings.DATABASE_PATH)
    print("Migration complete!")
