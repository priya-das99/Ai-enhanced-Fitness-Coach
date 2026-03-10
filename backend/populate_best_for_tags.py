#!/usr/bin/env python3
"""
Populate best_for tags for existing activities
"""

import sqlite3
import json

# Define best_for tags for each activity
ACTIVITY_TAGS = {
    'breathing': ['stress', 'anxiety', 'calm', 'focus'],
    'short_walk': ['energy', 'mood boost', 'physical tension', 'fresh air'],
    'meditation': ['stress', 'anxiety', 'calm', 'focus', 'overwhelm'],
    'stretching': ['physical tension', 'energy', 'tired', 'desk work'],
    'take_break': ['burnout', 'overwhelm', 'tired', 'work'],
    'journaling': ['self-reflection', 'mood boost', 'clarity', 'overwhelm'],
    'music': ['mood boost', 'calm', 'stress', 'energy'],
    'call_friend': ['loneliness', 'support', 'relationship', 'mood boost'],
    'hydrate': ['energy', 'health', 'tired', 'focus'],
    'power_nap': ['tired', 'energy', 'burnout', 'sleep'],
    'quick_workout': ['energy', 'mood boost', 'stress', 'physical tension'],
    'outdoor_time': ['mood boost', 'fresh air', 'energy', 'nature'],
    'healthy_snack': ['energy', 'health', 'mood boost', 'food'],
}

def populate_tags():
    conn = sqlite3.connect('backend/mood_capture.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("Populating best_for tags for activities")
    print("="*60 + "\n")
    
    for activity_key, tags in ACTIVITY_TAGS.items():
        tags_json = json.dumps(tags)
        
        cursor.execute("""
            UPDATE suggestion_master
            SET best_for = ?
            WHERE suggestion_key = ?
        """, (tags_json, activity_key))
        
        if cursor.rowcount > 0:
            print(f"✓ {activity_key}: {tags}")
        else:
            print(f"⚠ {activity_key}: not found in database")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Tags populated successfully!")
    print("="*60 + "\n")

if __name__ == "__main__":
    populate_tags()
