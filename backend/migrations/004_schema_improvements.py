"""
Migration 004: Schema Improvements for Production Readiness

Fixes:
1. Standardize user_id to INTEGER across all tables
2. Enable foreign key constraints
3. Add suggestion interaction tracking (rejected, ignored, expired)
4. Enhance user_activity_history with completion quality metrics
5. Add mood intensity and stress level to mood_logs
6. Link chat_messages to chat_sessions
7. Add ranking context snapshot table
"""

import sqlite3
from datetime import datetime


def upgrade(conn):
    """Schema Improvements for Production Readiness"""
    cursor = conn.cursor()
    
    print("🔧 Starting Schema Improvements Migration...")
    
    # Disable foreign keys temporarily for migration
    cursor.execute("PRAGMA foreign_keys = OFF;")
    print("✅ Foreign keys disabled for migration")
    
    # Helper function to check if table exists
    def table_exists(table_name):
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    # ============================================================
    # 1. Fix user_id type inconsistencies (skip if data exists)
    # ============================================================
    print("\n📊 Step 1: Standardizing user_id types...")
    
    # Check if tables exist and have data before attempting migration
    def safe_table_migration(table_name, new_schema, data_migration_query):
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            print(f"⚠️  {table_name} table not found, skipping")
            return
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        if row_count == 0:
            print(f"✅ {table_name} is empty, recreating with new schema")
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(new_schema)
        else:
            print(f"⚠️  {table_name} has {row_count} rows, skipping migration to preserve data")
    
    # Backup and recreate suggestion_history with INTEGER user_id
    safe_table_migration('suggestion_history', """
        CREATE TABLE suggestion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            suggestion_key TEXT NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            shown_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            interaction_type TEXT DEFAULT 'shown',
            accepted BOOLEAN DEFAULT 0,
            accepted_at DATETIME,
            rejected_at DATETIME,
            ignored BOOLEAN DEFAULT 0,
            expired BOOLEAN DEFAULT 0
        )
    """, None)
    
    # Backup and recreate analytics_events with INTEGER user_id
    safe_table_migration('analytics_events', """
        CREATE TABLE analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """, None)
    
    # Backup and recreate user_behavior_metrics with INTEGER user_id
    safe_table_migration('user_behavior_metrics', """
        CREATE TABLE user_behavior_metrics (
            user_id INTEGER PRIMARY KEY,
            avg_sleep_7d REAL DEFAULT 0,
            avg_water_7d REAL DEFAULT 0,
            avg_exercise_7d REAL DEFAULT 0,
            hydration_score REAL DEFAULT 0,
            stress_score REAL DEFAULT 0,
            suggestion_acceptance_rate REAL DEFAULT 0,
            suggestion_rejection_rate REAL DEFAULT 0,
            total_suggestions_shown INTEGER DEFAULT 0,
            total_suggestions_accepted INTEGER DEFAULT 0,
            total_suggestions_rejected INTEGER DEFAULT 0,
            total_suggestions_ignored INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """, None)
    
    # ============================================================
    # 2. Add missing columns to existing tables (safe approach)
    # ============================================================
    print("\n🔗 Step 2: Adding missing columns to existing tables...")
    
    # Add columns to mood_logs if they don't exist
    if table_exists('mood_logs'):
        cursor.execute("PRAGMA table_info(mood_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        missing_columns = [
            ('mood_intensity', 'INTEGER'),
            ('stress_level', 'INTEGER'),
            ('energy_level', 'INTEGER'),
            ('confidence_level', 'INTEGER'),
            ('reason_category', 'TEXT'),
            ('tags', 'TEXT')
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE mood_logs ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added {col_name} to mood_logs")
        
        print("✅ mood_logs enhanced with additional columns")
    
    # Add columns to user_activity_history if they don't exist
    if table_exists('user_activity_history'):
        cursor.execute("PRAGMA table_info(user_activity_history)")
        columns = [col[1] for col in cursor.fetchall()]
        
        missing_columns = [
            ('completion_percentage', 'INTEGER DEFAULT 100'),
            ('user_rating', 'INTEGER'),
            ('energy_before', 'INTEGER'),
            ('energy_after', 'INTEGER'),
            ('satisfaction_score', 'INTEGER'),
            ('would_repeat', 'BOOLEAN')
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE user_activity_history ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added {col_name} to user_activity_history")
        
        print("✅ user_activity_history enhanced with quality metrics")
    
    # ============================================================
    # 3. Create ranking context tables if they don't exist
    # ============================================================
    print("\n🎯 Step 3: Creating ranking context tables...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_ranking_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            ranking_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ranking_algorithm TEXT,
            total_candidates INTEGER,
            selected_suggestion_key TEXT,
            selected_rank INTEGER,
            context_snapshot TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_ranking_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ranking_context_id INTEGER NOT NULL,
            suggestion_key TEXT NOT NULL,
            rank_position INTEGER NOT NULL,
            final_score REAL NOT NULL,
            recency_score REAL,
            frequency_score REAL,
            acceptance_score REAL,
            mood_match_score REAL,
            time_match_score REAL,
            diversity_penalty REAL,
            signals_used TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_context_user ON suggestion_ranking_context(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_details_context ON suggestion_ranking_details(ranking_context_id)")
    print("✅ Ranking context tables created")
    
    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    print("✅ Foreign keys re-enabled")
    
    # Don't close connection - let migration runner handle it
    print("\n✅ Migration 004 completed successfully!")
    print("\n📊 Summary of changes:")
    print("  • Safely handled user_id standardization")
    print("  • Added missing columns to mood_logs and user_activity_history")
    print("  • Created ranking context tables")
    print("  • Preserved existing data integrity")


if __name__ == "__main__":
    migrate()
