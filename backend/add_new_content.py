#!/usr/bin/env python3
"""
Add new Yoga and Mindfulness content to the database
"""

import sqlite3
import json

# New content to add
NEW_CONTENT = [
    # YOGA Category
    {
        'title': '9 Best Chair Yoga Poses to Do at Your Desk',
        'description': 'Simple chair yoga poses you can do right at your desk to relieve tension and improve flexibility',
        'content_type': 'article',
        'content_url': 'https://www.vantagefit.io/en/blog/chair-yoga-poses/',
        'category': 'yoga',
        'duration_minutes': 10,
        'difficulty_level': 'low',
        'tags': ['yoga', 'desk work', 'office', 'stretching', 'work'],
        'is_featured': False
    },
    {
        'title': 'Top 15 Office Yoga Poses for Desk Warriors',
        'description': 'Essential yoga poses designed specifically for people who work at desks all day',
        'content_type': 'article',
        'content_url': 'https://www.vantagefit.io/en/blog/yoga-in-the-workplace/',
        'category': 'yoga',
        'duration_minutes': 15,
        'difficulty_level': 'low',
        'tags': ['yoga', 'office', 'desk work', 'work', 'physical tension'],
        'is_featured': False
    },
    {
        'title': 'Key Benefits of Yoga at Work to Boost Productivity',
        'description': 'Discover how yoga can improve your productivity and well-being at work',
        'content_type': 'article',
        'content_url': 'https://www.hopkinsmedicine.org/health/wellness-and-prevention/9-benefits-of-yoga',
        'category': 'yoga',
        'duration_minutes': 5,
        'difficulty_level': 'low',
        'tags': ['yoga', 'work', 'productivity', 'health', 'wellness'],
        'is_featured': False
    },
    # MINDFULNESS Category
    {
        'title': 'What is Stress Cycle',
        'description': 'Understanding the stress cycle and how it affects your body and mind',
        'content_type': 'article',
        'content_url': 'https://www.idanim.com/blog/the-stress-cycle-how-to-feel-safe-after-stressful-situations',
        'category': 'mindfulness',
        'duration_minutes': 8,
        'difficulty_level': 'low',
        'tags': ['stress', 'anxiety', 'mindfulness', 'calm', 'health'],
        'is_featured': False
    },
    {
        'title': 'The Stress Cycle: How to Feel Safe After Stressful Situations',
        'description': 'Learn practical techniques to complete the stress cycle and feel safe again',
        'content_type': 'article',
        'content_url': 'https://www.vantagefit.io/en/blog/employee-wellness-and-stress-management/',
        'category': 'mindfulness',
        'duration_minutes': 10,
        'difficulty_level': 'low',
        'tags': ['stress', 'anxiety', 'calm', 'wellness', 'work'],
        'is_featured': False
    },
    {
        'title': 'Mindful Affirmations to Calm and Love Yourself',
        'description': 'Guided mindful affirmations to help you find calm and self-compassion',
        'content_type': 'video',
        'content_url': 'https://www.youtube.com/watch?v=0H_AeBQY4gA',
        'category': 'mindfulness',
        'duration_minutes': 15,
        'difficulty_level': 'low',
        'tags': ['mindfulness', 'calm', 'self-care', 'meditation', 'stress'],
        'is_featured': False
    }
]

def add_content():
    conn = sqlite3.connect('backend/mood_capture.db')
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("Adding New Yoga and Mindfulness Content")
    print("="*70 + "\n")
    
    # Get category IDs
    cursor.execute("SELECT id, slug FROM content_categories")
    categories = {slug: cat_id for cat_id, slug in cursor.fetchall()}
    
    print(f"Available categories: {list(categories.keys())}\n")
    
    added_count = 0
    
    for content in NEW_CONTENT:
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
        
        print(f"✓ Added: {content['title']}")
        print(f"  Category: {category_slug}")
        print(f"  Type: {content['content_type']}")
        print(f"  Tags: {content['tags']}")
        print(f"  URL: {content['content_url'][:50]}...\n")
        
        added_count += 1
    
    conn.commit()
    conn.close()
    
    print("="*70)
    print(f"✅ Successfully added {added_count} new content items!")
    print("="*70 + "\n")

if __name__ == "__main__":
    add_content()
