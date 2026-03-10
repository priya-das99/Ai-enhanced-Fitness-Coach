# Activity Reminder & Summary System - Implementation Complete

## What Was Implemented

### 1. **UserContextService** (`app/services/user_context_service.py`)
Centralized service for retrieving user activity data.

**Methods:**
- `get_daily_summary(user_id)` - Complete daily activity summary
- `get_challenge_progress_today(user_id, challenge_type)` - Today's progress for specific challenge
- `get_all_challenges_progress(user_id)` - Progress for all active challenges
- `should_send_reminder(user_id, reminder_type)` - Smart reminder logic
- `get_active_users()` - List of active users

### 2. **NotificationService** (`app/services/notification_service.py`)
Handles notification delivery.

**Methods:**
- `send_notification(user_id, notification)` - Send notification
- `get_unread_notifications(user_id)` - Get unread notifications
- `mark_as_read(notification_id)` - Mark as read

**Storage:**
- Stores in `notifications` table
- Also stores as system message in `chat_messages` table

### 3. **Scheduler** (`app/scheduler.py`)
APScheduler for proactive reminders.

**Jobs:**
- `water_reminder_job()` - 2 PM daily
- `mood_reminder_job()` - 10 AM daily
- `exercise_reminder_job()` - 6 PM daily
- `evening_challenges_job()` - 8 PM daily

### 4. **ActivitySummaryWorkflow** (`chat_assistant/activity_summary_workflow.py`)
Handles user queries about their activities.

**Handles:**
- "What did I do today?"
- "How much water did I drink?"
- "Did I exercise today?"
- "What's my progress?"

### 5. **Intent Detection** (Updated)
Added `activity_summary` intent to LLM intent extractor.

### 6. **Workflow Registration** (Updated)
Registered ActivitySummaryWorkflow in workflow registry.

### 7. **FastAPI Integration** (Updated)
Added scheduler startup/shutdown in `app/main.py`.

---

## Installation

```bash
# Install APScheduler
pip install apscheduler==3.10.4

# Or use requirements file
pip install -r requirements_scheduler.txt
```

---

## How It Works

### Proactive Reminders (Scheduler)

```
2:00 PM → Scheduler wakes up
  ↓
For each active user:
  ↓
Check if water reminder needed:
  - Has active water challenge?
  - Less than 50% complete?
  - After 2 PM?
  ↓
If YES → Send notification:
  "You've only had 2/8 glasses today!"
  [Log Water] button
  ↓
Store in database as system message
```

### User Queries (Workflow)

```
User: "How much water did I drink?"
  ↓
Intent Detection → activity_summary
  ↓
ActivitySummaryWorkflow
  ↓
UserContextService.get_challenge_progress_today()
  ↓
Query database for today's water logs
  ↓
Calculate progress
  ↓
Format response:
  "You've logged 2/8 glasses today (25%)"
  "Remaining: 6 glasses"
```

---

## Testing

```bash
# Test the system
python test_activity_summary_system.py
```

**Tests:**
1. UserContextService - Get daily summary, challenge progress
2. NotificationService - Send and retrieve notifications
3. ActivitySummaryWorkflow - Answer user queries

---

## Usage Examples

### Scheduler Reminders

**Water Reminder (2 PM):**
```
💡 Hydration Reminder

You've only had 2/8 glasses today. Don't forget to drink water! 💧

[Log Water]
```

**Mood Reminder (10 AM):**
```
💡 Mood Check-in

Good morning! How are you feeling today? Take a moment to check in with yourself.

[Log Mood]
```

**Exercise Reminder (6 PM):**
```
💡 Exercise Reminder

You haven't logged any exercise today! Your goal is 30 minutes. Let's get moving! 🏃

[Log Exercise]
```

**Evening Challenges (8 PM):**
```
💡 Challenge Reminder

You have 2 challenges still pending today:

• 7-Day Hydration Challenge: 25%
• Daily Exercise: 0%

You've got this! 💪
```

### User Queries

**Query: "What did I do today?"**
```
📊 Here's your activity summary for today:

💧 Water: 2/8 glasses
😴 Sleep: 7/8 hours
🏃 Exercise: 0/30 minutes
😊 Mood: 😊

✨ Total activities logged: 3

Good start! Keep it up! 💪
```

