# Context-Aware System Architecture
## Solving User-Data-Dependent Responses & Proactive Notifications

## The Core Problem

You've identified a fundamental limitation: **The system needs user data to provide personalized, context-aware responses and proactive notifications.**

### Examples of User-Data-Dependent Features:

1. **Activity Summaries**
   - "What did I do today?" → Needs: user's logged activities
   - "How much water did I drink?" → Needs: today's water logs

2. **Proactive Notifications**
   - "You've only drunk 1/8 glasses today" → Needs: challenge target + today's progress
   - "You haven't logged your mood today" → Needs: mood logging history
   - "Great job! 5-day streak!" → Needs: activity streak data

3. **Personalized Recommendations**
   - "Based on your stress pattern..." → Needs: mood history analysis
   - "You usually exercise at 6 PM" → Needs: activity timing patterns
   - "This activity helped you before" → Needs: past activity ratings

4. **Progress Tracking**
   - "You're 75% through your challenge" → Needs: challenge progress
   - "Your sleep improved 20% this week" → Needs: weekly comparison
   - "You're more active than last month" → Needs: historical comparison

## Current System Limitations

### What Works (Reactive, User-Initiated):
```
User: "Did I meet my water goal?"
  ↓
Intent Detection → challenges
  ↓
ChallengesWorkflow → Query DB → Calculate → Respond
  ↓
"You drank 2/8 glasses. Need 6 more!"
```

### What Doesn't Work (Proactive, System-Initiated):
```
System at 6 PM: Should remind user about water?
  ❌ No scheduler
  ❌ No notification system
  ❌ No proactive message generation
```

## Architectural Solution: Context Service Layer

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  (Chat Interface, Push Notifications, In-App Messages)       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   WORKFLOW LAYER                             │
│  (MoodWorkflow, ChallengesWorkflow, ActivitySummaryWorkflow) │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              CONTEXT SERVICE LAYER ⭐ NEW                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  UserContextService                                   │   │
│  │  - get_daily_summary(user_id)                        │   │
│  │  - get_challenge_progress(user_id, challenge_type)   │   │
│  │  - get_activity_streak(user_id, activity_type)       │   │
│  │  - get_mood_patterns(user_id, days=7)                │   │
│  │  - should_send_reminder(user_id, reminder_type)      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 REPOSITORY LAYER                             │
│  (ChallengeRepo, HealthActivityRepo, MoodRepo)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│  (health_activities, challenges, moods, user_challenges)     │
└─────────────────────────────────────────────────────────────┘
```

### New Components Needed

#### 1. UserContextService (Core)
**Purpose**: Centralized service for retrieving user-specific data and context

```python
# backend/app/services/user_context_service.py

