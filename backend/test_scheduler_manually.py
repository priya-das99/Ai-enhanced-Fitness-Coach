#!/usr/bin/env python3
"""
Manually trigger scheduler jobs for testing
This allows you to test reminders without waiting for scheduled times
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scheduler import (
    water_reminder_job,
    mood_reminder_job,
    exercise_reminder_job,
    evening_challenges_job
)

async def test_all_reminders():
    """Test all reminder jobs"""
    print("=" * 80)
    print("MANUALLY TRIGGERING SCHEDULER JOBS")
    print("=" * 80)
    
    print("\n1. Testing Water Reminder Job...")
    print("-" * 80)
    await water_reminder_job()
    
    print("\n2. Testing Mood Reminder Job...")
    print("-" * 80)
    await mood_reminder_job()
    
    print("\n3. Testing Exercise Reminder Job...")
    print("-" * 80)
    await exercise_reminder_job()
    
    print("\n4. Testing Evening Challenges Job...")
    print("-" * 80)
    await evening_challenges_job()
    
    print("\n" + "=" * 80)
    print("ALL JOBS COMPLETED")
    print("=" * 80)
    print("\nCheck the chat_messages table to see system notifications:")
    print("  SELECT * FROM chat_messages WHERE sender='system' ORDER BY created_at DESC LIMIT 5;")

if __name__ == "__main__":
    asyncio.run(test_all_reminders())
