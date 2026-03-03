# Module Integration Guide - External Activity Modules

## Overview

This guide explains how to integrate external activity modules (Outdoor Activity, 7-Minute Workout, Meditation) with the chat assistant.

## Architecture

### Flow Diagram:
```
┌─────────────┐
│   User      │
│  "Stressed" │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Chat Assistant                     │
│  - Detects mood                     │
│  - Generates suggestions            │
│  - Shows buttons                    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  User Clicks Button                 │
│  "Start 7-Minute Workout"           │
└──────┬──────────────────────────────┘
       │
       ├─── Internal Activity (breathing, water)
       │    └─> Log immediately → Chat response
       │
       └─── External Module (workout, meditation)
            └─> Open module → User completes → Return to chat
```

## New Activities Added

### 1. Start Outdoor Activity 🌳
- **ID:** `outdoor_activity`
- **Module:** `outdoor_activity`
- **Effort:** Medium
- **Duration:** 20 minutes
- **Best for:** Energy, mood boost, nature
- **Triggers when:** User needs energy, fresh air, mood boost

### 2. Start 7-Minute Workout 💪
- **ID:** `seven_minute_workout`
- **Module:** `7min_workout`
- **Effort:** High
- **Duration:** 7 minutes
- **Best for:** Energy, quick exercise, stress relief
- **Triggers when:** User needs energy, physical activity

### 3. Start Meditation Session 🧘
- **ID:** `guided_meditation`
- **Module:** `meditation`
- **Effort:** Low
- **Duration:** 10 minutes
- **Best for:** Stress, anxiety, calm, focus
- **Triggers when:** User is stressed, anxious, needs calm

## Database Schema

### Activities Table (suggestion_master):
```sql
CREATE TABLE suggestion_master (
    suggestion_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    effort_level TEXT,
    duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT 1,
    triggers_module TEXT,        -- NEW: Module identifier
    module_type TEXT DEFAULT 'internal'  -- NEW: 'internal' or 'external'
);
```

### Example Data:
```sql
INSERT INTO suggestion_master VALUES
('outdoor_activity', 'Start Outdoor Activity', 
 'Get outside for fresh air', 'physical', 'medium', 20, 1,
 'outdoor_activity', 'external'),
 
('seven_minute_workout', 'Start 7-Minute Workout',
 'Quick high-intensity workout', 'physical', 'high', 7, 1,
 '7min_workout', 'external'),
 
('guided_meditation', 'Start Meditation Session',
 'Guided meditation for calm', 'mindfulness', 'low', 10, 1,
 'meditation', 'external');
```

## Frontend Integration

### Button Response Format:
```javascript
{
    "id": "seven_minute_workout",
    "name": "Start 7-Minute Workout",
    "description": "Quick high-intensity workout",
    "duration": "7 min",
    "effort": "high",
    "user_message": "Start 7-minute workout",
    "action_type": "open_module",  // NEW: Indicates module trigger
    "module_id": "7min_workout",   // NEW: Module to open
    "module_type": "external"      // NEW: External module
}
```

### Frontend Handling:
```javascript
// In chat.js
function handleButtonClick(button) {
    const actionType = button.action_type;
    
    if (actionType === 'open_module') {
        // External module
        const moduleId = button.module_id;
        
        // Save chat state
        saveChatState({
            waiting_for_module: moduleId,
            activity_id: button.id,
            timestamp: Date.now()
        });
        
        // Open module
        openExternalModule(moduleId);
        
    } else if (actionType === 'open_external') {
        // External link (content)
        window.open(button.content_url, '_blank');
        trackContentClick(button.id);
        
    } else {
        // Internal activity (breathing, water, etc.)
        logActivity(button.id);
    }
}

function openExternalModule(moduleId) {
    // Module-specific navigation
    switch(moduleId) {
        case '7min_workout':
            window.location.href = '/workout';
            break;
        case 'outdoor_activity':
            window.location.href = '/outdoor';
            break;
        case 'meditation':
            window.location.href = '/meditation';
            break;
    }
}
```

## Chat State Management

### State Flow:

#### 1. Before Module Opens:
```python
# Chat state
{
    'workflow': 'mood_logging',
    'step': 'suggesting_action',
    'mood': '😰',
    'reason': 'work stress',
    'suggestions': [...],
    'waiting_for_module': None  # Not waiting
}
```

#### 2. User Clicks "Start 7-Minute Workout":
```python
# Frontend saves state
localStorage.setItem('chat_state', JSON.stringify({
    'waiting_for_module': '7min_workout',
    'activity_id': 'seven_minute_workout',
    'mood': '😰',
    'reason': 'work stress',
    'timestamp': Date.now()
}));

# Navigate to module
window.location.href = '/workout';
```

#### 3. User Completes Workout:
```python
# Module calls completion endpoint
POST /api/v1/activity/complete
{
    'activity_id': 'seven_minute_workout',
    'duration_minutes': 7,
    'completed': true
}

# Backend logs activity
# Backend updates chat state
```

