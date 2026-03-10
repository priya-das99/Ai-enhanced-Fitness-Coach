# 🚀 Notification Scheduler System Implementation

## Overview

This document explains the complete implementation of the intelligent notification scheduler system for the FitWell wellness platform. The system provides personalized, data-driven notifications with beautiful UI animations and smart conditional logic.

## 🏗️ Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ Polling System  │  │ Beautiful UI    │                 │
│  │ (30s intervals) │  │ (CSS + JS)      │                 │
│  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ APScheduler     │  │ Notification    │                 │
│  │ (Cron Jobs)     │  │ Service         │                 │
│  └─────────────────┘  └─────────────────┘                 │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ Context Service │  │ Database        │                 │
│  │ (Smart Logic)   │  │ Integration     │                 │
│  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## 📚 Core Components

### 1. APScheduler Core (`backend/app/scheduler.py`)

**Purpose**: Time-based job scheduling engine

**Technology**: APScheduler AsyncIOScheduler

**Key Features**:
- Cron-based scheduling with precise time control
- Async execution for performance
- Multiple notification types support

```python
@scheduler.scheduled_job('cron', hour=14, minute=30, id='water_reminder')
async def water_reminder_job():
    """2:30 PM Daily: Send water reminders to users who need them"""
    logger.info("🕐 Running water reminder job")
    
    context_service = get_context_service()
    notification_service = get_notification_service()
    
    active_users = context_service.get_active_users()
    sent_count = 0
    
    for user_id in active_users:
        try:
            result = context_service.should_send_reminder(user_id, 'water_reminder')
            
            if result['should_send']:
                progress = result['data']
                message = _generate_water_reminder_message(progress)
                
                notification_service.send_notification(user_id, {
                    'title': '💧 Hydration Reminder',
                    'message': message,
                    'type': 'reminder',
                    'action_buttons': [
                        {'id': 'log_water', 'label': '💧 Log Water'}
                    ],
                    'priority': 'normal'
                })
                
                sent_count += 1
                logger.info(f"  ✓ Sent water reminder to user {user_id}")
        
        except Exception as e:
            logger.error(f"  ✗ Failed to send water reminder to user {user_id}: {e}")
    
    logger.info(f"✅ Water reminder job complete: {sent_count}/{len(active_users)} sent")
```

### 2. Context Service (`backend/app/services/user_context_service.py`)

**Purpose**: Smart decision making and data retrieval

**Technology**: Custom Python service with database integration

**Key Features**:
- Determines WHO needs notifications and WHEN
- Retrieves real user progress data
- Implements anti-spam logic

```python
def should_send_reminder(self, user_id: int, reminder_type: str) -> Dict:
    """
    Determine if reminder should be sent based on user progress and time
    """
    current_hour = datetime.now().hour
    
    if reminder_type == 'water_reminder':
        progress = self.get_challenge_progress_today(user_id, 'water')
        if not progress:
            return {'should_send': False, 'reason': 'No active water challenge'}
        
        # Send if: less than 50% complete AND after 12:05 PM
        if progress['percentage'] < 50 and current_hour >= 12:
            return {
                'should_send': True,
                'reason': 'Low progress, afternoon',
                'data': progress
            }
        
        return {'should_send': False, 'reason': 'Progress OK or too early'}

def get_challenge_progress_today(self, user_id: int, challenge_type: str) -> Optional[Dict]:
    """
    Get today's progress for specific challenge type with real database data
    """
    with get_db() as db:
        cursor = db.cursor()
        
        # Get active challenge using correct table structure
        cursor.execute('''
            SELECT c.id, c.title, c.challenge_type, c.target_value, c.target_unit, uc.progress
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.user_id = ? AND c.challenge_type = ? AND uc.status = 'active'
            LIMIT 1
        ''', (user_id, challenge_type))
        
        challenge = cursor.fetchone()
        if not challenge:
            return None
        
        # Use the progress from user_challenges table
        current_value = challenge['progress'] if challenge['progress'] else 0.0
        target_value = challenge['target_value']
        
        return {
            'challenge_id': challenge['id'],
            'challenge_title': challenge['title'],
            'challenge_type': challenge['challenge_type'],
            'current': current_value,
            'target': target_value,
            'unit': challenge['target_unit'],
            'remaining': max(0, target_value - current_value),
            'percentage': (current_value / target_value * 100) if target_value > 0 else 0,
            'completed': current_value >= target_value
        }
```

### 3. Notification Service (`backend/app/services/notification_service.py`)

**Purpose**: Message creation and storage

**Technology**: Database integration with dual storage

**Key Features**:
- Stores notifications in dedicated table
- Creates chat messages for frontend polling
- Supports action buttons and priorities

