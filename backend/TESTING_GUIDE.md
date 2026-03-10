# Testing Guide - Activity Reminders & Summary System

## Quick Start Testing

### 1. Test Activity Summary Queries

```bash
cd backend
python test_activity_queries.py
```

This will test queries like:
- "What did I do today?"
- "How much water did I drink?"
- "What's my progress?"

### 2. Test Scheduler (Manual Trigger)

```bash
cd backend
python test_scheduler_manually.py
```

This manually triggers all reminder jobs without waiting for scheduled times.

### 3. Check Notifications in Database

```bash
cd backend
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT * FROM chat_messages WHERE sender=\"system\" ORDER BY created_at DESC LIMIT 5'); print([dict(row) for row in cursor.fetchall()])"
```

Or use a simpler script:

```bash
python check_notifications.py
```

---

## Testing in UI (Frontend)

### Step 1: Start the Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Application startup complete.
✅ Scheduler started successfully
📋 Scheduled jobs: 4
  - water_reminder: 2026-03-06T14:00:00
  - mood_reminder: 2026-03-07T10:00:00
  - exercise_reminder: 2026-03-06T18:00:00
  - evening_challenges: 2026-03-06T20:00:00
```

### Step 2: Login to UI

1. Open browser: `http://localhost:8000`
2. Login with:
   - Username: `Ankur`
   - Password: `123456`

### Step 3: Test Activity Queries

In the chat, type these queries:

**Query 1: Daily Summary**
```
What did I do today?
```

**Expected Response:**
```
📊 Here's your activity summary for today:

💧 Water: 2/8 glasses
😴 Sleep: 0/8 hours
🏃 Exercise: 0/30 minutes

✨ Total activities logged: 1

Good start! Keep it up! 💪
```

**Query 2: Specific Activity**
```
How much water did I drink?
```

**Expected Response:**
```
You're making progress on water! 📈

Today: 2/8 glasses (25%)
Remaining: 6 glasses

You've got this! 🔥
```

**Query 3: Progress Check**
```
What's my progress?
```

**Expected Response:**
```
📊 Your Challenge Progress:

📈 In Progress:
  • 7-Day Hydration Challenge: 2/8 glasses (25%)
  • Daily Exercise: 0/30 minutes (0%)

🚀 Let's make some progress today!
```

### Step 4: Trigger Reminder Manually

While logged in, run in another terminal:

```bash
cd backend
python test_scheduler_manually.py
```

Then **refresh your chat** or send any message. You should see system notifications appear like:

```
💡 Hydration Reminder

You've only had 2/8 glasses today. Don't forget to drink water! 💧

[Log Water]
```

---

## How Reminders Appear in Chat

### Current Implementation (Phase 1)

Reminders are stored as **system messages** in the `chat_messages` table with:
- `sender = 'system'`
- `message_type = 'reminder'`

When you open the chat or refresh, these messages will appear in your chat history.

### Visual Example

```
┌─────────────────────────────────────────┐
│  Chat with MoodBot                      │
├─────────────────────────────────────────┤
│                                         │
│  You: I drank 2 glasses                │
│                                         │
│  Bot: Great! Logged 2 glasses 💧       │
│                                         │
│  [System Notification appears here]    │
│  ┌───────────────────────────────────┐ │
│  │ 💡 Hydration Reminder             │ │
│  │                                   │ │
│  │ You've only had 2/8 glasses      │ │
│  │ today. Don't forget to drink     │ │
│  │ water! 💧                        │ │
│  │                                   │ │
│  │ [Log Water]                      │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

---

## Testing Scenarios

### Scenario 1: Water Reminder

**Setup:**
1. Log 2 glasses of water (25% of 8 glass goal)
2. Wait until 2 PM OR run manual trigger

**Expected:**
- Reminder sent: "You've only had 2/8 glasses today!"
- Appears in chat as system message

**Test:**
```bash
# Log water first
# Then trigger reminder
python test_scheduler_manually.py

# Check if notification was created
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT COUNT(*) as count FROM chat_messages WHERE sender=\"system\" AND message_type=\"reminder\"'); print(f'System reminders: {cursor.fetchone()[\"count\"]}')"
```

### Scenario 2: No Reminder (Already Met Goal)

**Setup:**
1. Log 8 glasses of water (100% of goal)
2. Trigger reminder

**Expected:**
- NO reminder sent (already completed)

**Test:**
```bash
python test_scheduler_manually.py
# Should see: "Water reminder job complete: 0/1 sent"
```

### Scenario 3: Multiple Challenges

**Setup:**
1. Have multiple active challenges
2. Complete some, leave others incomplete
3. Trigger evening reminder (8 PM)

**Expected:**
- Reminder lists all incomplete challenges

---

## Checking Scheduler Status

### Method 1: Check Logs

```bash
# Start server and watch logs
python -m uvicorn app.main:app --reload

