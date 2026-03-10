#!/usr/bin/env python3
"""
Add mood-boosting video content for sleep, tiredness, stress, and boredom
"""

import sqlite3
import json

# Mood-boosting video content
MOOD_VIDEOS = [
    # SLEEP & RELAXATION
    {
        'title': 'Deep Sleep Music - Peaceful Sleeping Music',
        'description': 'Calming music to help you fall asleep faster and sleep more deeply',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=1ZYbU82GVz4',
        'category': 'mindfulness',
        'duration_minutes': 30,
        'difficulty_level': 'low',
        'tags': ['sleep', 'tired', 'calm', 'relaxation', 'rest'],
        'is_featured': True
    },
    {
        'title': 'Relaxing Sleep Music - Fall Asleep Fast',
        'description': 'Soothing music with nature sounds to help you relax and fall asleep',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=lTRiuFIWV54',
        'category': 'mindfulness',
        'duration_minutes': 60,
        'difficulty_level': 'low',
        'tags': ['sleep', 'tired', 'calm', 'relaxation', 'evening'],
        'is_featured': False
    },
    {
        'title': 'Guided Sleep Meditation - Let Go of Stress',
        'description': 'Guided meditation to release stress and tension before sleep',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=aEqlQvczMJQ',
        'category': 'mindfulness',
        'duration_minutes': 20,
        'difficulty_level': 'low',
        'tags': ['sleep', 'meditation', 'stress', 'calm', 'relaxation'],
        'is_featured': False
    },
    
    # STRESS RELIEF
    {
        'title': 'Calming Music for Stress Relief',
        'description': 'Beautiful relaxing music to reduce stress and anxiety',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=lFcSrYw-ARY',
        'category': 'mindfulness',
        'duration_minutes': 30,
        'difficulty_level': 'low',
        'tags': ['stress', 'anxiety', 'calm', 'relaxation', 'mood boost'],
        'is_featured': True
    },
    {
        'title': 'Peaceful Music for Stress Relief and Healing',
        'description': 'Gentle music to help you unwind and release tension',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=1vx8iUvfyCY',
        'category': 'mindfulness',
        'duration_minutes': 45,
        'difficulty_level': 'low',
        'tags': ['stress', 'calm', 'relaxation', 'health', 'wellness'],
        'is_featured': False
    },
    {
        'title': '5-Minute Meditation for Stress',
        'description': 'Quick guided meditation to instantly reduce stress',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=SEfs5TJZ6Nk',
        'category': 'mindfulness',
        'duration_minutes': 5,
        'difficulty_level': 'low',
        'tags': ['stress', 'meditation', 'quick', 'calm', 'work'],
        'is_featured': False
    },
    
    # ENERGY & TIREDNESS
    {
        'title': 'Energizing Morning Music - Wake Up Motivated',
        'description': 'Uplifting music to boost your energy and start your day right',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=2OEL4P1Rz04',
        'category': 'mindfulness',
        'duration_minutes': 15,
        'difficulty_level': 'low',
        'tags': ['energy', 'mood boost', 'morning', 'motivation', 'tired'],
        'is_featured': False
    },
    {
        'title': 'Quick Energy Boost - 10 Minute Yoga',
        'description': 'Fast yoga routine to energize your body and mind',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=g_tea8ZNk5A',
        'category': 'yoga',
        'duration_minutes': 10,
        'difficulty_level': 'low',
        'tags': ['energy', 'yoga', 'tired', 'quick', 'mood boost'],
        'is_featured': False
    },
    
    # BOREDOM & MOOD BOOST
    {
        'title': 'Happy Music - Uplifting & Positive Energy',
        'description': 'Cheerful music to lift your spirits and boost your mood',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=bx1Bh8ZvH84',
        'category': 'mindfulness',
        'duration_minutes': 20,
        'difficulty_level': 'low',
        'tags': ['mood boost', 'bored', 'energy', 'happy', 'motivation'],
        'is_featured': True
    },
    {
        'title': 'Motivational Music - Boost Your Mood',
        'description': 'Inspiring music to overcome boredom and feel motivated',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=ZbZSe6N_BXs',
        'category': 'mindfulness',
        'duration_minutes': 30,
        'difficulty_level': 'low',
        'tags': ['mood boost', 'motivation', 'bored', 'energy', 'inspiration'],
        'is_featured': False
    },
    {
        'title': 'Feel Good Music - Positive Vibes',
        'description': 'Upbeat music to instantly improve your mood and energy',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=n61ULEU7CO0',
        'category': 'mindfulness',
        'duration_minutes': 25,
        'difficulty_level': 'low',
        'tags': ['mood boost', 'happy', 'energy', 'bored', 'motivation'],
        'is_featured': False
    },
    
    # FOCUS & PRODUCTIVITY (for boredom at work)
    {
        'title': 'Focus Music - Concentration and Study',
        'description': 'Background music to help you focus and beat work boredom',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=jfKfPfyJRdk',
        'category': 'mindfulness',
        'duration_minutes': 60,
        'difficulty_level': 'low',
        'tags': ['focus', 'work', 'bored', 'productivity', 'calm'],
        'is_featured': False
    }
]

