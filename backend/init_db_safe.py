#!/usr/bin/env python3
"""
Safe Database Initialization Script
Only creates missing tables, preserves existing data
"""

import os
import sys
import sqlite3
import hashlib
from datetime import datetime

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_path():
    """Get database path"""
    return os.path.join(backend_dir, 'mood_capture.db')

def table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def create_missing_tables():
    """Create only missing tables, preserve existing data"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🔍 Checking existing database...")
    
    # Check existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"📊 Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
    
    tables_created = 0
    
    # Base tables
    if not table_exists(cursor, 'users'):
        print("Creating users table...")
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        tables_created += 1
    
    if not table_exists(cursor, 'mood_logs'):
        print("Creating mood_logs table...")
        cursor.execute('''
            CREATE TABLE mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mood TEXT NOT NULL,
                mood_emoji TEXT,
                reason TEXT,
                reason_category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        tables_created += 1
    
    if not table_exists(cursor, 'action_suggestions'):
        print("Creating action_suggestions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mood_log_id INTEGER NOT NULL,
                action_id TEXT NOT NULL,
                action_name TEXT NOT NULL,
                accepted BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mood_log_id) REFERENCES mood_logs(id)
            )
        ''')
        tables_created += 1
    
    if not table_exists(cursor, 'chat_sessions'):
        print("Creating chat_sessions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_end DATETIME,
                messages_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        tables_created += 1
    
    if not table_exists(cursor, 'user_activity_history'):
        print("Creating user_activity_history table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_id TEXT NOT NULL,
                activity_name TEXT NOT NULL,
                mood_emoji TEXT,
                reason TEXT,
                completed BOOLEAN DEFAULT 1,
                duration_minutes INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                day_of_week TEXT,
                time_of_day TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        tables_created += 1
    
    if not table_exists(cursor, 'health_activities'):
        print("Creating health_activities table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                value REAL,
                unit TEXT,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        tables_created += 1
    
    # Analytics tables
    if not table_exists(cursor, 'analytics_events'):
        print("Creating analytics_events table...")
        cursor.execute("""
            CREATE TABLE analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_events ON analytics_events(user_id, event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON analytics_events(created_at)")
        tables_created += 1
    
    if not table_exists(cursor, 'user_behavior_metrics'):
        print("Creating user_behavior_metrics table...")
        cursor.execute("""
            CREATE TABLE user_behavior_metrics (
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
        tables_created += 1
    
    if not table_exists(cursor, 'suggestion_master'):
        print("Creating suggestion_master table...")
        cursor.execute("""
            CREATE TABLE suggestion_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_key TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                effort_level TEXT,
                duration_minutes INTEGER,
                is_active BOOLEAN DEFAULT 1,
                triggers_module TEXT,
                module_type TEXT DEFAULT 'internal',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Populate suggestions only if table was just created
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
            ('outdoor_activity', 'Start Outdoor Activity', 'Get outside for fresh air and nature', 'physical', 'medium', 20),
            ('seven_minute_workout', 'Start 7-Minute Workout', 'Quick high-intensity workout routine', 'physical', 'high', 7),
            ('guided_meditation', 'Start Meditation Session', 'Guided meditation for calm and focus', 'mindfulness', 'low', 10),
        ]
        
        for suggestion in suggestions:
            cursor.execute("""
                INSERT OR IGNORE INTO suggestion_master 
                (suggestion_key, title, description, category, effort_level, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, suggestion)
        
        tables_created += 1
    
    if not table_exists(cursor, 'suggestion_history'):
        print("Creating suggestion_history table...")
        cursor.execute("""
            CREATE TABLE suggestion_history (
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_suggestions ON suggestion_history(user_id, suggestion_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shown_at ON suggestion_history(shown_at)")
        tables_created += 1
    
    # Chat tables
    if not table_exists(cursor, 'chat_messages'):
        print("Creating chat_messages table...")
        cursor.execute('''
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_user_timestamp 
            ON chat_messages(user_id, timestamp DESC)
        ''')
        tables_created += 1
    
    # Challenge tables
    challenge_tables = [
        ('challenges', '''
            CREATE TABLE challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                challenge_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                target_unit TEXT,
                duration_days INTEGER NOT NULL,
                points INTEGER DEFAULT 100,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                created_by INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        '''),
        ('user_challenges', '''
            CREATE TABLE user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_id INTEGER NOT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0,
                days_completed INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (challenge_id) REFERENCES challenges(id),
                UNIQUE(user_id, challenge_id)
            )
        '''),
        ('challenge_progress', '''
            CREATE TABLE challenge_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_challenge_id INTEGER NOT NULL,
                date DATE NOT NULL,
                value_achieved REAL,
                target_met BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_challenge_id) REFERENCES user_challenges(id),
                UNIQUE(user_challenge_id, date)
            )
        '''),
        ('user_points', '''
            CREATE TABLE user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_points INTEGER DEFAULT 0,
                challenges_completed INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id)
            )
        ''')
    ]
    
    for table_name, create_sql in challenge_tables:
        if not table_exists(cursor, table_name):
            print(f"Creating {table_name} table...")
            cursor.execute(create_sql)
            tables_created += 1
    
    # Wellness content tables
    wellness_tables = [
        ('content_categories', '''
            CREATE TABLE content_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT,
                color TEXT,
                is_active BOOLEAN DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''),
        ('content_items', '''
            CREATE TABLE content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                content_type TEXT NOT NULL,
                content_url TEXT,
                thumbnail_url TEXT,
                duration_minutes INTEGER,
                difficulty_level TEXT,
                tags TEXT,
                view_count INTEGER DEFAULT 0,
                is_featured BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES content_categories(id) ON DELETE CASCADE
            )
        '''),
        ('user_content_interactions', '''
            CREATE TABLE user_content_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                progress_percent INTEGER DEFAULT 0,
                time_spent_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
            )
        '''),
        ('user_wellness_preferences', '''
            CREATE TABLE user_wellness_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                smoking_status TEXT,
                fitness_goals TEXT,
                interests TEXT,
                preferred_content_types TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    ]
    
    for table_name, create_sql in wellness_tables:
        if not table_exists(cursor, table_name):
            print(f"Creating {table_name} table...")
            cursor.execute(create_sql)
            tables_created += 1
    
    # Create demo user only if users table was empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            ''', ('demo', 'demo@example.com', hash_password('demo123'), 'Demo User'))
            print("✅ Demo user created (username: demo, password: demo123)")
        except Exception as e:
            print(f"ℹ️  Demo user creation error: {e}")
    else:
        print(f"ℹ️  Found {user_count} existing users - preserving them")
    
    conn.commit()
    conn.close()
    
    return tables_created

def show_table_summary():
    """Show all tables and their row counts"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n📊 Database Summary: {len(tables)} tables")
    print("=" * 50)
    
    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  📋 {table_name}: {count} rows")
    
    conn.close()

def main():
    """Safe database initialization"""
    print("🔒 Safe Database Initialization")
    print("=" * 50)
    print("This script will PRESERVE existing data and only create missing tables.")
    
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("📁 No existing database found - creating new one")
    else:
        print("📁 Existing database found - preserving data")
    
    tables_created = create_missing_tables()
    
    if tables_created > 0:
        print(f"\n✅ Created {tables_created} missing tables")
    else:
        print("\n✅ All tables already exist - no changes made")
    
    show_table_summary()
    
    print(f"\n📍 Database location: {db_path}")
    print("\n🔑 Demo Login (if created):")
    print("   Username: demo")
    print("   Password: demo123")

if __name__ == '__main__':
    main()