**Query: "How much water did I drink?"**
```
You're making progress on water! 📈

Today: 2/8 glasses (25%)
Remaining: 6 glasses

You've got this! 🔥
```

**Query: "Did I exercise today?"**
```
You haven't logged any exercise today yet.

Your goal: 30 minutes

Let's get started! 🚀
```

**Query: "What's my progress?"**
```
📊 Your Challenge Progress:

✅ Completed Today:
  • Sleep Challenge: 7/8 hours ✓

📈 In Progress:
  • 7-Day Hydration Challenge: 2/8 glasses (25%)
  • Daily Exercise: 0/30 minutes (0%)

💪 Great progress! Keep going!
```

---

## Scheduler Configuration

### Reminder Times

| Reminder | Time | Condition |
|----------|------|-----------|
| Water | 2 PM | < 50% complete |
| Mood | 10 AM | Not logged yet |
| Exercise | 6 PM | Not completed |
| Evening Challenges | 8 PM | Any incomplete |

### Customization

Edit `app/scheduler.py` to change times:

```python
@scheduler.scheduled_job('cron', hour=14, minute=0)  # Change hour
async def water_reminder_job():
    # ...
```

---

## Database Tables

### notifications
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    action_buttons TEXT,
    priority TEXT DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    read_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### chat_messages (Updated)
System messages are stored with `sender='system'` and `message_type='reminder'`.

---

## Monitoring

### Check Scheduler Status

```python
from app.scheduler import get_scheduler_status

status = get_scheduler_status()
print(status)
# {
#     'running': True,
#     'jobs_count': 4,
#     'jobs': [
#         {'id': 'water_reminder', 'next_run': '2026-03-06T14:00:00'},
#         {'id': 'mood_reminder', 'next_run': '2026-03-07T10:00:00'},
#         ...
#     ]
# }
```

### View Logs

```bash
# Scheduler logs
tail -f logs/app.log | grep "Running.*reminder"

# Example output:
# 2026-03-06 14:00:00 INFO Running water reminder job
# 2026-03-06 14:00:01 INFO   ✓ Sent water reminder to user 1
# 2026-03-06 14:00:02 INFO ✅ Water reminder job complete: 5/10 sent
```

---

## Next Steps

### Phase 2: WebSocket Integration
- Real-time notification delivery
- In-chat system messages
- See: `IN_CHAT_NOTIFICATION_SYSTEM.md`

### Phase 3: Advanced Features
- Weekly summaries
- Streak celebrations
- Pattern detection
- Personalized tips

### Phase 4: User Preferences
- Allow users to enable/disable reminders
- Customize reminder times
- Set notification preferences

---

## Troubleshooting

### Scheduler Not Running

**Check:**
```python
from app.scheduler import scheduler
print(scheduler.running)  # Should be True
print(scheduler.get_jobs())  # Should show 4 jobs
```

**Fix:**
- Ensure `start_scheduler()` is called in `app/main.py`
- Check logs for errors
- Restart FastAPI server

### Notifications Not Appearing

**Check:**
1. Database table exists: `SELECT * FROM notifications LIMIT 1`
2. Notifications are being created: `SELECT COUNT(*) FROM notifications`
3. Chat messages are being created: `SELECT * FROM chat_messages WHERE sender='system'`

**Fix:**
- Run migrations if tables don't exist
- Check notification service logs
- Verify user_id is correct

### Reminders Not Sending

**Check:**
1. User has active challenges
2. Reminder conditions are met (time, progress, etc.)
3. User is in active_users list

**Debug:**
```python
from app.services.user_context_service import get_context_service

context = get_context_service()
result = context.should_send_reminder(user_id, 'water_reminder')
print(result)  # Check should_send and reason
```

---

## Summary

✅ **Implemented:**
- Proactive reminders (4 types)
- Activity summary queries
- Smart reminder logic
- Notification storage
- Scheduler integration

✅ **Works:**
- Scheduler runs automatically
- Reminders sent at scheduled times
- Users can query their activities
- Notifications stored in database

✅ **Ready for:**
- Production deployment
- WebSocket integration
- Advanced features
