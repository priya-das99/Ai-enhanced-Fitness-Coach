#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import _load_activities_from_db

# Load activities
activities = _load_activities_from_db()

print(f"\nTotal activities loaded: {len(activities)}\n")

# Count by type
content_count = sum(1 for k in activities.keys() if k.startswith('content_'))
activity_count = len(activities) - content_count

print(f"Activities: {activity_count}")
print(f"Content items: {content_count}\n")

# Show some content items
print("=== CONTENT ITEMS ===")
for key, activity in activities.items():
    if key.startswith('content_'):
        print(f"{key}: {activity['name']}")
        print(f"  best_for: {activity.get('best_for', [])}")
        print(f"  action_type: {activity.get('action_type', 'N/A')}\n")
        if key == 'content_5':
            break

# Show some regular activities
print("\n=== REGULAR ACTIVITIES ===")
count = 0
for key, activity in activities.items():
    if not key.startswith('content_'):
        print(f"{key}: {activity['name']}")
        print(f"  best_for: {activity.get('best_for', [])}\n")
        count += 1
        if count >= 3:
            break
