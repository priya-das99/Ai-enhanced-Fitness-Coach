# Module Activities - Implementation Summary

## Current Situation

Your system currently uses **hardcoded activities** in `smart_suggestions.py`. The activities are not in a database table yet.

## Your Requirements

You want to add 3 new activities that trigger external modules:
1. **Start Outdoor Activity** → Opens outdoor module
2. **Start 7-Minute Workout** → Opens workout module  
3. **Start Meditation Session** → Opens meditation module

## Solution: Two Approaches

### Approach 1: Quick Implementation (Recommended)

Add the activities to the hardcoded list and handle module triggering in frontend.

### Approach 2: Full Database Migration

Create `suggestion_master` table and migrate all activities to database.

---

## ✅ Approach 1: Quick Implementation (RECOMMENDED)

### Step 1: Add Activities to Hardcoded List

**File:** `backend/chat_assistant/smart_suggestions.py`

Find `WELLNESS_ACTIVITIES_FALLBACK` and add:

```python
WELLNESS_ACTIVITIES_FALLBACK = {
    # ... existing activities ...
    
    # NEW: Module-triggering activities
    "outdoor_activity": {
        "id": "outdoor_activity",
        "name": "Start Outdoor Activity",
        "effort": "medium",
        "work_friendly": False,
        "description": "Get outside for fresh air and nature",
        "duration": "20 min",
        "best_for": ["energy", "mood boost", "stress"],
        "triggers_module": "outdoor_activity",  # NEW
        "module_type": "external"  # NEW
    },
    "seven_minute_workout": {
        "id": "seven_minute_workout",
        "name": "Start 7-Minute Workout",
        "effort": "high",
        "work_friendly": False,
        "description": "Quick high-intensity workout",
        "duration": "7 min",
        "best_for": ["energy", "exercise", "stress"],
        "triggers_module": "7min_workout",  # NEW
        "module_type": "external"  # NEW
    },
    "guided_meditation": {
        "id": "guided_meditation",
        "name": "Start Meditation Session",
        "effort": "low",
        "work_friendly": True,
        "description": "Guided meditation for calm and focus",
        "duration": "10 min",
        "best_for": ["stress", "anxiety", "calm", "focus"],
        "triggers_module": "meditation",  # NEW
        "module_type": "external"  # NEW
    }
}
```

### Step 2: Update Frontend Button Handler

**File:** `frontend/chat.js`

```javascript
function handleSuggestionClick(button) {
    const buttonData = JSON.parse(button.dataset.action);
    
    // Check if this triggers an external module
    if (buttonData.module_type === 'external') {
        handleModuleActivity(buttonData);
    } else if (buttonData.action_type === 'open_external') {
        // External content (blogs, videos)
        window.open(buttonData.content_url, '_blank');
        trackContentClick(buttonData.id);
    } else {
        // Internal activity (breathing, water, etc.)
        handleInternalActivity(buttonData);
    }
}

function handleModuleActivity(buttonData) {
    // Save state before leaving chat
    const chatState = {
        waiting_for_module: buttonData.triggers_module,
        activity_id: buttonData.id,
        activity_name: buttonData.name,
        timestamp: Date.now()
    };
    
    localStorage.setItem('pending_module', JSON.stringify(chatState));
    
    // Send message to chat
    sendMessage(buttonData.user_message || buttonData.name);
    
    // Navigate to module
    const moduleRoutes = {
        'outdoor_activity': '/outdoor',
        '7min_workout': '/workout',
        'meditation': '/meditation'
    };
    
    const route = moduleRoutes[buttonData.triggers_module];
    if (route) {
        // Small delay to show message
        setTimeout(() => {
            window.location.href = route;
        }, 500);
    }
}
```

### Step 3: Handle Module Completion

**In each module (workout.html, meditation.html, outdoor.html):**

```javascript
// When user completes the module
function onModuleComplete() {
    // Get pending module info
    const pending = JSON.parse(localStorage.getItem('pending_module'));
    
    if (pending) {
        // Log the activity
        fetch('/api/v1/activity/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                activity_type: pending.activity_id,
                quantity: 1,
                unit: 'session',
                notes: `Completed ${pending.activity_name}`
            })
        });
        
        // Mark as completed
        pending.completed = true;
        pending.completed_at = Date.now();
        localStorage.setItem('pending_module', JSON.stringify(pending));
    }
    
    // Return to chat
    window.location.href = '/chat';
}
```

### Step 4: Handle Chat Resume

**In chat.js - on page load:**

```javascript
// Check if returning from module
async function checkModuleCompletion() {
    const pending = JSON.parse(localStorage.getItem('pending_module'));
    
    if (pending && pending.completed) {
        // Show completion message
        displayBotMessage(`Great job completing ${pending.activity_name}! 🎉`);
        displayBotMessage("How are you feeling now?");
        
        // Clear pending state
        localStorage.removeItem('pending_module');
        
        // Show mood buttons
        showMoodButtons();
    }
}

// Call on page load
window.addEventListener('DOMContentLoaded', checkModuleCompletion);
```

