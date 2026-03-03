# MoodCapture System Documentation - Part 6: Challenge System

## 7. Challenge System Architecture

### Overview
Challenges are goal-based activities that users can complete over multiple days to earn points and build habits.

### Database Schema

#### Challenges Table
```sql
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title TEXT,                    -- "Walk 7,000+ steps 4 days this week"
    description TEXT,
    challenge_type TEXT,           -- "steps", "meditation", "mood"
    duration_days INTEGER,         -- 4 (complete in 4 days)
    points INTEGER,                -- 50 (reward points)
    is_active BOOLEAN
)
```

#### User Challenges Table
```sql
CREATE TABLE user_challenges (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    challenge_id INTEGER,
    status TEXT,                   -- "active", "completed", "failed"
    progress INTEGER,              -- 0-100 (percentage)
    started_at DATETIME,
    completed_at DATETIME
)
```

#### Challenge Progress Table
```sql
CREATE TABLE challenge_progress (
    id INTEGER PRIMARY KEY,
    user_challenge_id INTEGER,
    date DATE,                     -- "2026-02-27"
    value_achieved REAL,           -- 7500 (steps), 1 (mood logged)
    target_met BOOLEAN,            -- Did they meet today's goal?
    notes TEXT,
    UNIQUE(user_challenge_id, date)  -- One entry per day
)
```

### Core Components

#### 7.1 Challenge Service
**File**: `backend/app/services/challenge_service.py`

```python
class ChallengeService:
    def enroll_user(user_id: int, challenge_id: int):
        """
        Enrolls user in a challenge
        
        Steps:
        1. Check if already enrolled
        2. Create user_challenges entry
        3. Initialize progress to 0
        4. Return enrollment confirmation
        """
    
    def update_progress(user_id: int, challenge_type: str, value: float):
        """
        Updates challenge progress when user logs activity
        
        Called automatically when:
        - User logs mood (mood challenges)
        - User logs steps (step challenges)
        - User completes meditation (meditation challenges)
        
        Steps:
        1. Find active challenges of this type
        2. Check if today's goal already met
        3. Record progress for today
        4. Calculate overall progress percentage
        5. Check if challenge completed
        6. Award points if completed
        """
    
    def get_user_challenges(user_id: int):
        """
        Gets all challenges for user with progress
        
        Returns:
        [
            {
                "id": 1,
                "title": "Log mood 3 days this week",
                "progress": 66,  # 2 out of 3 days
                "days_completed": 2,
                "days_required": 3,
                "status": "active",
                "points": 25
            }
        ]
        """
```

#### 7.2 Challenge Repository
**File**: `backend/app/repositories/challenge_repository.py`

```python
class ChallengeRepository:
    def get_active_challenges():
        """Returns all available challenges"""
    
    def get_user_challenge_progress(user_challenge_id: int):
        """
        Gets detailed progress for a specific challenge
        
        Returns:
        {
            "challenge": {...},
            "progress_by_date": [
                {"date": "2026-02-25", "target_met": True},
                {"date": "2026-02-26", "target_met": True},
                {"date": "2026-02-27", "target_met": False}
            ],
            "days_completed": 2,
            "days_remaining": 1
        }
        """
    
    def mark_challenge_complete(user_challenge_id: int):
        """
        Marks challenge as completed
        
        Steps:
        1. Update status to 'completed'
        2. Set completed_at timestamp
        3. Award points to user
        4. Trigger completion notification
        """
```

### Challenge Workflow

#### Enrollment Flow
```python
# File: backend/chat_assistant/challenges_workflow.py

User: "I want to join a challenge"
Bot: Shows available challenges

User: Clicks "Join" on "Log mood 3 days"
→ ChallengeService.enroll_user(user_id, challenge_id)
→ Creates user_challenges entry
→ Bot: "Great! You're enrolled. Log your mood to make progress!"
```

#### Progress Update Flow
```python
# Automatic progress tracking

User: Logs mood with 😊
→ MoodWorkflow.handle_mood_logged()
→ ChallengeService.update_progress(user_id, "mood", 1)
→ Finds active mood challenges
→ Records progress for today
→ Calculates: 2/3 days = 66% progress
→ Bot: "Nice! Challenge progress: 2/3 days completed 🎯"
```

