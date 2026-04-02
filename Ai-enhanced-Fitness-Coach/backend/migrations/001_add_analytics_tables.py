"""
Migration 001: Add Analytics and Personalization Tables

Adds:
- analytics_events: Event-driven architecture for tracking user actions
- user_behavior_metrics: Precomputed personalization metrics
- suggestion_master: Centralized suggestion registry
- suggestion_history: Track suggestion exposure and acceptance

This migration is NON-BREAKING and additive only.
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get database path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'mood.db')

def run_migration(cursor):
    """Run migration"""
    conn = cursor.connection
    
    print("Starting migration 001: Add analytics tables...")
    
    # 1. analytics_events - Event-driven architecture
    print("Creating analytics_events table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_events ON analytics_events(user_id, event_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON analytics_events(created_at)
    """)
    
    # 2. user_behavior_metrics - Precomputed personalization
    print("Creating user_behavior_metrics table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_behavior_metrics (
            user_id TEXT PRIMARY KEY,
            avg_sleep_7d REAL DEFAULT 0,
            avg_water_7d REAL DEFAULT 0,
            avg_exercise_7d REAL DEFAULT 0,
            hydration_score REAL DEFAULT 0,
            stress_score REAL DEFAULT 0,
            suggestion_acceptance_rate REAL DEFAULT 0,
            total_suggestions_shown INTEGER DEFAULT 0,
            total_suggestions_accepted INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. suggestion_master - Centralized suggestion registry
    print("Creating suggestion_master table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_key TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            effort_level TEXT,
            duration_minutes INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 4. suggestion_history - Track exposure and acceptance
    print("Creating suggestion_history table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            suggestion_key TEXT NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            shown_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            accepted BOOLEAN DEFAULT 0,
            accepted_at DATETIME
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_suggestions ON suggestion_history(user_id, suggestion_key)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_shown_at ON suggestion_history(shown_at)
    """)
    
    # Populate suggestion_master with existing wellness activities
    print("Populating suggestion_master with wellness activities...")
    suggestions = [
        ('breathing', 'Breathing Exercise', 'Quick breathing exercises to calm your mind', 'mindfulness', 'low', 5),
        ('short_walk', 'Short Walk', 'Brief walk or movement to refresh', 'physical', 'medium', 15),
        ('meditation', 'Meditation', 'Mindfulness or meditation session', 'mindfulness', 'low', 10),
        ('stretching', 'Stretching', 'Gentle stretches to release tension', 'physical', 'low', 10),
        ('take_break', 'Take a Break', 'Step away from current activity', 'rest', 'low', 5),
        ('journaling', 'Journaling', 'Write down your thoughts and feelings', 'reflection', 'low', 15),
        ('music', 'Listen to Music', 'Listen to calming or uplifting music', 'relaxation', 'low', 15),
        ('call_friend', 'Call a Friend', 'Connect with someone you trust', 'social', 'medium', 20),
        ('hydrate', 'Drink Water', 'Have a glass of water and hydrate', 'health', 'low', 1),
        ('power_nap', 'Power Nap', 'Short 15-20 minute rest', 'rest', 'low', 20),
        ('outdoor_activity', 'Outdoor Activity', 'Go outside for fresh air and movement', 'physical', 'medium', 30),
        ('seven_minute_workout', '7 Minute Workout', 'Quick high-intensity workout routine', 'physical', 'high', 7),
        ('squats_workout', 'Squats Workout', 'Focused squats exercise routine', 'physical', 'medium', 15),
        ('meditation_module', 'Guided Meditation', 'Guided meditation session', 'mindfulness', 'low', 20),
    ]
    
    for suggestion in suggestions:
        cursor.execute("""
            INSERT OR IGNORE INTO suggestion_master 
            (suggestion_key, title, description, category, effort_level, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, suggestion)
    
    # Don't close connection - let migration runner handle it
    print("✅ Migration 001 completed successfully!")
    print("Added tables: analytics_events, user_behavior_metrics, suggestion_master, suggestion_history")

def rollback():
    """Rollback migration (optional)"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Rolling back migration 001...")
    
    cursor.execute("DROP TABLE IF EXISTS analytics_events")
    cursor.execute("DROP TABLE IF EXISTS user_behavior_metrics")
    cursor.execute("DROP TABLE IF EXISTS suggestion_master")
    cursor.execute("DROP TABLE IF EXISTS suggestion_history")
    
    conn.commit()
    conn.close()
    
    print("✅ Migration 001 rolled back")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