---

## Chat State Management

### State Flow:

```
1. User in chat: "I'm stressed"
   State: {workflow: 'mood_logging', step: 'suggesting_action'}

2. Bot shows: "Start Meditation Session" button
   State: {workflow: 'mood_logging', step: 'suggesting_action', suggestions: [...]}

3. User clicks button
   Frontend saves: {waiting_for_module: 'meditation', activity_id: 'guided_meditation'}
   Frontend navigates to: /meditation

4. User completes meditation
   Module calls: onModuleComplete()
   Module logs activity
   Module updates state: {completed: true}
   Module navigates to: /chat

5. Chat loads
   Chat checks: localStorage.getItem('pending_module')
   Chat shows: "Great job! How do you feel?"
   Chat clears: localStorage.removeItem('pending_module')
```

### State Persistence:

**LocalStorage:**
```javascript
{
    "pending_module": {
        "waiting_for_module": "meditation",
        "activity_id": "guided_meditation",
        "activity_name": "Start Meditation Session",
        "timestamp": 1234567890,
        "completed": true,
        "completed_at": 1234567900
    }
}
```

---

## Response Messages

### When User Returns from Module:

**Option 1: Simple**
```
Bot: "Great job completing the meditation! 🧘"
Bot: "How are you feeling now?"
[😊 Better] [😐 Same] [😢 Worse]
```

**Option 2: Detailed**
```
Bot: "Awesome! You completed a 10-minute meditation session! 🎉"
Bot: "Has your stress level improved?"
[Much better] [A bit better] [No change] [Worse]
```

**Option 3: Continue Conversation**
```
Bot: "Nice work on the meditation! 🧘"
Bot: "Would you like to:"
[Log how I feel] [Try another activity] [End session]
```

---

## Testing

### Test Scenario 1: Complete Flow
```
1. Open chat
2. Say "I'm stressed"
3. Click "Start Meditation Session"
4. → Redirects to /meditation
5. Complete meditation
6. Click "Done" in module
7. → Returns to /chat
8. See "Great job!" message
9. Answer "How do you feel?"
```

### Test Scenario 2: Abandoned Module
```
1. Click "Start 7-Minute Workout"
2. → Redirects to /workout
3. Close tab without completing
4. Later: Open /chat
5. See "Want to continue the workout?"
```

### Test Scenario 3: Multiple Activities
```
1. Complete meditation
2. Return to chat
3. Say "Still stressed"
4. Click "Start Outdoor Activity"
5. Complete outdoor activity
6. Return to chat
7. See "2 activities completed today! 🎉"
```

---

## Implementation Checklist

### Backend:
- [ ] Add 3 new activities to `WELLNESS_ACTIVITIES_FALLBACK`
- [ ] Add `triggers_module` and `module_type` fields
- [ ] Ensure activities appear in suggestions

### Frontend (chat.js):
- [ ] Add `handleModuleActivity()` function
- [ ] Save state to localStorage before navigation
- [ ] Add `checkModuleCompletion()` on page load
- [ ] Show completion message when returning

### Modules (workout.html, meditation.html, outdoor.html):
- [ ] Add "Complete" button
- [ ] Call `onModuleComplete()` when done
- [ ] Log activity via API
- [ ] Navigate back to chat

### Testing:
- [ ] Test complete flow
- [ ] Test abandoned module
- [ ] Test multiple modules
- [ ] Test state persistence

---

## Quick Start

### 1. Add Activities (5 minutes)
Edit `backend/chat_assistant/smart_suggestions.py` and add the 3 activities to `WELLNESS_ACTIVITIES_FALLBACK`.

### 2. Update Frontend (10 minutes)
Add the button handler and state management code to `frontend/chat.js`.

### 3. Update Modules (15 minutes)
Add completion callbacks to each module (workout, meditation, outdoor).

### 4. Test (10 minutes)
Test the complete flow with each module.

**Total Time: ~40 minutes**

---

## Summary

✅ **3 new module-triggering activities** defined
✅ **State management** using localStorage
✅ **Frontend integration** pattern provided
✅ **Module completion** callbacks specified
✅ **Chat resume** logic documented

**Key Points:**
1. Activities marked with `module_type='external'` trigger modules
2. State saved in localStorage before navigation
3. Module calls completion callback when done
4. Chat checks state on load and shows message
5. Activity logged for analytics

**The assistant state remains in "suggesting_action" until user responds to the "How do you feel?" question after returning from the module.**

---

## Need Help?

If you need the actual code files created, let me know and I can:
1. Create the updated `smart_suggestions.py` with new activities
2. Create the frontend handler code
3. Create module completion templates
4. Create test scripts

Just ask! 🚀