#### 4. User Returns to Chat:
```python
# Frontend checks state
const chatState = JSON.parse(localStorage.getItem('chat_state'));

if (chatState.waiting_for_module) {
    // Show completion message
    displayMessage("Great job completing the 7-minute workout! How do you feel now?");
    
    // Clear waiting state
    chatState.waiting_for_module = null;
    localStorage.setItem('chat_state', JSON.stringify(chatState));
}
```

## Backend API Endpoints

### 1. Activity Completion Endpoint:
```python
# backend/app/api/v1/endpoints/activity.py

@router.post("/complete")
async def complete_module_activity(
    request: ModuleActivityRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Called when user completes an external module activity
    """
    # Log the activity
    activity_service.log_activity(
        user_id=current_user['id'],
        activity_type=request.activity_id,
        quantity=request.duration_minutes,
        unit='minutes'
    )
    
    # Update chat state
    chat_service.update_module_completion(
        user_id=current_user['id'],
        module_id=request.module_id,
        completed=True
    )
    
    return {
        "status": "completed",
        "message": "Activity logged successfully",
        "next_prompt": "How do you feel after the workout?"
    }
```

### 2. Chat Resume Endpoint:
```python
@router.get("/resume")
async def resume_after_module(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get chat state after returning from module
    """
    state = chat_service.get_pending_module_state(current_user['id'])
    
    if state:
        return {
            "has_pending": True,
            "module_id": state['module_id'],
            "activity_id": state['activity_id'],
            "prompt": "How do you feel after completing the activity?"
        }
    
    return {"has_pending": False}
```

## Module Response Messages

### After Module Completion:

**Option 1: Simple Acknowledgment**
```
Bot: "Great job completing the 7-minute workout! 💪"
Bot: "How are you feeling now?"
```

**Option 2: Follow-up Question**
```
Bot: "Awesome! You completed the workout! 🎉"
Bot: "On a scale of 1-5, how energized do you feel?"
[1] [2] [3] [4] [5]
```

**Option 3: Mood Check**
```
Bot: "Nice work on the meditation session! 🧘"
Bot: "Has your stress level changed?"
[Much better] [A bit better] [Same] [Worse]
```

## Implementation Steps

### Step 1: Run Migration
```bash
python backend/migrations/006_add_module_activities.py
```

### Step 2: Update Frontend Button Handler
```javascript
// Add to chat.js
if (button.action_type === 'open_module') {
    saveChatState({
        waiting_for_module: button.module_id,
        activity_id: button.id
    });
    openExternalModule(button.module_id);
}
```

### Step 3: Add Module Completion Callback
```javascript
// In each module (workout.js, meditation.js, outdoor.js)
function onModuleComplete() {
    // Call completion API
    fetch('/api/v1/activity/complete', {
        method: 'POST',
        body: JSON.stringify({
            activity_id: 'seven_minute_workout',
            duration_minutes: 7,
            completed: true
        })
    });
    
    // Return to chat
    window.location.href = '/chat';
}
```

### Step 4: Handle Chat Resume
```javascript
// In chat.js - on page load
async function checkModuleCompletion() {
    const response = await fetch('/api/v1/chat/resume');
    const data = await response.json();
    
    if (data.has_pending) {
        displayMessage(data.prompt);
    }
}
```

## State Persistence

### LocalStorage Structure:
```javascript
{
    "chat_state": {
        "waiting_for_module": "7min_workout",
        "activity_id": "seven_minute_workout",
        "mood": "😰",
        "reason": "work stress",
        "timestamp": 1234567890,
        "suggestions_shown": [...]
    }
}
```

### Backend State (Optional):
```python
# Store in database for reliability
CREATE TABLE module_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    module_id TEXT,
    activity_id TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT  -- 'pending', 'completed', 'abandoned'
);
```

## Testing

### Test Scenario 1: Complete Flow
```
1. User: "I'm stressed"
2. Bot: Shows "Start Meditation Session" button
3. User: Clicks button
4. System: Opens meditation module
5. User: Completes 10-minute meditation
6. Module: Calls completion API
7. System: Returns to chat
8. Bot: "Great job! How do you feel now?"
```

### Test Scenario 2: Abandoned Module
```
1. User: Clicks "Start 7-Minute Workout"
2. System: Opens workout module
3. User: Closes without completing
4. User: Returns to chat later
5. Bot: "Want to try the workout again, or something else?"
```

### Test Scenario 3: Multiple Modules
```
1. User: Completes meditation
2. Bot: "How do you feel?"
3. User: "Still stressed"
4. Bot: Shows "Start Outdoor Activity"
5. User: Completes outdoor activity
6. Bot: "Excellent! Two activities today! 🎉"
```

## Summary

✅ **3 new module-triggering activities** added
✅ **Database schema** extended with module fields
✅ **State management** architecture defined
✅ **Frontend integration** pattern documented
✅ **API endpoints** specified
✅ **Testing scenarios** provided

**Key Points:**
1. Activities marked as `module_type='external'` trigger modules
2. Chat state is saved before opening module
3. Module calls completion API when done
4. Chat resumes with contextual message
5. Activity is logged for analytics

**Next:** Implement the frontend button handler and module completion callbacks!