# Look for:
# ✅ Scheduler started successfully
# 📋 Scheduled jobs: 4
```

### Method 2: API Endpoint (Optional - Not implemented yet)

You can add this endpoint to check scheduler status:

```python
# In app/api/v1/endpoints/system.py

@router.get("/scheduler/status")
async def get_scheduler_status():
    from app.scheduler import get_scheduler_status
    return get_scheduler_status()
```

### Method 3: Database Check

```bash
# Check if notifications are being created
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT COUNT(*) as count FROM notifications'); print(f'Total notifications: {cursor.fetchone()[\"count\"]}')"
```

---

## Troubleshooting

### Issue: Scheduler Not Starting

**Symptoms:**
- No log message "✅ Scheduler started"
- No scheduled jobs listed

**Fix:**
```bash
# Check if APScheduler is installed
pip list | grep -i apscheduler

# Reinstall if needed
pip install apscheduler==3.10.4

# Check for errors in startup
python -m uvicorn app.main:app --reload 2>&1 | grep -i error
```

### Issue: Reminders Not Appearing in Chat

**Symptoms:**
- Scheduler runs but no messages in chat
- Notifications table is empty

**Debug:**
```bash
# 1. Check if notifications are being created
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT * FROM notifications ORDER BY created_at DESC LIMIT 1'); print(dict(cursor.fetchone()) if cursor.fetchone() else 'No notifications')"

# 2. Check if chat_messages are being created
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT * FROM chat_messages WHERE sender=\"system\" ORDER BY created_at DESC LIMIT 1'); print(dict(cursor.fetchone()) if cursor.fetchone() else 'No system messages')"

# 3. Check user_id
# Make sure you're using the correct user_id (1 for Ankur)
```

### Issue: Activity Queries Not Working

**Symptoms:**
- Query returns generic response
- No activity data shown

**Debug:**
```bash
# Test the workflow directly
python test_activity_queries.py

# Check if intent is detected correctly
python -c "import sys; sys.path.insert(0, '.'); from chat_assistant.domain.llm.intent_extractor import get_intent_extractor; extractor = get_intent_extractor(); result = extractor.extract_intent('What did I do today?'); print(f'Intent: {result[\"primary_intent\"]}')"
```

### Issue: Wrong User Data

**Symptoms:**
- Shows data for wrong user
- No data when there should be

**Fix:**
```bash
# Check user_id in database
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT id, username FROM users'); print([dict(row) for row in cursor.fetchall()])"

# Ankur should be user_id = 1
```

---

## Expected Behavior Summary

### Reminders (Proactive)

| Time | Reminder | Condition | Message |
|------|----------|-----------|---------|
| 2 PM | Water | < 50% complete | "You've only had X/8 glasses..." |
| 10 AM | Mood | Not logged | "How are you feeling today?" |
| 6 PM | Exercise | Not completed | "You haven't logged any exercise..." |
| 8 PM | Challenges | Any incomplete | "You have X challenges pending..." |

### Queries (Reactive)

| Query | Response |
|-------|----------|
| "What did I do today?" | Full daily summary |
| "How much water did I drink?" | Water progress with target |
| "Did I exercise?" | Yes/No with details |
| "What's my progress?" | All challenge progress |

---

## Next Steps

### Phase 2: Real-time Notifications

Currently, reminders appear as chat history. To make them appear in real-time:

1. Implement WebSocket (see `IN_CHAT_NOTIFICATION_SYSTEM.md`)
2. Send notifications via WebSocket when user is online
3. Show as popup/banner in UI

### Phase 3: User Preferences

Allow users to:
- Enable/disable specific reminders
- Customize reminder times
- Set notification preferences

---

## Quick Reference Commands

```bash
# Test activity queries
python test_activity_queries.py

# Trigger reminders manually
python test_scheduler_manually.py

# Check notifications
python -c "import sys; sys.path.insert(0, '.'); from app.core.database import get_db; with get_db() as db: cursor = db.cursor(); cursor.execute('SELECT * FROM chat_messages WHERE sender=\"system\" ORDER BY created_at DESC LIMIT 5'); [print(dict(row)) for row in cursor.fetchall()]"

# Start server with scheduler
python -m uvicorn app.main:app --reload

# Check scheduler status in logs
python -m uvicorn app.main:app --reload 2>&1 | grep -i scheduler
```
