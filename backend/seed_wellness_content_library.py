"""
Seed Wellness Content Library
Populates database with curated videos, music, and blogs organized by mood/category
"""
import sqlite3
import json
from datetime import datetime

# Wellness Content Library organized by mood/purpose
WELLNESS_CONTENT = {
    # STRESS RELIEF
    'stress': [
        {
            'title': '10 Minute Guided Meditation for Stress',
            'description': 'Calm your mind and release tension with this guided meditation',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=z6X5oEIg6Ak',
            'duration_minutes': 10,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['stress', 'meditation', 'calm', 'anxiety'],
            'is_featured': True
        },
        {
            'title': 'Relaxing Music for Stress Relief',
            'description': 'Peaceful piano music to help you unwind and de-stress',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=lTRiuFIWV54',
            'duration_minutes': 180,
            'difficulty_level': 'low',
            'category': 'relaxation',
            'tags': ['stress', 'music', 'calm', 'relaxation'],
            'is_featured': True
        },
        {
            'title': '5 Minute Breathing Exercise for Stress',
            'description': 'Quick breathing technique to reduce stress instantly',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=tybOi4hjZFQ',
            'duration_minutes': 5,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['stress', 'breathing', 'quick relief'],
            'is_featured': False
        },
        {
            'title': 'Yoga for Stress Relief',
            'description': 'Gentle yoga flow to release tension and calm your mind',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=COp7BR_Dvps',
            'duration_minutes': 20,
            'difficulty_level': 'medium',
            'category': 'yoga',
            'tags': ['stress', 'yoga', 'exercise', 'flexibility'],
            'is_featured': False
        }
    ],
    
    # ANXIETY RELIEF
    'anxiety': [
        {
            'title': 'Guided Meditation for Anxiety',
            'description': 'Soothing meditation to ease anxious thoughts',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=O-6f5wQXSu8',
            'duration_minutes': 15,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['anxiety', 'meditation', 'calm', 'peace'],
            'is_featured': True
        },
        {
            'title': 'Calming Music for Anxiety',
            'description': 'Gentle ambient music to reduce anxiety and worry',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=1ZYbU82GVz4',
            'duration_minutes': 60,
            'difficulty_level': 'low',
            'category': 'relaxation',
            'tags': ['anxiety', 'music', 'calm', 'ambient'],
            'is_featured': True
        },
        {
            'title': '4-7-8 Breathing for Anxiety',
            'description': 'Powerful breathing technique to calm anxiety fast',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=gz4G31LGyog',
            'duration_minutes': 3,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['anxiety', 'breathing', 'quick relief', 'technique'],
            'is_featured': False
        }
    ],
    
    # ENERGY & MOTIVATION
    'energy': [
        {
            'title': 'Morning Yoga for Energy',
            'description': 'Energizing yoga flow to start your day right',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=VaoV1PrYft4',
            'duration_minutes': 15,
            'difficulty_level': 'medium',
            'category': 'yoga',
            'tags': ['energy', 'morning', 'yoga', 'motivation'],
            'is_featured': True
        },
        {
            'title': 'Upbeat Music for Energy',
            'description': 'Motivating music to boost your energy and mood',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=uwEaQk5VeS4',
            'duration_minutes': 30,
            'difficulty_level': 'low',
            'category': 'exercise',
            'tags': ['energy', 'music', 'motivation', 'upbeat'],
            'is_featured': True
        },
        {
            'title': '10 Minute Morning Workout',
            'description': 'Quick energizing workout to wake up your body',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=gC_L9qAHVJ8',
            'duration_minutes': 10,
            'difficulty_level': 'medium',
            'category': 'exercise',
            'tags': ['energy', 'workout', 'morning', 'fitness'],
            'is_featured': False
        }
    ],
    
    # SLEEP & RELAXATION
    'sleep': [
        {
            'title': 'Sleep Meditation - Deep Relaxation',
            'description': 'Guided meditation to help you fall asleep peacefully',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=aEqlQvczMJQ',
            'duration_minutes': 30,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['sleep', 'meditation', 'relaxation', 'bedtime'],
            'is_featured': True
        },
        {
            'title': 'Relaxing Sleep Music',
            'description': 'Peaceful music to help you drift off to sleep',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=lFcSrYw-ARY',
            'duration_minutes': 180,
            'difficulty_level': 'low',
            'category': 'relaxation',
            'tags': ['sleep', 'music', 'relaxation', 'calm'],
            'is_featured': True
        },
        {
            'title': 'Bedtime Yoga for Better Sleep',
            'description': 'Gentle yoga stretches to prepare your body for sleep',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=BiWDsfZ3zbo',
            'duration_minutes': 20,
            'difficulty_level': 'low',
            'category': 'yoga',
            'tags': ['sleep', 'yoga', 'bedtime', 'stretching'],
            'is_featured': False
        }
    ],
    
    # MINDFULNESS & MEDITATION
    'mindfulness': [
        {
            'title': 'Mindfulness Meditation for Beginners',
            'description': 'Learn the basics of mindfulness meditation',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=6p_yaNFSYao',
            'duration_minutes': 10,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['mindfulness', 'meditation', 'beginner', 'awareness'],
            'is_featured': True
        },
        {
            'title': 'Peaceful Meditation Music',
            'description': 'Serene music for meditation and mindfulness practice',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=5qap5aO4i9A',
            'duration_minutes': 60,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['mindfulness', 'meditation', 'music', 'peace'],
            'is_featured': True
        },
        {
            'title': 'Body Scan Meditation',
            'description': 'Mindful body scan to increase awareness and relaxation',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=15q-N-_kkrU',
            'duration_minutes': 15,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['mindfulness', 'meditation', 'body scan', 'awareness'],
            'is_featured': False
        }
    ],
    
    # MOOD BOOST & HAPPINESS
    'mood_boost': [
        {
            'title': 'Happy Music Playlist',
            'description': 'Uplifting music to boost your mood instantly',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=ZbZSe6N_BXs',
            'duration_minutes': 60,
            'difficulty_level': 'low',
            'category': 'relaxation',
            'tags': ['mood boost', 'music', 'happy', 'uplifting'],
            'is_featured': True
        },
        {
            'title': 'Gratitude Meditation',
            'description': 'Cultivate gratitude and positive emotions',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=nj-hdQP_lJo',
            'duration_minutes': 10,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['mood boost', 'gratitude', 'meditation', 'positive'],
            'is_featured': True
        },
        {
            'title': 'Dance Workout for Mood',
            'description': 'Fun dance workout to lift your spirits',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=gBAfejjUQoA',
            'duration_minutes': 20,
            'difficulty_level': 'medium',
            'category': 'exercise',
            'tags': ['mood boost', 'dance', 'workout', 'fun'],
            'is_featured': False
        }
    ],
    
    # FOCUS & CONCENTRATION
    'focus': [
        {
            'title': 'Focus Music - Study & Work',
            'description': 'Concentration music to enhance productivity',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=jfKfPfyJRdk',
            'duration_minutes': 180,
            'difficulty_level': 'low',
            'category': 'relaxation',
            'tags': ['focus', 'music', 'study', 'work', 'concentration'],
            'is_featured': True
        },
        {
            'title': 'Meditation for Focus',
            'description': 'Sharpen your mind and improve concentration',
            'content_type': 'video',
            'content_url': 'https://www.youtube.com/watch?v=SEfs5TJZ6Nk',
            'duration_minutes': 10,
            'difficulty_level': 'low',
            'category': 'mindfulness',
            'tags': ['focus', 'meditation', 'concentration', 'clarity'],
            'is_featured': True
        }
    ]
}


