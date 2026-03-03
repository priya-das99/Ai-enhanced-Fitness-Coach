# Proactive Insights System - How It Works

## Overview
The system **automatically detects patterns** and shows insights to users **without them asking**. This happens when users open the app or during key interactions.

## When Insights Are Shown

### 1. On App Open / Login
When a user opens the app, the `/chat/init` endpoint is called, which:
1. Detects all patterns using `PatternDetector`
2. Identifies actionable patterns (things worth telling the user)
3. Generates a personalized greeting with the top priority insight
4. Shows it automatically in the chat

**Frequency**: Once per day (to avoid being annoying)

### 2. Pattern Detection Priorities

The system checks patterns in this order:

#### HIGH PRIORITY: Stress-Inactivity Cycle ⚠️
**Triggers when:**
- User has been stressed for 3+ consecutive days
- Activity level dropped by 30%+ compared to baseline

**Example Message:**
> "I've noticed you've been feeling stressed about work for the past 5 days, and your activity level has dropped by 40%. Research shows that even light exercise can help reduce stress. Would you like to try a quick 10-minute activity?"

**What It Shows:**
- Insight about the pattern
- Activity suggestions tailored to break the cycle
- Encouragement based on past successes

#### MEDIUM PRIORITY: Proven Solution Available 💡
**Triggers when:**
- User is stressed
- System knows what worked for them before

**Example Message:**
> "You're feeling stressed. Last time this happened, you found that yoga really helped (you rated it 4.5/5). Want to try that again?"

#### MEDIUM PRIORITY: Low Activity 📉
**Triggers when:**
- Activity dropped 30%+ but user isn't stressed
- Gentle nudge to stay active

**Example Message:**
> "Your activity level has been lower than usual this week. Everything okay? Would you like some suggestions to get back on track?"

#### LOW PRIORITY: Activity Streak 🎉
**Triggers when:**
- User has an active streak (3+ days)
- Celebration and encouragement

**Example Message:**
> "Amazing! You've logged activities for 7 days straight! Keep up the great work! 🎉"

## How Pattern Detection Works

### Step 1: Data Collection
```python
# PatternDetector analyzes:
- Last 30 days of mood logs
- Last 30 days of health activities
- Suggestion acceptance rates
- Activity effectiveness ratings
```

### Step 2: Pattern Identification
```python
# Checks for:
mood_patterns = {
    'has_prolonged_stress': True/False,  # 3+ consecutive negative moods
    'consecutive_negative_days': 5,
    'recurring_reason': 'work',
    'dominant_mood': '😟'
}

activity_patterns = {
    'activity_drop': True/False,  # 30%+ drop
    'current_week_count': 2,
    'baseline_per_week': 5,
    'activity_drop_percentage': 60,
    'has_streak': False,
    'streak': 0
}
```

### Step 3: Actionable Insight Generation
```python
# If stress + activity drop detected:
{
    'type': 'stress_inactivity_cycle',
    'priority': 'high',
    'data': {
        'stressed_days': 5,
        'reason': 'work',
        'drop_percentage': 60
    }
}
```

### Step 4: LLM-Generated Message
```python
# LLM creates natural, empathetic message:
"I've noticed you've been feeling stressed about work for the past 5 days, 
and your activity level has dropped significantly. This is a common pattern 
when we're overwhelmed. Would you like to try a quick stress-relief activity?"
```

## Testing with 30-Day User

The test user (`test_user_30days`) has perfect data to test this:

### Week 1-2 (Feb 1-14): Should Trigger HIGH PRIORITY Insight
- **Pattern**: Stressed 😟 for 14 days + No exercise
- **Expected Insight**: "Stress-inactivity cycle detected"
- **Suggestion**: Exercise, meditation, stress relief

### Week 3 (Feb 15-21): Should Trigger MEDIUM PRIORITY
- **Pattern**: Improving, starting exercise
- **Expected Insight**: "Great progress!" or activity suggestions

### Week 4 (Feb 22-28): Should Trigger LOW PRIORITY
- **Pattern**: Consistent exercise, good mood
- **Expected Insight**: "You're on a roll!" celebration

## How to Test

### Test 1: Login as Stressed User (Week 1 Data)
```bash
# Login as test_user_30days
# Expected: Automatic insight about stress + activity drop
# Should see: Personalized message + activity suggestions
```

### Test 2: Check Pattern Detection Manually
```python
from app.services.insight_system import InsightSystem

insight_system = InsightSystem()
insights = insight_system.generate_insights(user_id=21)

print(insights)
# Should show detected patterns and generated messages
```

### Test 3: Verify Greeting Shows Insight
```bash
# Call /chat/init endpoint
# Check response for 'insight' field
# Verify message mentions detected pattern
```

## Current Limitations

### 1. Once Per Day
Insights are shown only once per day on greeting to avoid being annoying.

**Why**: Users don't want to see the same insight every time they open the app.

**Workaround**: Insights can still be requested manually ("How am I doing?")

### 2. Only on Init
Currently, insights are only shown proactively on app open, not during other interactions.

**Enhancement Idea**: Show insights after logging certain activities:
- After logging poor sleep → "I notice your sleep has been poor for 3 days..."
- After logging stressed mood → "This is your 4th stressed day this week..."

### 3. No Push Notifications
System doesn't send push notifications for detected patterns.

**Enhancement Idea**: 
- "You haven't logged any activities in 3 days, everything okay?"
- "Your stress pattern is concerning, want to talk?"

## Code Locations

### Pattern Detection
- `backend/app/services/pattern_detector.py` - Rule-based pattern detection
- `backend/app/services/insight_system.py` - Insight generation orchestration
- `backend/app/services/llm_insight_generator.py` - LLM-powered message generation

### Integration Points
- `backend/app/services/chat_service.py` - `init_conversation()` method
- `backend/app/api/v1/endpoints/chat.py` - `/chat/init` endpoint

## Enhancement: Show Insights After Activity Logging

To make insights more proactive, you could add insight checks after key activities:

```python
# In activity_workflow.py, after logging sleep:
if activity_type == 'sleep' and value < 6:
    # Check for poor sleep pattern
    patterns = pattern_detector.detect_all_patterns(user_id)
    if patterns['activity_patterns']['poor_sleep_streak'] >= 3:
        return {
            'message': "I've noticed you've had poor sleep for 3 nights in a row. This can really affect your mood and energy. Would you like some tips for better sleep?",
            'ui_elements': ['action_buttons'],
            'actions': [sleep_improvement_activities]
        }
```

## Summary

✅ **System ALREADY has proactive insights**
✅ **Automatically detects stress-inactivity cycles**
✅ **Shows insights on app open (once per day)**
✅ **Prioritizes high-impact patterns**
✅ **Uses LLM for natural, empathetic messages**

🔄 **Potential Enhancements:**
- Show insights after logging concerning activities
- Multiple insights per day (context-dependent)
- Push notifications for critical patterns
- Weekly summary insights
