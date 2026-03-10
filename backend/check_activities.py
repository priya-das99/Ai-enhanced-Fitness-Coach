#!/usr/bin/env python3
"""Check what activities are in the database"""
import sqlite3

conn = sqlite3.connect('fitness_chat.db')
cursor = conn.cursor()

# Check tables
print("\n📋 Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"  - {table}")

# Check if wellness_content exists
if 'wellness_content' in tables:
    print("\n✅ wellness_content table exists")
    cursor.execute("SELECT COUNT(*) FROM wellness_content")
    count = cursor.fetchone()[0]
    print(f"   Total activities: {count}")
    
    # Show first 10
    cursor.execute("SELECT id, name, best_for FROM wellness_content LIMIT 10")
    print("\n   First 10 activities:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")
        print(f"      best_for: {row[2]}")
else:
    print("\n❌ wellness_content table does NOT exist!")
    print("   Activities are coming from hardcoded WELLNESS_ACTIVITIES_FALLBACK")

# Check module_activities
if 'module_activities' in tables:
    print("\n📦 module_activities table exists")
    cursor.execute("SELECT COUNT(*) FROM module_activities")
    count = cursor.fetchone()[0]
    print(f"   Total module activities: {count}")
    
    cursor.execute("SELECT id, name, tags FROM module_activities LIMIT 10")
    print("\n   First 10 module activities:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")
        print(f"      tags: {row[2]}")

conn.close()