class UserContextService:
    """
    Centralized service for user context and personalized data.
    Used by workflows, notifications, and any feature needing user data.
    """
    
    def __init__(self):
        self.health_repo = HealthActivityRepository()
        self.challenge_repo = ChallengeRepository()
        self.mood_repo = MoodRepository()
    
    # ===== ACTIVITY SUMMARIES =====
    
    def get_daily_summary(self, user_id: int, date: str = None) -> Dict:
        """
        Get complete daily summary for user.
        Used by: Activity summary queries, daily reports
        """
        return {
            'water': self.health_repo.get_daily_total(user_id, 'water', date),
            'sleep': self.health_repo.get_daily_total(user_id, 'sleep', date),
            'exercise': self.health_repo.get_daily_total(user_id, 'exercise', date),
            'mood': self.mood_repo.get_daily_mood(user_id, date),
            'activities_completed': self.health_repo.count_activities(user_id, date)
        }
    
    def get_activity_history(self, user_id: int, activity_type: str, days: int = 7) -> List[Dict]:
        """
        Get activity history for specific type.
        Used by: Trend analysis, progress tracking
        """
        return self.health_repo.get_activity_history(user_id, activity_type, days)
    
    # ===== CHALLENGE CONTEXT =====
    
    def get_challenge_progress_today(self, user_id: int, challenge_type: str) -> Dict:
        """
        Get today's progress for specific challenge.
        Used by: Reminders, progress checks
        """
        challenge = self.challenge_repo.get_active_challenge(user_id, challenge_type)
        if not challenge:
            return None
        
        today_value = self.health_repo.get_daily_total(user_id, challenge_type)
        target_value = challenge['target_value']
        
        return {
            'challenge_id': challenge['id'],
            'challenge_title': challenge['title'],
            'current': today_value,
            'target': target_value,
            'remaining': max(0, target_value - today_value),
            'percentage': (today_value / target_value * 100) if target_value > 0 else 0,
            'completed': today_value >= target_value
        }
    
    def get_all_challenges_progress(self, user_id: int) -> List[Dict]:
        """
        Get progress for all active challenges.
        Used by: Dashboard, daily summary
        """
        active_challenges = self.challenge_repo.get_user_active_challenges(user_id)
        return [
            self.get_challenge_progress_today(user_id, ch['challenge_type'])
            for ch in active_challenges
        ]
    
    # ===== REMINDER LOGIC =====
    
    def should_send_reminder(self, user_id: int, reminder_type: str) -> Dict:
        """
        Determine if reminder should be sent.
        Used by: Notification scheduler
        
        Returns: {
            'should_send': bool,
            'reason': str,
            'data': dict  # Context for message generation
        }
        """
        if reminder_type == 'water_reminder':
            progress = self.get_challenge_progress_today(user_id, 'water')
            if not progress:
                return {'should_send': False, 'reason': 'No active water challenge'}
            
            # Send reminder if:
            # 1. Less than 50% complete
            # 2. After 2 PM
            # 3. Haven't logged in last 2 hours
            current_hour = datetime.now().hour
            if progress['percentage'] < 50 and current_hour >= 14:
                last_log = self.health_repo.get_last_activity_time(user_id, 'water')
                if not last_log or (datetime.now() - last_log).seconds > 7200:
                    return {
                        'should_send': True,
                        'reason': 'Low progress, afternoon, no recent log',
                        'data': progress
                    }
            
            return {'should_send': False, 'reason': 'Conditions not met'}
        
        elif reminder_type == 'mood_reminder':
            # Check if mood logged today
            mood_today = self.mood_repo.get_daily_mood(user_id)
            if not mood_today and datetime.now().hour >= 10:
                return {
                    'should_send': True,
                    'reason': 'No mood logged, after 10 AM',
                    'data': {'last_mood': self.mood_repo.get_last_mood(user_id)}
                }
            
            return {'should_send': False, 'reason': 'Mood already logged'}
        
        elif reminder_type == 'challenge_completion':
            # Remind about incomplete challenges near end of day
            if datetime.now().hour >= 20:  # After 8 PM
                incomplete = [
                    ch for ch in self.get_all_challenges_progress(user_id)
                    if not ch['completed']
                ]
                if incomplete:
                    return {
                        'should_send': True,
                        'reason': 'Incomplete challenges, evening',
                        'data': {'incomplete_challenges': incomplete}
                    }
            
            return {'should_send': False, 'reason': 'All complete or too early'}
        
        return {'should_send': False, 'reason': 'Unknown reminder type'}
    
    # ===== PATTERN DETECTION =====
    
    def get_activity_streak(self, user_id: int, activity_type: str) -> Dict:
        """
        Calculate activity streak.
        Used by: Motivation messages, achievements
        """
        history = self.health_repo.get_activity_history(user_id, activity_type, days=30)
        
        current_streak = 0
        for day in history:
            if day['total'] > 0:
                current_streak += 1
            else:
                break
        
        return {
            'activity_type': activity_type,
            'current_streak': current_streak,
            'longest_streak': self._calculate_longest_streak(history)
        }
    
    def get_mood_patterns(self, user_id: int, days: int = 7) -> Dict:
        """
        Analyze mood patterns.
        Used by: Insights, recommendations
        """
        moods = self.mood_repo.get_mood_history(user_id, days)
        
        return {
            'average_mood': sum(m['value'] for m in moods) / len(moods) if moods else 0,
            'most_common_mood': self._get_most_common(moods, 'emoji'),
            'stress_days': len([m for m in moods if m['emoji'] in ['😰', '😟', '😫']]),
            'happy_days': len([m for m in moods if m['emoji'] in ['😊', '😄', '🥰']])
        }
