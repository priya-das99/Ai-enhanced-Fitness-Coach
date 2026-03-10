#!/usr/bin/env python3
"""Check what activity tables and data exist"""

import sqlite3

conn = sqlite3.connect('backend/mood_capture.db')
cursor = conn.cursor()

print("\n=== Tables with 'activity' or 'content' ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%activity%' OR name LIKE '%content%' OR name LIKE '%wellness%')")
tables = cursor.fetchall()
for t in tables:
    print(f"  {t[0]}")

print("\n=== Checking content_items table ===")
cursor.execute("SELECT id, title, category, content_type FROM content_items LIMIT 10")
rows = cursor.fetchall()
print("Sample content:")
for r in rows:
    print(f"  ID: {r[0]}, Title: {r[1]}, Category: {r[2]}, Type: {r[3]}")

print("\n=== Checking predefined activities in smart_suggestions.py ===")
print("Activities defined in WELLNESS_ACTIVITIES dict:")
print("  - meditation")
print("  - breathing")
print("  - short_walk")
print("  - stretching")
print("  - take_break")
print("  - etc.")

conn.close()
