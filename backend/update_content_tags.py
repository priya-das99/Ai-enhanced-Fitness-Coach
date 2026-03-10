#!/usr/bin/env python3
"""
Update content_items tags to match the best_for format
This will improve suggestion diversity by making content items
properly match user problems (stress, anxiety, work, etc.)
"""

import sqlite3
import json

# Map content items to appropriate best_for tags
CONTENT_TAG_MAPPING = {
    1: ['energy', 'mood boost', 'morning', 'physical tension'],  # Morning Sun Salutation
    2: ['calm', 'sleep', 'stress', 'evening'],  # Evening Relaxation Yoga
    3: ['work', 'physical tension', 'desk work', 'quick'],  # Desk Yoga Stretches
    4: ['stress', 'anxiety', 'calm', 'breathing'],  # 5-Minute Breathing Exercise
    5: ['stress', 'anxiety', 'calm', 'meditation'],  # Body Scan Meditation
    6: ['mindfulness', 'calm', 'focus', 'nature'],  # Mindful Walking Guide
    7: ['energy', 'mood boost', 'physical tension', 'quick'],  # 7-Minute HIIT Workout
    8: ['energy', 'physical tension', 'health', 'strength'],  # Beginner Strength Training
    9: ['energy', 'mood boost', 'fun', 'cardio'],  # Cardio Dance Workout
    10: ['health', 'food', 'energy', 'nutrition'],  # Meal Prep Basics
    11: ['health', 'food', 'energy', 'quick'],  # Quick Healthy Snacks
    12: ['health', 'food', 'nutrition', 'wellness'],  # Nutrition Fundamentals
    13: ['sleep', 'tired', 'rest', 'health'],  # Sleep Hygiene Tips
    14: ['sleep', 'calm', 'evening', 'routine'],  # Bedtime Routine Guide
    15: ['stress', 'work', 'burnout', 'overwhelm'],  # Managing Work Stress
}

def update_tags():
    conn = sqlite3.connect('backend/mood_capture.db')
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("Updating content_items tags for better suggestion diversity")
    print("="*70 + "\n")
    
    # Get all content items
    cursor.execute("SELECT id, title, tags FROM content_items")
    items = cursor.fetchall()
    
    print(f"Found {len(items)} content items\n")
    
    updated_count = 0
    for content_id, title, old_tags in items:
        if content_id in CONTENT_TAG_MAPPING:
            new_tags = CONTENT_TAG_MAPPING[content_id]
            new_tags_json = json.dumps(new_tags)
            
            cursor.execute("""
                UPDATE content_items
                SET tags = ?
                WHERE id = ?
            """, (new_tags_json, content_id))
            
            print(f"✓ ID {content_id}: {title[:40]}")
            print(f"  Old: {old_tags}")
            print(f"  New: {new_tags}\n")
            updated_count += 1
        else:
            print(f"⚠ ID {content_id}: {title[:40]} - No mapping defined\n")
    
    conn.commit()
    conn.close()
    
    print("="*70)
    print(f"✅ Updated {updated_count} content items successfully!")
    print("="*70 + "\n")
    
    print("Content items will now be properly matched to user problems:")
    print("  - Stress/Anxiety → Breathing, Meditation, Yoga")
    print("  - Work → Desk stretches, Work stress management")
    print("  - Energy/Tired → Morning yoga, HIIT, Healthy snacks")
    print("  - Sleep → Evening yoga, Sleep hygiene, Bedtime routine")
    print("  - Food/Health → Nutrition, Meal prep, Healthy snacks\n")

if __name__ == "__main__":
    update_tags()
