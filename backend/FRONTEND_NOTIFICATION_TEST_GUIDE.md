# 🎯 Frontend Notification Testing Guide

## How to Test Scheduler Notifications in Your Real Frontend

### 📋 **Setup Steps**

1. **Start your backend server** (with scheduler enabled)
   ```bash
   cd backend
   python app.py  # or however you start your server
   ```

2. **Verify scheduler is running at 13:21**
   - The scheduler is now set to trigger at **13:21 (1:21 PM)**
   - Check `backend/app/scheduler.py` - line shows `hour=13, minute=21`

3. **Open your frontend**
   - Go to `http://localhost:8000`
   - Login as **Ankur** (Username: `Ankur`, Password: `123456`)

### 🧪 **Testing Options**

#### **Option A: Wait for Automatic Trigger (13:21)**
- Simply wait until 1:21 PM
- The scheduler will automatically check Ankur's water progress
- If progress < 50%, it will create a notification
- Notification appears in chat within 30 seconds

#### **Option B: Force Create Notification (Immediate)**
```bash
cd backend
python force_notification_for_frontend_test.py
```
- Creates a notification immediately
- Appears in frontend within 30 seconds
- No need to wait for 13:21

#### **Option C: Change Scheduler Time (Quick Test)**
1. Edit `backend/app/scheduler.py`
2. Change line: `hour=13, minute=21` to current time + 2 minutes
3. Restart backend server
4. Wait 2 minutes and see notification

### 🎨 **What You'll See in Frontend**

When notification appears, you'll see:

```
💧 Hydration Reminder                    13:21
Hey Ankur! You're at 25% of your water goal 
(2.0/8.0 glasses). You need 6.0 more glasses 
to reach your daily goal! 💧

[💧 Log Water] [⏰ Remind Later] [📊 View Progress]
```

### 🔧 **How It Works**

1. **Scheduler runs** at 13:21 and checks water progress
2. **NotificationService** creates system message in database
3. **Frontend polls** every 30 seconds for new system messages
4. **system_notifications.js** detects new notification
5. **Notification displays** in chat with action buttons
6. **User clicks buttons** → triggers chat messages

### 🐛 **Troubleshooting**

#### **Notification doesn't appear:**
1. Check browser console for errors
2. Verify you're logged in as Ankur
3. Check if notification was created:
   ```bash
   python show_scheduler_notifications.py
   ```

#### **Scheduler not running:**
1. Check server logs for scheduler startup
2. Verify `start_scheduler()` is called in your app
3. Check for any scheduler errors in logs

#### **Wrong time:**
1. Verify server time matches your local time
2. Check timezone settings
3. Use Option B (force create) for immediate testing

### 📱 **Action Button Testing**

When you click notification buttons:

- **💧 Log Water** → Sends "I want to log water" to chat
- **⏰ Remind Later** → Sends "Remind me later" to chat  
- **📊 View Progress** → Sends "Show my progress" to chat

These messages trigger your existing chat workflows!

### 🔄 **Continuous Testing**

For ongoing testing:
1. Use `force_notification_for_frontend_test.py` to create notifications
2. Test different scenarios (different water levels)
3. Verify action buttons work correctly
4. Check notification styling matches your UI

### 📊 **Monitoring**

Check notification system status:
```bash
# See recent notifications
python show_scheduler_notifications.py

# Check scheduler status  
python test_scheduler_13_21.py

# Force create for testing
python force_notification_for_frontend_test.py
```

---

## 🎯 **Quick Test (Recommended)**

1. **Start backend server**
2. **Open frontend and login as Ankur**
3. **Run:** `python force_notification_for_frontend_test.py`
4. **Wait 30 seconds** and see notification appear in chat
5. **Click action buttons** to test interaction

This gives you immediate feedback without waiting for 13:21!