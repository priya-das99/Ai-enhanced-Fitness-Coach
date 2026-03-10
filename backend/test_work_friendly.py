#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import _load_activities_from_db
from chat_assistant.context_builder_simple import build_context

# Load activities
activities = _load_activities_from_db()

# Build context
context = build_context(1)

print(f"\nContext is_work_hours: {context.get('is_work_hours', False)}\n")

# Check work_friendly status
print("=== WORK-FRIENDLY STATUS ===\n")

work_friendly_count = 0
not_work_friendly_count = 0

for key, activity in activities.items():
    is_work_friendly = activity.get('work_friendly', False)
    if is_work_friendly:
        work_friendly_count += 1
    else:
        not_work_friendly_count += 1

print(f"Work-friendly: {work_friendly_count}")
print(f"NOT work-friendly: {not_work_friendly_count}")
print(f"\nIf is_work_hours=True, {not_work_friendly_count} activities would be filtered out!\n")

# Show some examples
print("=== EXAMPLES ===\n")
count = 0
for key, activity in activities.items():
    print(f"{key}: {activity['name']}")
    print(f"  work_friendly: {activity.get('work_friendly', False)}")
    print(f"  effort: {activity.get('effort', 'N/A')}\n")
    count += 1
    if count >= 5:
        break