```

#### 2. NotificationScheduler (Proactive System)
**Purpose**: Schedule and send proactive notifications

```python
# backend/app/services/notification_scheduler.py

class NotificationScheduler:
    """
    Handles scheduled notifications and proactive messages.
    Runs as background job (cron/celery).
    """
    
    def __init__(self):
        self.context_service = UserContextService()
        self.notification_service = NotificationService()
    
    def check_and_send_reminders(self):
        """
        Main scheduler function - runs every hour.
        Checks all users and sends appropriate reminders.
        """
        active_users = self._get_active_users()
        
        for user_id in active_users:
            # Check each reminder type
            self._check_water_reminder(user_id)
            self._check_mood_reminder(user_id)
            self._check_challenge_reminder(user_id)
            self._check_streak_celebration(user_id)
    
    def _check_water_reminder(self, user_id: int):
        """Send water reminder if needed"""
        result = self.context_service.should_send_reminder(user_id, 'water_reminder')
        
        if result['should_send']:
            progress = result['data']
            message = self._generate_water_reminder_message(progress)
            
            self.notification_service.send_push_notification(
                user_id=user_id,
                title="💧 Hydration Reminder",
                message=message,
                action_buttons=[
                    {'id': 'log_water', 'label': 'Log Water'}
                ]
            )
    
    def _generate_water_reminder_message(self, progress: Dict) -> str:
        """Generate personalized water reminder"""
        current = progress['current']
        target = progress['target']
        remaining = progress['remaining']
        
        if current == 0:
            return f"You haven't logged any water today! Your goal is {target} glasses. Stay hydrated! 💧"
        elif progress['percentage'] < 25:
            return f"You've only had {current}/{target} glasses today. Don't forget to drink water! 💧"
        elif progress['percentage'] < 50:
            return f"Halfway there! {current}/{target} glasses. Keep it up! 💧"
        else:
            return f"Almost done! Just {remaining} more glasses to reach your goal! 💧"
    
    def _check_streak_celebration(self, user_id: int):
        """Celebrate activity streaks"""
        water_streak = self.context_service.get_activity_streak(user_id, 'water')
        
        # Celebrate milestones: 3, 7, 14, 30 days
        if water_streak['current_streak'] in [3, 7, 14, 30]:
            message = f"🔥 Amazing! {water_streak['current_streak']}-day water streak! Keep it going!"
            
            self.notification_service.send_push_notification(
                user_id=user_id,
                title="🎉 Streak Milestone!",
                message=message
            )
```

#### 3. NotificationService (Delivery)
**Purpose**: Handle actual notification delivery

```python
# backend/app/services/notification_service.py

class NotificationService:
    """
    Handles notification delivery via multiple channels.
    """
    
    def send_push_notification(self, user_id: int, title: str, message: str, 
                               action_buttons: List[Dict] = None):
        """
        Send push notification to user's device.
        Integrates with: Firebase, OneSignal, or custom push service
        """
        # Store in database for in-app display
        self._store_notification(user_id, title, message, action_buttons)
        
        # Send via push service
        self._send_via_push_service(user_id, title, message, action_buttons)
    
    def send_in_app_message(self, user_id: int, message: str, 
                           message_type: str = 'reminder'):
        """
        Send in-app chat message (appears in chat interface).
        """
        from app.repositories.chat_repository import ChatRepository
        chat_repo = ChatRepository()
        
        chat_repo.save_message(
            user_id=user_id,
            sender='bot',
            message=message,
            message_type=message_type
        )
    
    def _store_notification(self, user_id: int, title: str, message: str, 
                           action_buttons: List[Dict]):
        """Store notification in database"""
        # Create notifications table if needed
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO notifications 
                (user_id, title, message, action_buttons, created_at, read)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, message, json.dumps(action_buttons), 
                  datetime.now(), False))
```

#### 4. Enhanced Workflows Using Context Service

```python
# backend/chat_assistant/activity_summary_workflow.py