def create_content_tables(conn):
    """Create content tables if they don't exist"""
    cursor = conn.cursor()
    
    # Create content_categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            color TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create content_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT NOT NULL,
            content_url TEXT NOT NULL,
            duration_minutes INTEGER,
            difficulty_level TEXT,
            tags TEXT,
            is_featured INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES content_categories(id)
        )
    """)
    
    # Create user_content_interactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_content_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content_id INTEGER NOT NULL,
            interaction_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content_items(id)
        )
    """)
    
    conn.commit()
    print("✅ Content tables created")


def seed_categories(conn):
    """Seed content categories"""
    cursor = conn.cursor()
    
    categories = [
        ('Mindfulness', 'mindfulness', 'Meditation and mindfulness practices', '🧘', '#9333EA', 1),
        ('Yoga', 'yoga', 'Yoga flows and stretches', '🤸', '#EC4899', 2),
        ('Exercise', 'exercise', 'Workouts and physical activities', '💪', '#F59E0B', 3),
        ('Relaxation', 'relaxation', 'Music and sounds for relaxation', '🎵', '#3B82F6', 4),
        ('Healthy Eating', 'healthy-eating', 'Nutrition and healthy eating tips', '🥗', '#10B981', 5),
        ('Smoking Cessation', 'smoking-cessation', 'Resources to quit smoking', '🚭', '#EF4444', 6)
    ]
    
    for name, slug, desc, icon, color, order in categories:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO content_categories 
                (name, slug, description, icon, color, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, slug, desc, icon, color, order))
        except Exception as e:
            print(f"Error inserting category {name}: {e}")
    
    conn.commit()
    print(f"✅ Seeded {len(categories)} categories")


