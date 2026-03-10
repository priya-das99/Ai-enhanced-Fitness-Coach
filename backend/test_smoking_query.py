#!/usr/bin/env python3
"""
Test smoking cessation query
"""

import sys
sys.path.insert(0, '.')
import sqlite3

# Check what's in the database for smoking cessation
conn = sqlite3.connect('backend/mood_capture.db')
cursor = conn.cursor()

print("\n=== SMOKING CESSATION CONTENT ===\n")

# Check content_categories
cursor.execute("SELECT id, name, slug FROM content_categories WHERE slug LIKE '%smok%'")
categories = cursor.fetchall()
print(f"Categories: {categories}\n")

# Check content_items
cursor.execute("""
    SELECT ci.id, ci.title, ci.content_type, ci.tags, c.name as category
    FROM content_items ci
    JOIN content_categories c ON ci.category_id = c.id
    WHERE c.slug LIKE '%smok%' OR ci.title LIKE '%smok%'
""")
items = cursor.fetchall()

print(f"Found {len(items)} smoking-related content items:\n")
for item in items:
    print(f"ID {item[0]}: {item[1]}")
    print(f"  Type: {item[2]}")
    print(f"  Category: {item[4]}")
    print(f"  Tags: {item[3]}\n")

conn.close()

# Now test if smart_suggestions would return these
print("\n=== TESTING SMART SUGGESTIONS ===\n")

from chat_assistant.smart_suggestions import get_smart_suggestions
from chat_assistant.context_builder_simple import build_context

context = build_context(1)

# Test with different reasons
for reason in ["smoking", "smoking cessation", "quit smoking"]:
    print(f"\nReason: '{reason}'")
    suggestions = get_smart_suggestions(
        mood_emoji="😐",
        reason=reason,
        context=context,
        count=5
    )
    
    print(f"Got {len(suggestions)} suggestions:")
    for i, sugg in enumerate(suggestions[:5], 1):
        print(f"  {i}. {sugg['name']}")
