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


def migrate(db_path: str = "mood.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Starting Schema Improvements Migration...")
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    print("✅ Foreign keys enabled")
    
    # Helper function to check if table exists
    def table_exists(table_name):
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    # ============================================================
    # 1. Fix user_id type inconsistencies
    # ============================================================
    print("\n📊 Step 1: Standardizing user_id types...")
    
    # Backup and recreate suggestion_history with INTEGER user_id
    if table_exists('suggestion_history'):
        cursor.execute("""
            CREATE TABLE suggestion_history_new (
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
                expired BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Migrate data (convert TEXT user_id to INTEGER)
        cursor.execute("""
            INSERT INTO suggestion_history_new 
            (id, user_id, suggestion_key, mood_emoji, reason, shown_at, accepted, accepted_at)
            SELECT 
                id, 
                CAST(user_id AS INTEGER), 
                suggestion_key, 
                mood_emoji, 
                reason, 
                shown_at, 
                accepted, 
                accepted_at
            FROM suggestion_history
            WHERE user_id GLOB '[0-9]*'
        """)
        
        cursor.execute("DROP TABLE suggestion_history")
        cursor.execute("ALTER TABLE suggestion_history_new RENAME TO suggestion_history")
        cursor.execute("CREATE INDEX idx_suggestion_history_user ON suggestion_history(user_id)")
        cursor.execute("CREATE INDEX idx_suggestion_history_key ON suggestion_history(suggestion_key)")
        print("✅ suggestion_history migrated with INTEGER user_id")
    else:
        print("⚠️  suggestion_history table not found, skipping")
    
    # Backup and recreate analytics_events with INTEGER user_id
    if table_exists('analytics_events'):
        cursor.execute("""
            CREATE TABLE analytics_events_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            INSERT INTO analytics_events_new 
            (id, user_id, event_type, event_data, created_at)
            SELECT 
                id, 
                CAST(user_id AS INTEGER), 
                event_type, 
                event_data, 
                created_at
            FROM analytics_events
            WHERE user_id GLOB '[0-9]*'
        """)
        
        cursor.execute("DROP TABLE analytics_events")
        cursor.execute("ALTER TABLE analytics_events_new RENAME TO analytics_events")
        cursor.execute("CREATE INDEX idx_analytics_user ON analytics_events(user_id)")
        cursor.execute("CREATE INDEX idx_analytics_type ON analytics_events(event_type)")
        print("✅ analytics_events migrated with INTEGER user_id")
    else:
        print("⚠️  analytics_events table not found, skipping")
    
    # Backup and recreate user_behavior_metrics with INTEGER user_id
    if table_exists('user_behavior_metrics'):
        cursor.execute("""
            CREATE TABLE user_behavior_metrics_new (
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
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            INSERT INTO user_behavior_metrics_new 
            (user_id, avg_sleep_7d, avg_water_7d, avg_exercise_7d, hydration_score, 
             stress_score, suggestion_acceptance_rate, total_suggestions_shown, 
             total_suggestions_accepted, last_updated)
            SELECT 
                CAST(user_id AS INTEGER), 
                avg_sleep_7d, 
                avg_water_7d, 
                avg_exercise_7d, 
                hydration_score,
                stress_score, 
                suggestion_acceptance_rate, 
                total_suggestions_shown, 
                total_suggestions_accepted, 
                last_updated
            FROM user_behavior_metrics
            WHERE user_id GLOB '[0-9]*'
        """)
        
        cursor.execute("DROP TABLE user_behavior_metrics")
        cursor.execute("ALTER TABLE user_behavior_metrics_new RENAME TO user_behavior_metrics")
        print("✅ user_behavior_metrics migrated with INTEGER user_id")
    else:
        print("⚠️  user_behavior_metrics table not found, skipping")
    
    # ============================================================
    # 2. Add foreign keys to existing tables
    # ============================================================
    print("\n🔗 Step 2: Adding foreign key constraints...")
    
    # Recreate mood_logs with foreign keys
    cursor.execute("""
        CREATE TABLE mood_logs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            mood_emoji TEXT,
            mood_intensity INTEGER,
            stress_level INTEGER,
            energy_level INTEGER,
            confidence_level INTEGER,
            reason TEXT,
            reason_category TEXT,
            tags TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        INSERT INTO mood_logs_new 
        (id, user_id, mood, mood_emoji, reason, reason_category, timestamp)
        SELECT id, user_id, mood, mood_emoji, reason, reason_category, timestamp
        FROM mood_logs
    """)
    
    cursor.execute("DROP TABLE mood_logs")
    cursor.execute("ALTER TABLE mood_logs_new RENAME TO mood_logs")
    cursor.execute("CREATE INDEX idx_mood_logs_user ON mood_logs(user_id)")
    cursor.execute("CREATE INDEX idx_mood_logs_timestamp ON mood_logs(timestamp)")
    print("✅ mood_logs enhanced with intensity tracking and foreign keys")
    
    # Recreate health_activities with foreign keys
    cursor.execute("""
        CREATE TABLE health_activities_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            value REAL,
            unit TEXT,
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        INSERT INTO health_activities_new 
        SELECT * FROM health_activities
    """)
    
    cursor.execute("DROP TABLE health_activities")
    cursor.execute("ALTER TABLE health_activities_new RENAME TO health_activities")
    cursor.execute("CREATE INDEX idx_health_activities_user ON health_activities(user_id)")
    cursor.execute("CREATE INDEX idx_health_activities_type ON health_activities(activity_type)")
    print("✅ health_activities with foreign keys")
    
    # ============================================================
    # 3. Link chat_messages to chat_sessions
    # ============================================================
    print("\n💬 Step 3: Linking chat_messages to sessions...")
    
    cursor.execute("""
        CREATE TABLE chat_messages_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            message TEXT NOT NULL,
            sender TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL
        )
    """)
    
    cursor.execute("""
        INSERT INTO chat_messages_new 
        (id, user_id, message, sender, timestamp, metadata)
        SELECT id, user_id, message, sender, timestamp, metadata
        FROM chat_messages
    """)
    
    cursor.execute("DROP TABLE chat_messages")
    cursor.execute("ALTER TABLE chat_messages_new RENAME TO chat_messages")
    cursor.execute("CREATE INDEX idx_chat_messages_user ON chat_messages(user_id)")
    cursor.execute("CREATE INDEX idx_chat_messages_session ON chat_messages(session_id)")
    print("✅ chat_messages linked to sessions")
    
    # ============================================================
    # 4. Enhance user_activity_history
    # ============================================================
    print("\n📈 Step 4: Enhancing activity history...")
    
    cursor.execute("""
        CREATE TABLE user_activity_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            mood_emoji TEXT,
            reason TEXT,
            completed BOOLEAN DEFAULT 1,
            completion_percentage INTEGER DEFAULT 100,
            duration_minutes INTEGER,
            user_rating INTEGER,
            energy_before INTEGER,
            energy_after INTEGER,
            satisfaction_score INTEGER,
            would_repeat BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            day_of_week TEXT,
            time_of_day TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        INSERT INTO user_activity_history_new 
        (id, user_id, activity_id, activity_name, mood_emoji, reason, 
         completed, duration_minutes, timestamp, day_of_week, time_of_day)
        SELECT id, user_id, activity_id, activity_name, mood_emoji, reason,
               completed, duration_minutes, timestamp, day_of_week, time_of_day
        FROM user_activity_history
    """)
    
    cursor.execute("DROP TABLE user_activity_history")
    cursor.execute("ALTER TABLE user_activity_history_new RENAME TO user_activity_history")
    cursor.execute("CREATE INDEX idx_activity_history_user ON user_activity_history(user_id)")
    print("✅ user_activity_history enhanced with quality metrics")
    
    # ============================================================
    # 5. Create ranking context snapshot table
    # ============================================================
    print("\n🎯 Step 5: Creating ranking context table...")
    
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
    
    cursor.execute("CREATE INDEX idx_ranking_context_user ON suggestion_ranking_context(user_id)")
    cursor.execute("CREATE INDEX idx_ranking_details_context ON suggestion_ranking_details(ranking_context_id)")
    print("✅ Ranking context tables created")
    
    # ============================================================
    # 6. Add foreign keys to remaining tables
    # ============================================================
    print("\n🔗 Step 6: Adding foreign keys to remaining tables...")
    
    # user_challenges
    cursor.execute("""
        CREATE TABLE user_challenges_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            progress REAL DEFAULT 0,
            days_completed INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            completed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("INSERT INTO user_challenges_new SELECT * FROM user_challenges")
    cursor.execute("DROP TABLE user_challenges")
    cursor.execute("ALTER TABLE user_challenges_new RENAME TO user_challenges")
    cursor.execute("CREATE INDEX idx_user_challenges_user ON user_challenges(user_id)")
    cursor.execute("CREATE INDEX idx_user_challenges_challenge ON user_challenges(challenge_id)")
    print("✅ user_challenges with foreign keys")
    
    # user_points
    cursor.execute("""
        CREATE TABLE user_points_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_points INTEGER DEFAULT 0,
            challenges_completed INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_activity_date DATE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("INSERT INTO user_points_new SELECT * FROM user_points")
    cursor.execute("DROP TABLE user_points")
    cursor.execute("ALTER TABLE user_points_new RENAME TO user_points")
    cursor.execute("CREATE INDEX idx_user_points_user ON user_points(user_id)")
    print("✅ user_points with foreign keys")
    
    # chat_sessions
    cursor.execute("""
        CREATE TABLE chat_sessions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_end DATETIME,
            messages_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("INSERT INTO chat_sessions_new SELECT * FROM chat_sessions")
    cursor.execute("DROP TABLE chat_sessions")
    cursor.execute("ALTER TABLE chat_sessions_new RENAME TO chat_sessions")
    cursor.execute("CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id)")
    print("✅ chat_sessions with foreign keys")
    
    conn.commit()
    print("\n✅ Migration 004 completed successfully!")
    print("\n📊 Summary of changes:")
    print("  • Standardized user_id to INTEGER across all tables")
    print("  • Enabled foreign key constraints")
    print("  • Added suggestion interaction tracking (rejected, ignored, expired)")
    print("  • Enhanced mood_logs with intensity, stress, energy, confidence")
    print("  • Enhanced user_activity_history with quality metrics")
    print("  • Linked chat_messages to chat_sessions")
    print("  • Created ranking context snapshot tables")
    print("  • Added CASCADE delete rules for data integrity")
    
    conn.close()


if __name__ == "__main__":
    migrate()