class ActivitySummaryWorkflow(BaseWorkflow):
    """
    Handles activity summary queries using UserContextService.
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="activity_summary",
            handled_intents=['activity_summary', 'activity_history']
        )
        self.context_service = UserContextService()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle activity summary requests"""
        
        # Detect query type
        if self._is_daily_summary_request(message):
            summary = self.context_service.get_daily_summary(user_id)
            response = self._format_daily_summary(summary)
        
        elif self._is_specific_activity_request(message):
            activity_type = self._extract_activity_type(message)
            history = self.context_service.get_activity_history(user_id, activity_type)
            response = self._format_activity_history(activity_type, history)
        
        elif self._is_challenge_progress_request(message):
            progress = self.context_service.get_all_challenges_progress(user_id)
            response = self._format_challenge_progress(progress)
        
        return self._complete_workflow(message=response)
```

## Implementation Plan

### Phase 1: Core Context Service (Week 1)
1. Create `UserContextService` class
2. Implement basic data retrieval methods:
   - `get_daily_summary()`
   - `get_challenge_progress_today()`
   - `get_activity_history()`
3. Create repository layer if missing:
   - `HealthActivityRepository`
   - `MoodRepository` (enhance existing)
4. Add unit tests

### Phase 2: Activity Summary Workflow (Week 1-2)
1. Add `activity_summary` intent to `IntentExtractor`
2. Create `ActivitySummaryWorkflow`
3. Implement query parsing and response formatting
4. Register workflow
5. Add integration tests

### Phase 3: Notification System (Week 2-3)
1. Create `notifications` database table
2. Implement `NotificationService`
3. Implement `NotificationScheduler`
4. Add reminder logic to `UserContextService`
5. Set up cron job or Celery task

### Phase 4: Proactive Features (Week 3-4)
1. Implement streak tracking
2. Add pattern detection
3. Create personalized message templates
4. Add celebration notifications
5. Implement smart reminder timing

## Database Schema Updates

### New Table: notifications
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- 'reminder', 'celebration', 'insight'
    action_buttons TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    read_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### New Table: user_preferences
```sql
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    water_reminder_enabled BOOLEAN DEFAULT 1,
    water_reminder_time TEXT DEFAULT '14:00', -- 2 PM
    mood_reminder_enabled BOOLEAN DEFAULT 1,
    mood_reminder_time TEXT DEFAULT '10:00', -- 10 AM
    challenge_reminder_enabled BOOLEAN DEFAULT 1,
    streak_celebrations_enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Benefits of This Architecture

### 1. Separation of Concerns
- **Workflows**: Handle conversation logic
- **Context Service**: Handle data retrieval and business logic
- **Repositories**: Handle database queries
- **Notification Service**: Handle delivery

### 2. Reusability
- Same context service used by:
  - Chat workflows
  - Notification scheduler
  - API endpoints
  - Dashboard/reports

### 3. Testability
- Each layer can be tested independently
- Mock context service for workflow tests
- Mock repositories for context service tests

### 4. Scalability
- Easy to add new reminder types
- Easy to add new data sources
- Easy to add new notification channels

### 5. Maintainability
- Clear responsibility boundaries
- Easy to find and fix bugs
- Easy to add features

## Example Usage

### Reactive (User-Initiated)
```python
# User asks: "What did I do today?"
# → ActivitySummaryWorkflow
summary = context_service.get_daily_summary(user_id)
# → Returns: water, sleep, exercise, mood data
# → Formats into readable message
```

### Proactive (System-Initiated)
```python
# Scheduler runs at 2 PM
# → NotificationScheduler.check_water_reminder()
result = context_service.should_send_reminder(user_id, 'water_reminder')
if result['should_send']:
    message = generate_water_reminder_message(result['data'])
    notification_service.send_push_notification(user_id, message)
```

## Conclusion

The solution is a **Context Service Layer** that:
1. Centralizes user data retrieval
2. Provides business logic for reminders and patterns
3. Enables both reactive (chat) and proactive (notifications) features
4. Maintains clean architecture and separation of concerns

This solves not just activity summaries, but ALL features requiring user data:
- ✅ Activity summaries
- ✅ Proactive reminders
- ✅ Streak tracking
- ✅ Pattern detection
- ✅ Personalized recommendations
- ✅ Progress tracking
- ✅ Celebrations and achievements