#### Completion Flow
```python
User: Logs mood (3rd day)
→ ChallengeService.update_progress(user_id, "mood", 1)
→ Detects: 3/3 days completed
→ ChallengeService.mark_challenge_complete()
→ Awards 25 points
→ Bot: "🎉 Challenge completed! You earned 25 points!"
```

### Challenge Types

#### 1. Mood Logging Challenge
```python
{
    "title": "Log your mood 3 days this week",
    "challenge_type": "mood",
    "duration_days": 3,
    "target": 1,  # Log once per day
    "points": 25
}

# Progress tracking
def check_mood_challenge(user_id, date):
    # Check if mood logged today
    mood_logged = has_mood_log_for_date(user_id, date)
    if mood_logged:
        record_progress(user_challenge_id, date, value=1, target_met=True)
```

#### 2. Activity Challenge
```python
{
    "title": "Walk 7,000+ steps 4 days this week",
    "challenge_type": "steps",
    "duration_days": 4,
    "target": 7000,  # Steps per day
    "points": 50
}

# Progress tracking
def check_steps_challenge(user_id, steps, date):
    target_met = steps >= 7000
    record_progress(user_challenge_id, date, value=steps, target_met=target_met)
```

#### 3. Meditation Challenge
```python
{
    "title": "Meditate 5+ minutes 2 days this week",
    "challenge_type": "meditation",
    "duration_days": 2,
    "target": 5,  # Minutes per day
    "points": 25
}
```

### Integration with Chat

**File**: `backend/chat_assistant/challenges_workflow.py`

```python
class ChallengesWorkflow:
    def handle(user_id: int, message: str):
        """
        Handles challenge-related messages
        
        Intents:
        - "show challenges" → List available challenges
        - "my challenges" → Show user's active challenges
        - "join challenge" → Enrollment flow
        - "challenge progress" → Show detailed progress
        """
    
    def handle_challenge_query(user_id: int):
        """
        User asks about challenges
        
        Response includes:
        - Active challenges with progress
        - Available challenges to join
        - Points earned
        """
        
        active = ChallengeService.get_user_challenges(user_id)
        available = ChallengeService.get_available_challenges()
        
        return f"""
        Your Active Challenges:
        📊 Log mood 3 days: 66% (2/3 days)
        💪 Exercise 4 days: 25% (1/4 days)
        
        Available Challenges:
        🧘 Meditate 2 days (25 points)
        💧 Drink 8 glasses water 5 days (50 points)
        
        [View Details] [Join Challenge]
        """
```

### Progress Calculation

```python
def calculate_progress(user_challenge_id: int) -> int:
    """
    Calculates challenge progress percentage
    
    Logic:
    1. Get challenge requirements (e.g., 3 days)
    2. Count days where target was met
    3. Calculate percentage
    
    Example:
    Challenge: Log mood 3 days
    Progress: 2 days completed
    Percentage: (2 / 3) * 100 = 66%
    """
    
    challenge = get_challenge(user_challenge_id)
    progress_records = get_progress_records(user_challenge_id)
    
    days_completed = sum(1 for p in progress_records if p.target_met)
    days_required = challenge.duration_days
    
    percentage = (days_completed / days_required) * 100
    return min(percentage, 100)  # Cap at 100%
```

### Points System

**Table**: `user_points`
```sql
CREATE TABLE user_points (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    total_points INTEGER,
    challenges_completed INTEGER,
    current_streak INTEGER,
    longest_streak INTEGER
)
```

```python
def award_points(user_id: int, points: int, reason: str):
    """
    Awards points to user
    
    Updates:
    - total_points
    - challenges_completed (if challenge)
    - current_streak (if daily challenge)
    """
    
    UPDATE user_points
    SET total_points = total_points + ?,
        challenges_completed = challenges_completed + 1
    WHERE user_id = ?
```

### Files Involved

**Core Challenge Logic**:
- `backend/app/services/challenge_service.py` - Main service
- `backend/app/repositories/challenge_repository.py` - Data access
- `backend/chat_assistant/challenges_workflow.py` - Chat integration

**Database**:
- `backend/migrations/003_add_challenges.py` - Schema creation

**API Endpoints**:
- `backend/app/api/v1/endpoints/admin.py` - Challenge management

**Testing**:
- `backend/test_complete_challenge_flow.py`
- `backend/test_challenge_progress_issue.py`
