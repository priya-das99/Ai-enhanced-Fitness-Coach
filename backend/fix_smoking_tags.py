#!/usr/bin/env python3
"""
Fix smoking cessation content tags
"""

import sqlite3
import json

# Correct tags for smoking cessation content
SMOKING_TAGS = {
    13: ['smoking', 'quit smoking', 'cessation', 'health', 'timeline'],  # Quit Smoking Timeline
    14: ['smoking', 'cravings', 'cessation', 'support', 'addiction'],  # Coping with Cravings
    15: ['smoking', 'breathing', 'cessation', 'recovery', 'health'],  # Breathing Exercises for Ex-Smokers
}

conn = sqlite3.connect('backend/mood_capture.db')
cursor = conn.cursor()

print("\n" + "="*70)
print("Fixing Smoking Cessation Content Tags")
print("="*70 + "\n")

for content_id, tags in SMOKING_TAGS.items():
    tags_json = json.dumps(tags)
    
    # Get current title
    cursor.execute("SELECT title FROM content_items WHERE id = ?", (content_id,))
    title = cursor.fetchone()[0]
    
    cursor.execute("""
        UPDATE content_items
        SET tags = ?
        WHERE id = ?
    """, (tags_json, content_id))
    
    print(f"✓ ID {content_id}: {title}")
    print(f"  New tags: {tags}\n")

conn.commit()
conn.close()

print("="*70)
print("✅ Smoking cessation tags updated!")
print("="*70 + "\n")