def add_mood_videos():
    conn = sqlite3.connect('backend/mood_capture.db')
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("Adding Mood-Boosting Video Content")
    print("="*70 + "\n")
    
    # Get category IDs
    cursor.execute("SELECT id, slug FROM content_categories")
    categories = {slug: cat_id for cat_id, slug in cursor.fetchall()}
    
    print(f"Available categories: {list(categories.keys())}\n")
    
    added_count = 0
    by_mood = {'sleep': 0, 'stress': 0, 'energy': 0, 'boredom': 0}
    
    for content in MOOD_VIDEOS:
        category_slug = content['category']
        category_id = categories.get(category_slug)
        
        if not category_id:
            print(f"⚠️  Category '{category_slug}' not found, skipping: {content['title']}")
            continue
        
        # Convert tags to JSON
        tags_json = json.dumps(content['tags'])
        
        # Insert content
        cursor.execute("""
            INSERT INTO content_items (
                title, description, content_type, content_url,
                category_id, duration_minutes, difficulty_level,
                tags, is_featured, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            content['title'],
            content['description'],
            content['content_type'],
            content['content_url'],
            category_id,
            content['duration_minutes'],
            content['difficulty_level'],
            tags_json,
            content['is_featured']
        ))
        
        # Count by mood type
        tags = content['tags']
        if 'sleep' in tags or 'tired' in tags:
            by_mood['sleep'] += 1
        if 'stress' in tags or 'anxiety' in tags:
            by_mood['stress'] += 1
        if 'energy' in tags:
            by_mood['energy'] += 1
        if 'bored' in tags:
            by_mood['boredom'] += 1
        
        featured = "⭐" if content['is_featured'] else "  "
        print(f"{featured} ✓ {content['title']}")
        print(f"     Category: {category_slug} | Duration: {content['duration_minutes']}min")
        print(f"     Tags: {', '.join(content['tags'][:4])}")
        print(f"     URL: {content['content_url']}\n")
        
        added_count += 1
    
    conn.commit()
    conn.close()
    
    print("="*70)
    print(f"✅ Successfully added {added_count} mood-boosting videos!")
    print(f"\n📊 Content by mood:")
    print(f"   💤 Sleep/Tiredness: {by_mood['sleep']} videos")
    print(f"   😰 Stress Relief: {by_mood['stress']} videos")
    print(f"   ⚡ Energy Boost: {by_mood['energy']} videos")
    print(f"   😐 Boredom Relief: {by_mood['boredom']} videos")
    print("="*70 + "\n")

if __name__ == "__main__":
    add_mood_videos()