```python
def send_notification(self, user_id: int, notification: Dict):
    """
    Send notification to user with dual storage approach
    """
    try:
        # Store in notifications table
        self._store_notification(user_id, notification)
        
        # Store as chat message (so it appears in chat history)
        self._store_as_chat_message(user_id, notification)
        
        logger.info(f"Notification sent to user {user_id}: {notification['type']}")
        
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")

def _store_as_chat_message(self, user_id: int, notification: Dict):
    """Store notification as system message in chat for frontend polling"""
    with get_db() as db:
        cursor = db.cursor()
        
        # Format message with title if present
        full_message = notification['message']
        if notification.get('title'):
            full_message = f"💡 {notification['title']}\n\n{notification['message']}"
        
        # Insert into chat_messages (using actual schema)
        cursor.execute('''
            INSERT INTO chat_messages 
            (user_id, sender, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            'system',
            full_message,
            datetime.now()
        ))
```

### 4. Frontend Polling System (`frontend/system_notifications.js`)

**Purpose**: Real-time notification display

**Technology**: JavaScript polling + CSS animations

**Key Features**:
- Polls API every 30 seconds
- Tracks shown notifications to prevent duplicates
- Beautiful animations and interactions

```javascript
const NOTIFICATION_CHECK_INTERVAL = 30000; // Check every 30 seconds
let shownNotificationIds = new Set(); // Track which notifications we've already shown

// Start checking for notifications
function startNotificationPolling() {
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
    }
    
    // Check immediately
    checkForNewNotifications();
    
    // Then check every 30 seconds
    notificationCheckInterval = setInterval(() => {
        checkForNewNotifications();
    }, NOTIFICATION_CHECK_INTERVAL);
    
    console.log('✅ Notification polling started (checking every 30 seconds)');
}

// Check for new system notifications
async function checkForNewNotifications() {
    if (!currentUser) return;
    
    try {
        let response = await fetch(`${API_BASE_URL}/chat/messages`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            console.error('Failed to fetch notifications:', response.status);
            return;
        }
        
        const data = await response.json();
        
        // Handle response format - filter for system messages
        let notifications = [];
        
        if (data.messages) {
            notifications = data.messages
                .filter(msg => msg.sender === 'system')
                .filter(msg => {
                    // Only show recent notifications (last 5 minutes)
                    const msgTime = new Date(msg.timestamp);
                    const now = new Date();
                    const diffMinutes = (now - msgTime) / (1000 * 60);
                    return diffMinutes <= 5;
                })
                .filter(msg => !shownNotificationIds.has(msg.id)) // Only show new ones
                .map(msg => ({
                    id: msg.id,
                    title: extractNotificationTitle(msg.message),
                    message: msg.message,
                    timestamp: msg.timestamp,
                    action_buttons: generateActionButtons(msg.message)
                }));
        }
        
        if (notifications.length > 0) {
            console.log(`📬 Found ${notifications.length} new notification(s)`);
            
            // Display each notification and mark as shown
            notifications.forEach(notification => {
                displaySystemNotification(notification);
                shownNotificationIds.add(notification.id); // Mark as shown
            });
        }
        
    } catch (error) {
        console.error('Error checking for notifications:', error);
    }
}
```

### 5. Beautiful UI System (`frontend/system_notifications.css`)

**Purpose**: Premium visual experience

**Technology**: CSS3 animations and gradients

**Key Features**:
- Type-specific gradient backgrounds
- Animated shimmer effects
- Pulse animations
- Interactive buttons

```css
/* System Notification Styles - Beautiful Design */
.system-notification {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    animation: slideInFromTop 0.5s ease-out;
    position: relative;
    overflow: hidden;
    max-width: 90%;
}

.system-notification::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #ffd700, #ff6b6b, #4ecdc4, #45b7d1);
    animation: shimmer 2s infinite;
}

/* Different notification types */
.notification-water .system-notification-bubble {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.notification-exercise .system-notification-bubble {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.notification-mood .system-notification-bubble {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

/* Animations */
@keyframes slideInFromTop {
    from {
        transform: translateY(-20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes shimmer {
    0% { 
        transform: translateX(-100%); 
        opacity: 0.6;
    }
    50% {
        opacity: 1;
    }
    100% { 
        transform: translateX(100%); 
        opacity: 0.6;
    }
}

.pulse {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { 
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transform: scale(1);
    }
    50% { 
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        transform: scale(1.02);
    }
    100% { 
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transform: scale(1);
    }
}
```

## 📅 Scheduled Jobs

### Current Schedule

| Job | Time | Frequency | Purpose | Condition |
|-----|------|-----------|---------|-----------|
| 💧 Water Reminder | 14:30 (2:30 PM) | Daily | Hydration reminders | < 50% water goal |
| 😊 Mood Check-in | 10:00 (10:00 AM) | Daily | Morning mood tracking | No mood logged |
| 🏃 Exercise Reminder | 18:00 (6:00 PM) | Daily | Evening workout motivation | Exercise goal incomplete |
| ⏰ Evening Challenge Check | 20:00 (8:00 PM) | Daily | Final challenge reminder | Incomplete challenges |

### Message Generation

