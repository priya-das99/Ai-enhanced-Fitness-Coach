#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import _load_activities_from_db, _categorize_reason, CATEGORY_TO_ACTIVITY_TAGS

# Load activities
activities = _load_activities_from_db()

# Test "work" reason
reason = "work"
categories = _categorize_reason(reason)

print(f"\nReason: '{reason}'")
print(f"Categories: {categories}")
print(f"Expected tags: {[CATEGORY_TO_ACTIVITY_TAGS.get(cat, []) for cat in categories]}\n")

# Find activities that match "work"
print("=== ACTIVITIES MATCHING 'WORK' ===\n")

work_activities = []
for key, activity in activities.items():
    best_for = activity.get('best_for', [])
    
    # Check if any work-related tag is in best_for
    work_tags = ['work', 'stress', 'overwhelm', 'burnout', 'desk work']
    has_work_tag = any(tag in best_for for tag in work_tags)
    
    if has_work_tag:
        work_activities.append((key, activity, best_for))

print(f"Found {len(work_activities)} activities matching work\n")

# Show them
for key, activity, tags in work_activities[:10]:
    is_content = key.startswith('content_')
    type_str = "CONTENT" if is_content else "ACTIVITY"
    print(f"[{type_str}] {key}: {activity['name']}")
    print(f"  Tags: {tags}\n")
