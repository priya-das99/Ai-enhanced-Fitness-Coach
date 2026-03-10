# Quick Test Guide - See Reminders in UI

## For User: Ankur (Password: 123456)

### Step 1: Start the Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Look for this in the output:**
```
✅ Scheduler started successfully
📋 Scheduled jobs: 4
```

### Step 2: Trigger a Reminder Manually

Open a **NEW terminal** (keep server running) and run:

```bash
cd backend
python test_scheduler_manually.py
```

**You should see:**
```
1. Testing Water Reminder Job...
  ✓ Sent water reminder to user 1
✅ Water reminder job complete: 1/1 sent
```

### Step 3: Check if Notification Was Created

```bash
python check_notifications.py
```

**You should see:**
```
System Messages in Chat:
Total system messages: 1

Last 5 system messages:
  - [reminder] Hydration Reminder You've only had 2/8 glasses today...
```

### Step 4: See it in the UI

1. Open browser: `http://localhost:8000`
2. Login:
   - Username: `Ankur`
   - Password: `123456`
3. Open the chat
4. **You should see the system notification in your chat history!**

---

## Test Activity Queries

While in the chat, type:

### Query 1:
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
```

### Query 2:
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

### Query 3:
```
What's my progress?
```

**Expected Response:**
```
📊 Your Challenge Progress:

📈 In Progress:
  • 7-Day Hydration Challenge: 2/8 glasses (25%)

🚀 Let's make some progress today!
```

---

## How Reminders Work

### Current Setup (Phase 1):

1. **Scheduler runs** at scheduled times (2 PM, 10 AM, 6 PM, 8 PM)
2. **Checks each user** to see if they need a reminder
3. **Sends notification** by storing it in `chat_messages` table as a system message
4. **Appears in chat** when you open/refresh the chat

### Visual Flow:

```
2:00 PM → Scheduler wakes up
  ↓
Check Ankur's water progress: 2/8 glasses (25%)
  ↓
Condition met: < 50% complete
  ↓
Create system message in database:
  "💡 Hydration Reminder
   You've only had 2/8 glasses today!"
  ↓
Message appears in Ankur's chat history
```

---

## Troubleshooting

### Problem: No notification appears

**Solution 1: Check if it was created**
```bash
python check_notifications.py
```

**Solution 2: Trigger manually**
```bash
python test_scheduler_manually.py
```

**Solution 3: Check user_id**
Make sure you're logged in as Ankur (user_id = 1)

### Problem: Scheduler not starting

**Check logs when starting server:**
```bash
python -m uvicorn app.main:app --reload 2>&1 | grep -i scheduler
```

Should see:
```
✅ Scheduler started successfully
```

### Problem: Activity queries not working

**Test directly:**
```bash
python test_activity_queries.py
```

---

## Summary

✅ **Scheduler**: Runs automatically, sends reminders at scheduled times
✅ **Activity Queries**: Answer "What did I do?", "How much water?", etc.
✅ **Notifications**: Appear as system messages in chat
✅ **Testing**: Use `test_scheduler_manually.py` to trigger reminders immediately

**Next**: Implement WebSocket for real-time notifications (see `IN_CHAT_NOTIFICATION_SYSTEM.md`)