```python
def _generate_water_reminder_message(progress: dict) -> str:
    """Generate personalized water reminder message"""
    current = progress['current']
    target = progress['target']
    remaining = progress['remaining']
    percentage = progress['percentage']
    challenge_title = progress.get('challenge_title', 'water challenge')
    
    if current == 0:
        return f"You haven't started your {challenge_title} yet! You need {target} glasses total. Let's get hydrated! 💧"
    elif percentage < 25:
        return f"You've logged {current}/{target} glasses for your {challenge_title}. You need {remaining} more glasses to reach your goal! 💧"
    elif percentage < 50:
        return f"Great progress! {current}/{target} glasses logged. Just {remaining} more glasses to complete your {challenge_title}! 💧"
    elif percentage < 75:
        return f"You're doing amazing! {current}/{target} glasses done. Only {remaining} more glasses to finish your {challenge_title}! 💧"
    else:
        return f"Almost there! Just {remaining} more glasses to complete your {challenge_title} of {target} glasses! You've got this! 💧"
```

## 🎯 Key Implementation Features

### ✅ Smart Conditional Logic
- Only sends notifications when users actually need them
- Prevents notification spam with intelligent conditions
- Time-based logic (e.g., only after 12 PM for water reminders)

### ✅ Real Database Integration
- Pulls actual user progress from `user_challenges` table
- Joins with `challenges` table for complete context
- Uses real numbers, not hardcoded test values

### ✅ Personalized Messages
- Dynamic content based on user's actual progress
- Includes challenge names and specific numbers
- Progress-based messaging (0%, 25%, 50%, 75%+ completion)

### ✅ Beautiful User Interface
- Type-specific gradient backgrounds (blue for water, green for exercise, pink for mood)
- Animated rainbow shimmer effects on top borders
- Pulse animations for new notifications
- Interactive action buttons with hover effects

### ✅ Anti-Duplicate System
- Tracks shown notification IDs to prevent repeats
- Only displays notifications from last 5 minutes
- Prevents notification overload

### ✅ Performance Optimized
- Async scheduling for non-blocking execution
- Efficient database queries with proper joins
- 30-second polling interval balances real-time feel with performance

## 🔄 Complete Flow

1. **APScheduler** triggers at scheduled time (e.g., 2:30 PM for water reminders)
2. **Context Service** checks which users need reminders based on progress
3. **Database queries** retrieve real user challenge data
4. **Smart logic** determines if notification should be sent (< 50% progress)
5. **Message generator** creates personalized content with actual numbers
6. **Notification Service** stores notification in database as system message
7. **Frontend polling** detects new notifications every 30 seconds
8. **Beautiful UI** displays notification with animations and action buttons
9. **User interaction** through action buttons triggers appropriate workflows

## 🚀 Benefits

### For Users
- **Relevant notifications** - Only get reminders when actually needed
- **Beautiful experience** - Premium UI with smooth animations
- **Actionable** - Interactive buttons for immediate action
- **Personal** - Messages include their actual progress and challenge names

### For Developers
- **Scalable** - Can handle many users and notification types
- **Maintainable** - Clean separation of concerns across layers
- **Extensible** - Easy to add new notification types
- **Reliable** - Robust error handling and fallback mechanisms

### For Business
- **Increased engagement** - Smart, relevant notifications drive user action
- **Better retention** - Helpful reminders keep users on track with goals
- **Premium feel** - Beautiful UI creates positive brand impression
- **Data-driven** - Real user progress creates meaningful interactions

## 🔧 Configuration

### Adding New Notification Types

1. **Add scheduler job** in `scheduler.py`:
```python
@scheduler.scheduled_job('cron', hour=15, minute=0, id='new_reminder')
async def new_reminder_job():
    # Implementation
```

2. **Add logic** in `user_context_service.py`:
```python
elif reminder_type == 'new_reminder':
    # Check conditions and return data
```

3. **Add message generator** in `scheduler.py`:
```python
def _generate_new_reminder_message(progress: dict) -> str:
    # Generate personalized message
```

4. **Add UI styling** in `system_notifications.css`:
```css
.notification-new {
    background: linear-gradient(135deg, #color1 0%, #color2 100%);
}
```

### Customizing Schedule Times

Edit the cron parameters in `scheduler.py`:
```python
@scheduler.scheduled_job('cron', hour=11, minute=0, id='water_reminder')  # 11:00 AM
@scheduler.scheduled_job('cron', hour=15, minute=30, id='water_reminder') # 3:30 PM
```

## 📊 Monitoring and Testing

### Demo System
Run the demo script to test all notification types:
```bash
python backend/demo_push_notifications.py
```

### Scheduler Status
Check current scheduler status:
```python
from app.scheduler import get_scheduler_status
status = get_scheduler_status()
```

### Manual Testing
Force notifications for specific users:
```python
from app.services.notification_service import get_notification_service
notification_service = get_notification_service()
notification_service.send_notification(user_id, notification_data)
```

## 🎉 Conclusion

This notification scheduler system provides a **professional, intelligent, and beautiful** user experience that drives engagement through relevant, data-driven notifications. The implementation balances performance, scalability, and user experience to create a premium wellness platform feature.

The system successfully combines:
- **Backend intelligence** (APScheduler + smart logic)
- **Real data integration** (database-driven personalization)  
- **Frontend beauty** (CSS animations + smooth interactions)
- **User value** (relevant, actionable notifications)

This creates a notification system that users actually appreciate rather than find annoying! 🚀