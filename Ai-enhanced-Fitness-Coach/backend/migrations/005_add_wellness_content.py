"""Add wellness content system"""
import sqlite3
from datetime import datetime

def upgrade(conn):
    """Add wellness content tables"""
    cursor = conn.cursor()
    
    try:
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
        
        # Don't close connection - let migration runner handle it
        print("✅ Wellness content tables created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating tables: {e}")
        raise

def seed_initial_data(db_path: str):
    """Seed initial categories"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Insert categories
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
        
        print("✅ Categories seeded successfully")
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "mood_capture.db"
    upgrade(db_path)
    seed_initial_data(db_path)
