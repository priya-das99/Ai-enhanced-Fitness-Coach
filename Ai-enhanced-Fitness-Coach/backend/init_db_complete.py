#!/usr/bin/env python3
"""
Complete Database Initialization Script
Runs all migrations to create the full database schema
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

def create_base_tables():
    """Create the 6 base tables from init_db.py"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("Creating base tables...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Drop old mood_logs if exists and recreate with proper schema
    cursor.execute('DROP TABLE IF EXISTS mood_logs')
    
    # Mood logs table
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
    
    # Action suggestions table
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
    
    # Chat sessions table
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
    
    # User activity history table
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
    
    # Health activities table
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
    
    conn.commit()
    conn.close()
    print("✅ Base tables created (6 tables)")

def run_analytics_migration():
    """Run migration 001: Analytics tables"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("Running migration 001: Analytics tables...")
    
    # analytics_events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_events ON analytics_events(user_id, event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON analytics_events(created_at)")
    
    # user_behavior_metrics
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
    
    # suggestion_master
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
            triggers_module TEXT,
            module_type TEXT DEFAULT 'internal',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # suggestion_history
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
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_suggestions ON suggestion_history(user_id, suggestion_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shown_at ON suggestion_history(shown_at)")
    
    # Populate suggestions
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
    
    conn.commit()
    conn.close()
    print("✅ Analytics tables created (4 tables)")

def run_chat_migration():
    """Run migration 002: Chat history"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("Running migration 002: Chat history...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
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
    
    conn.commit()
    conn.close()
    print("✅ Chat history table created (1 table)")

def run_challenges_migration():
    """Run migration 003: Challenges system"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("Running migration 003: Challenges system...")
    
    # Challenges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
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
    ''')
    
    # User challenge participation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_challenges (
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
    ''')
    
    # Daily challenge progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_progress (
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
    ''')
    
    # User points
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_points (
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
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_challenges_active ON challenges(is_active, start_date, end_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_challenges_status ON user_challenges(user_id, status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_challenge_progress_date ON challenge_progress(user_challenge_id, date)')
    
    conn.commit()
    conn.close()
    print("✅ Challenges system created (4 tables)")

def run_wellness_migration():
    """Run migration 005: Wellness content"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("Running migration 005: Wellness content...")
    
    # Content Categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_categories (
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
    """)
    
    # Content Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
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
    """)
    
    # User Content Interactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_content_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content_id INTEGER NOT NULL,
            interaction_type TEXT NOT NULL,
            progress_percent INTEGER DEFAULT 0,
            time_spent_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
        )
    """)
    
    # User Wellness Preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_wellness_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            smoking_status TEXT,
            fitness_goals TEXT,
            interests TEXT,
            preferred_content_types TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed categories
    categories = [
        ('Yoga', 'yoga', 'Stress relief, mindfulness, and physical wellness', '🧘', '#8B5CF6', 1, 1),
        ('Mindfulness', 'mindfulness', 'Meditation and stress management', '🧠', '#10B981', 1, 2),
        ('Exercise', 'exercise', 'Fitness and physical activity', '💪', '#F59E0B', 1, 3),
        ('Healthy Eating', 'healthy-eating', 'Nutrition and healthy lifestyle', '🥗', '#EF4444', 1, 4),
        ('Smoking Cessation', 'smoking-cessation', 'Support for quitting smoking', '🚭', '#6B7280', 1, 5)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO content_categories 
        (name, slug, description, icon, color, is_active, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, categories)
    
    conn.commit()
    conn.close()
    print("✅ Wellness content created (4 tables)")

def create_demo_user():
    """Create demo user"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        ''', ('demo', 'demo@example.com', hash_password('demo123'), 'Demo User'))
        print("✅ Demo user created (username: demo, password: demo123)")
    except Exception as e:
        print(f"ℹ️  Demo user already exists or error: {e}")
    
    conn.commit()
    conn.close()

def show_table_summary():
    """Show all created tables"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n📊 Database Summary: {len(tables)} tables created")
    print("=" * 50)
    
    # Group tables by category
    base_tables = ['users', 'mood_logs', 'action_suggestions', 'chat_sessions', 'user_activity_history', 'health_activities']
    analytics_tables = ['analytics_events', 'user_behavior_metrics', 'suggestion_master', 'suggestion_history']
    chat_tables = ['chat_messages']
    challenge_tables = ['challenges', 'user_challenges', 'challenge_progress', 'user_points']
    wellness_tables = ['content_categories', 'content_items', 'user_content_interactions', 'user_wellness_preferences']
    
    def print_table_group(title, table_list):
        found_tables = [t[0] for t in tables if t[0] in table_list]
        if found_tables:
            print(f"\n{title} ({len(found_tables)} tables):")
            for table in found_tables:
                print(f"  ✅ {table}")
    
    print_table_group("Base System", base_tables)
    print_table_group("Analytics & Suggestions", analytics_tables)
    print_table_group("Chat System", chat_tables)
    print_table_group("Challenges System", challenge_tables)
    print_table_group("Wellness Content", wellness_tables)
    
    # Show any other tables
    all_categorized = base_tables + analytics_tables + chat_tables + challenge_tables + wellness_tables
    other_tables = [t[0] for t in tables if t[0] not in all_categorized]
    if other_tables:
        print_table_group("Other", other_tables)
    
    conn.close()

def main():
    """Initialize complete database"""
    print("🚀 Initializing Complete Database Schema")
    print("=" * 50)
    
    # Remove existing database to start fresh
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed existing database")
    
    # Run all migrations
    create_base_tables()
    run_analytics_migration()
    run_chat_migration()
    run_challenges_migration()
    run_wellness_migration()
    create_demo_user()
    
    # Show summary
    show_table_summary()
    
    print("\n🎉 Complete database initialization finished!")
    print(f"📍 Database location: {db_path}")
    print("\n🔑 Demo Login:")
    print("   Username: demo")
    print("   Password: demo123")

if __name__ == '__main__':
    main()