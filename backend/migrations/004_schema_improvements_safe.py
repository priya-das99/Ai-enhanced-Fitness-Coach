"""
Migration 004: Schema Improvements (Safe Version for Fresh DB)

This version assumes a fresh database and just adds new columns and tables.
"""

import sqlite3


def upgrade(conn):
    """Schema Improvements (Safe Version for Fresh DB)"""
    cursor = conn.cursor()
    
    print("🔧 Starting Schema Improvements Migration (Safe Version)...")
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    print("✅ Foreign keys enabled")
    
    try:
        # ============================================================
        # 1. Add new columns to suggestion_history
        # ============================================================
        print("\n📊 Step 1: Enhancing suggestion_history...")
        
        cursor.execute("ALTER TABLE suggestion_history ADD COLUMN interaction_type TEXT DEFAULT 'shown'")
        cursor.execute("ALTER TABLE suggestion_history ADD COLUMN rejected_at DATETIME")
        cursor.execute("ALTER TABLE suggestion_history ADD COLUMN ignored BOOLEAN DEFAULT 0")
        cursor.execute("ALTER TABLE suggestion_history ADD COLUMN expired BOOLEAN DEFAULT 0")
        print("✅ Added interaction tracking columns to suggestion_history")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  Columns already exist in suggestion_history")
        else:
            raise
    
    try:
        # ============================================================
        # 2. Add new columns to user_behavior_metrics
        # ============================================================
        print("\n📊 Step 2: Enhancing user_behavior_metrics...")
        
        cursor.execute("ALTER TABLE user_behavior_metrics ADD COLUMN suggestion_rejection_rate REAL DEFAULT 0")
        cursor.execute("ALTER TABLE user_behavior_metrics ADD COLUMN total_suggestions_rejected INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE user_behavior_metrics ADD COLUMN total_suggestions_ignored INTEGER DEFAULT 0")
        print("✅ Added rejection/ignore tracking to user_behavior_metrics")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  Columns already exist in user_behavior_metrics")
        else:
            raise
    
    try:
        # ============================================================
        # 3. Add new columns to mood_logs
        # ============================================================
        print("\n📊 Step 3: Enhancing mood_logs...")
        
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN mood_intensity INTEGER")
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN stress_level INTEGER")
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN energy_level INTEGER")
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN confidence_level INTEGER")
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN tags TEXT")
        print("✅ Added intensity and depth tracking to mood_logs")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  Columns already exist in mood_logs")
        else:
            raise
    
    try:
        # ============================================================
        # 4. Add new columns to user_activity_history
        # ============================================================
        print("\n📊 Step 4: Enhancing user_activity_history...")
        
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN completion_percentage INTEGER DEFAULT 100")
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN user_rating INTEGER")
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN energy_before INTEGER")
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN energy_after INTEGER")
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN satisfaction_score INTEGER")
        cursor.execute("ALTER TABLE user_activity_history ADD COLUMN would_repeat BOOLEAN")
        print("✅ Added quality metrics to user_activity_history")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  Columns already exist in user_activity_history")
        else:
            raise
    
    try:
        # ============================================================
        # 5. Add session_id to chat_messages
        # ============================================================
        print("\n📊 Step 5: Linking chat_messages to sessions...")
        
        cursor.execute("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER")
        print("✅ Added session_id to chat_messages")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  session_id already exists in chat_messages")
        else:
            raise
    
    # ============================================================
    # 6. Create ranking context tables
    # ============================================================
    print("\n📊 Step 6: Creating ranking context tables...")
    
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
            context_snapshot TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
            signals_used TEXT,
            FOREIGN KEY (ranking_context_id) REFERENCES suggestion_ranking_context(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_context_user ON suggestion_ranking_context(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_details_context ON suggestion_ranking_details(ranking_context_id)")
    print("✅ Ranking context tables created")
    
    # ============================================================
    # 7. Create indexes for performance
    # ============================================================
    print("\n📊 Step 7: Creating performance indexes...")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_suggestion_history_user ON suggestion_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_suggestion_history_key ON suggestion_history(suggestion_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mood_logs_user ON mood_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mood_logs_timestamp ON mood_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_activities_user ON health_activities(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_activities_type ON health_activities(activity_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_history_user ON user_activity_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_challenges_user ON user_challenges(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_challenges_challenge ON user_challenges(challenge_id)")
    print("✅ Performance indexes created")
    
    # Don't close connection - let migration runner handle it
    print("\n✅ Migration 004 completed successfully!")
    print("\n📊 Summary of changes:")
    print("  • Added suggestion interaction tracking (rejected, ignored, expired)")
    print("  • Enhanced mood_logs with intensity, stress, energy, confidence")
    print("  • Enhanced user_activity_history with quality metrics")
    print("  • Linked chat_messages to chat_sessions")
    print("  • Created ranking context snapshot tables")
    print("  • Added performance indexes")
    print("  • Enabled foreign key constraints")


if __name__ == "__main__":
    migrate()
