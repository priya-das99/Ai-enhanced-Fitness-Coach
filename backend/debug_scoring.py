#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import sqlite3
import json

# Check what's in the database
conn = sqlite3.connect('backend/mood_capture.db')
cursor = conn.cursor()

print("\n=== CONTENT ITEMS ===")
cursor.execute("SELECT id, title, tags FROM content_items WHERE is_active = 1 LIMIT 5")
for row in cursor.fetchall():
    content_id, title, tags = row
    try:
        tags_list = json.loads(tags) if tags else []
    except:
        tags_list = tags.split(',') if tags else []
    print(f"content_{content_id}: {title}")
    print(f"  Tags: {tags_list}")
    print(f"  Has 'work' tag: {'work' in tags_list}")
    print(f"  Has 'stress' tag: {'stress' in tags_list}\n")

print("\n=== ACTIVITIES ===")
cursor.execute("SELECT suggestion_key, title, best_for FROM suggestion_master WHERE is_active = 1 LIMIT 5")
for row in cursor.fetchall():
    key, title, best_for = row
    try:
        tags_list = json.loads(best_for) if best_for else []
    except:
        tags_list = []
    print(f"{key}: {title}")
    print(f"  Tags: {tags_list}")
    print(f"  Has 'work' tag: {'work' in tags_list}")
    print(f"  Has 'stress' tag: {'stress' in tags_list}\n")

conn.close()