def seed_content(conn):
    """Seed wellness content"""
    cursor = conn.cursor()
    
    # Get category IDs
    cursor.execute("SELECT id, slug FROM content_categories")
    category_map = {slug: id for id, slug in cursor.fetchall()}
    
    total_content = 0
    
    for mood_category, content_list in WELLNESS_CONTENT.items():
        for content in content_list:
            # Map content category to database category
            category_slug = content['category']
            category_id = category_map.get(category_slug)
            
            if not category_id:
                print(f"⚠️  Category not found: {category_slug}")
                continue
            
            try:
                cursor.execute("""
                    INSERT INTO content_items 
                    (category_id, title, description, content_type, content_url, 
                     duration_minutes, difficulty_level, tags, is_featured)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category_id,
                    content['title'],
                    content['description'],
                    content['content_type'],
                    content['content_url'],
                    content['duration_minutes'],
                    content['difficulty_level'],
                    json.dumps(content['tags']),
                    1 if content['is_featured'] else 0
                ))
                total_content += 1
            except Exception as e:
                print(f"Error inserting content '{content['title']}': {e}")
    
    conn.commit()
    print(f"✅ Seeded {total_content} content items")


def show_content_summary(conn):
    """Show summary of seeded content"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("CONTENT LIBRARY SUMMARY")
    print("=" * 80)
    
    # Count by category
    cursor.execute("""
        SELECT c.name, c.icon, COUNT(ci.id) as count
        FROM content_categories c
        LEFT JOIN content_items ci ON c.id = ci.category_id
        GROUP BY c.id
        ORDER BY c.display_order
    """)
    
    print("\nContent by Category:")
    for name, icon, count in cursor.fetchall():
        print(f"  {icon} {name}: {count} items")
    
    # Count by mood/purpose
    print("\nContent by Mood/Purpose:")
    for mood, content_list in WELLNESS_CONTENT.items():
        print(f"  {mood}: {len(content_list)} items")
    
    # Featured content
    cursor.execute("SELECT COUNT(*) FROM content_items WHERE is_featured = 1")
    featured_count = cursor.fetchone()[0]
    print(f"\nFeatured Content: {featured_count} items")
    
    # Total content
    cursor.execute("SELECT COUNT(*) FROM content_items")
    total_count = cursor.fetchone()[0]
    print(f"Total Content: {total_count} items")
    
    print("\n" + "=" * 80)


def main():
    """Main function to seed wellness content"""
    import os
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'mood_capture.db')
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("SEEDING WELLNESS CONTENT LIBRARY")
    print("=" * 80)
    print()
    
    try:
        # Create tables
        create_content_tables(conn)
        
        # Seed categories
        seed_categories(conn)
        
        # Seed content
        seed_content(conn)
        
        # Show summary
        show_content_summary(conn)
        
        print("\n✅ Wellness content library seeded successfully!")
        print("\nYou can now:")
        print("1. Restart your backend server")
        print("2. Ask for activity suggestions")
        print("3. Click on videos/music to open them")
        print("4. System will follow up when you return")
        
    except Exception as e:
        print(f"\n❌ Error seeding content: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
