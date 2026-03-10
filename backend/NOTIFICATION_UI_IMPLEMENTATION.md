# System Notifications in UI - Implementation Guide

## Current Status

✅ **Scheduler works** - Creates notifications at 12:05 PM
✅ **Notifications stored** - In database (chat_messages table)
❌ **UI doesn't show them** - Needs frontend integration

## Problem

The UI only loads chat history on page load. When scheduler creates new notifications, the UI doesn't know about them.

## Solution: Polling System

### Step 1: Change Scheduler Time (DONE)

File: `backend/app/scheduler.py`
- Changed from 2 PM → **12:05 PM** for testing
- Changed time check from hour >= 14 → **hour >= 12**

### Step 2: Add Frontend Files

**Created:**
1. `frontend/system_notifications.js` - Polls for new notifications every 30 seconds
2. `frontend/system_notifications.css` - Styles for notification bubbles

### Step 3: Add Backend API Endpoint

Create: `backend/app/api/v1/endpoints/chat.py` (add this endpoint)

```python
@router.get("/system-notifications")
async def get_system_notifications(
    current_user: dict = Depends(get_current_user)
):
    """
    Get unread system notifications for current user
    """
    user_id = current_user['id']
    
    # Get system messages created in last 5 minutes that user hasn't seen
    with get_db() as db:
        cursor = db.cursor()
        
        # Get recent system messages
        cursor.execute('''
            SELECT message, timestamp
            FROM chat_messages
            WHERE user_id = ?
            AND sender = 'system'
            AND timestamp >= datetime('now', '-5 minutes')
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        messages = cursor.fetchall()
        
        notifications = []
        for row in messages:
            # Parse message (format: "💡 Title\n\nMessage")
            message_text = row['message']
            parts = message_text.split('\n\n', 1)
            
            if len(parts) == 2:
                title = parts[0].replace('💡 ', '').strip()
                message = parts[1].strip()
            else:
                title = ''
                message = message_text
            
            notifications.append({
                'title': title,
                'message': message,
                'timestamp': row['timestamp'],
                'type': 'reminder',
                'action_buttons': []  # TODO: Parse from metadata
            })
        
        return {
            'success': True,
            'notifications': notifications
        }
```

### Step 4: Update HTML

Add to `index.html` (in `<head>` section):

```html
<!-- System Notifications -->
<link rel="stylesheet" href="frontend/system_notifications.css">
<script src="frontend/system_notifications.js"></script>
```

Add badge to chatbot button (in `<body>`):

```html
<button id="chatbotButton" class="chatbot-button" onclick="toggleChat()">
    💬
    <span id="chatbotBadge" class="chatbot-badge"></span>
</button>
```

### Step 5: Update chat.js

Add to `initializeChat()` function:

```javascript
async function initializeChat() {
    // ... existing code ...
    
    // Start polling for system notifications
    if (typeof startNotificationPolling === 'function') {
        startNotificationPolling();
    }
}
```

Add to chat close handler:

```javascript
function toggleChat() {
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        chatContainer.classList.add('open');
        hideNewMessageBadge();  // Hide badge when opening chat
    } else {
        chatContainer.classList.remove('open');
        stopNotificationPolling();  // Stop polling when closing
    }
}
```

## Testing

### 1. Start Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Look for:**
```
✅ Scheduler started successfully
📋 Scheduled jobs: 4
  - water_reminder: 2026-03-06T12:05:00  ← Should be 12:05 PM
```

### 2. Wait for 12:05 PM

The scheduler will automatically run at 12:05 PM and send notifications to users who need them.

### 3. Check in UI

1. Login at `http://localhost:8000`
2. Username: `Ankur`, Password: `123456`
3. Open chat
4. **Within 30 seconds**, you should see a notification appear like:

```
┌─────────────────────────────────────┐
│ 💡  Hydration Reminder              │
│                                     │
│ You've only had 2/8 glasses today.  │
│ Don't forget to drink water! 💧     │
│                                     │
│ [💧 Log Water]                      │
└─────────────────────────────────────┘
```

### 4. Manual Test (Don't Wait)

If you don't want to wait until 12:05 PM:

```bash
cd backend
python force_water_reminder_for_ankur.py
```

Then refresh the chat in UI - notification should appear!

## How It Works

```
12:05 PM → Scheduler runs
  ↓
Checks Ankur's water: 2/8 glasses (25%)
  ↓
Condition met: < 50% AND after 12 PM
  ↓
Creates system message in database
  ↓
Frontend polls every 30 seconds
  ↓
Finds new system message
  ↓
Displays as notification bubble in chat
  ↓
Shows badge on chatbot button if chat closed
```

## Visual Design

### Notification Bubble

- **Background**: Purple gradient (matches brand)
- **Icon**: 💡 on the left
- **Title**: Bold, white text
- **Message**: Regular white text
- **Buttons**: Semi-transparent white buttons
- **Animation**: Slides in from top

### Badge

- **Position**: Top-right of chatbot button
- **Color**: Red (#ff4444)
- **Animation**: Pulses to attract attention
- **Behavior**: Disappears when chat is opened

## Next Steps (Phase 2)

For real-time notifications without polling:

1. **WebSocket Integration**
   - Instant delivery (no 30-second delay)
   - Two-way communication
   - See: `IN_CHAT_NOTIFICATION_SYSTEM.md`

2. **Push Notifications**
   - Work even when browser is closed
   - Requires service worker
   - Platform-specific (Firebase, OneSignal)

## Troubleshooting

### Notifications not appearing

**Check:**
1. Scheduler is running: Look for "✅ Scheduler started" in logs
2. Time is correct: Should be 12:05 PM in scheduler.py
3. Notifications created: Run `python show_scheduler_notifications.py`
4. Frontend polling: Check browser console for "✅ Notification polling started"

### Wrong time

**Fix:**
- Edit `backend/app/scheduler.py` line 18: `hour=12, minute=5`
- Edit `backend/app/services/user_context_service.py` line 145: `current_hour >= 12`
- Restart server

### UI not updating

**Fix:**
- Make sure `system_notifications.js` is loaded
- Check browser console for errors
- Try manual refresh (F5)
