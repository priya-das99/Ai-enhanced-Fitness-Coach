# Insights System Guide

## Overview

The system generates **7 types of insights** based on user behavior patterns over the past 30 days. These insights are shown at appropriate times to help users understand their patterns and take action.

## Insight Types

### 1. 🚨 Prolonged Stress Pattern (Priority 1 - Highest)

**What it detects:**
- User has been stressed for 3+ consecutive days
- Same reason recurring (e.g., "work")

**Threshold:**
- 3+ consecutive days with negative mood (😟, 😢, 😰)
- Same reason mentioned repeatedly

**When it shows:**
- When user logs a negative mood again
- Proactively after mood logging
- In response to stress-related queries

**Example message:**
```
💡 I've noticed you've been stressed for 7 consecutive days, mostly about work. 
Let's work on this together.
```

**Data pattern that triggers it:**
```
Feb 13: 😟 work
Feb 14: 😟 work
Feb 15: 😟 work
Feb 16: 😟 work
Feb 17: 😟 work
... (continues)
```

---

### 2. 🚨 Stress-Inactivity Cycle (Priority 1 - Highest)

**What it detects:**
- Prolonged stress (3+ days) AND
- Activity dropped 40%+ from baseline

**Threshold:**
- 3+ consecutive stressed days
- Activity level dropped 40% or more

**When it shows:**
- After mood logging (proactive)
- When suggesting activities
- High priority - shown even if user didn't ask

**Example message:**
```
💡 I've noticed you've been stressed for 7 days and your activity has dropped 60%. 
This pattern can make things harder. Let's break it together.
```

**Data pattern that triggers it:**
```
Week 1 (Baseline): 5 activities/week (meditation, exercise)
Week 3 (Stress): 1 activity/week (60% drop)
+ Stressed mood every day
```

---

### 3. 📉 Activity Decline (Priority 2)

**What it detects:**
- Activity level dropped 40%+ from baseline
- No stress required (just inactivity)

**Threshold:**
- 40%+ drop in activity frequency

**When it shows:**
- When suggesting activities
- In response to "I'm bored" or "nothing to do"
- Lower priority than stress-related insights

**Example message:**
```
I've noticed your activity has decreased lately. 
Would you like to try something to get back on track?
```

**Data pattern that triggers it:**
```
Week 1: 5 activities
Week 3: 2 activities (60% drop)
```

---

### 4. 🔥 Activity Streak (Priority 4 - Positive)

**What it detects:**
- User has been active for 3+ consecutive days

**Threshold:**
- 3+ consecutive days with at least one activity

**When it shows:**
- As positive reinforcement
- When user logs activity
- Celebration message

**Example message:**
```
🔥 You're on a 5-day streak! That's amazing - keep it going!
```

**Data pattern that triggers it:**
```
Feb 27: Meditation ✅
Feb 28: Exercise ✅
Mar 1: Meditation ✅
Mar 2: Exercise ✅
Mar 3: Meditation ✅
```

---

### 5. 💡 Proven Solution Available (Priority 1)

**What it detects:**
- User has a history of effective activities for current mood
- Activity worked well in the past (high completion rate)

**Threshold:**
- Activity completed 3+ times
- 80%+ completion rate
- Helped with similar mood before

**When it shows:**
- When suggesting activities for stress/anxiety
- Personalized recommendations
- "This worked for you before"

**Example message:**
```
Meditation has been really effective for you in the past. 
Would you like to try a session?
```

**Data pattern that triggers it:**
```
Past activities for stress:
- Meditation: 8 times, 100% completion
- Exercise: 3 times, 66% completion
→ Suggests meditation first
```

---

### 6. 📈 Improvement Trend (Priority 4 - Positive)

**What it detects:**
- Mood improving over past week
- Activity increasing
- Sleep improving

**Threshold:**
- Positive mood 5+ days in past week
- Activity increased from previous week
- Sleep hours increased

**When it shows:**
- As encouragement
- When user asks "how am I doing?"
- Positive reinforcement

**Example message:**
```
📈 Great progress! Your mood and activity have improved significantly 
over the past week. Keep it up!
```

**Data pattern that triggers it:**
```
Week 3: 😟 every day, 1 activity
Week 4: 😊 5/7 days, 5 activities
→ Clear improvement
```

---

### 7. 😴 Low Engagement (Priority 3)

**What it detects:**
- User hasn't interacted much
- Few mood logs or activities
- Minimal engagement

**Threshold:**
- Less than 3 interactions in past week
- No activities logged

**When it shows:**
- Gentle check-in
- "Haven't seen you in a while"
- Encouragement to engage

**Example message:**
```
I haven't heard from you in a while. How are you doing?
```

**Data pattern that triggers it:**
```
Past 7 days: 1 mood log, 0 activities
```

---

## Insight Priority System

Insights are shown based on priority:

| Priority | Type | When Shown |
|----------|------|------------|
| 1 (Highest) | Prolonged Stress, Stress-Inactivity, Proven Solution | Always shown if detected |
| 2 | Activity Decline | Shown if no P1 insights |
| 3 | Low Engagement | Shown if no P1/P2 insights |
| 4 (Lowest) | Activity Streak, Improvement Trend | Shown as positive reinforcement |

## Timing Rules

### Rate Limiting
- Same insight shown max once per 24 hours
- Prevents insight fatigue

### Context-Aware Timing
- High session fatigue → No insights
- User just started → No insights yet
- User engaged → Show insights
- User stressed → Show high-priority insights

### Proactive vs Reactive

**Proactive (shown automatically):**
- Prolonged Stress Pattern
- Stress-Inactivity Cycle
- Activity Streak

**Reactive (shown when relevant):**
- Activity Decline (when suggesting activities)
- Proven Solution (when suggesting for stress)
- Improvement Trend (when user asks)
- Low Engagement (periodic check-in)

## Testing the 30-Day Data

### Step 1: Generate Data
```bash
cd backend
python create_30_day_history.py
```

### Step 2: Login on March 6, 2026
The system will treat it as "today" and analyze the past 30 days.

### Step 3: Test Scenarios

#### Scenario 1: Stress Query
```
User: "I'm feeling stressed about work"

Expected Response:
💡 I've noticed you've been stressed for 7 consecutive days, mostly about work.
Let's work on this together.

Here are some activities that might help:
[Meditation] [Breathing Exercise] [Take a Break]
```

#### Scenario 2: Activity Query
```
User: "What should I do?"

Expected Response:
💡 Meditation has been really effective for you in the past.

Here are some suggestions:
[Start Meditation Session] [Exercise] [Breathing]
```

#### Scenario 3: Mood Logging
```
User: "I'm feeling okay today"

Expected Response:
📈 Great progress! Your mood has improved over the past week.

[Log another mood] [Try an activity]
```

#### Scenario 4: Check Progress
```
User: "How am I doing?"

Expected Response:
📈 You're on a 5-day activity streak! 🔥

Your mood and activity have improved significantly. Keep it up!
```

## Data Patterns in 30-Day History

### Week 1 (Feb 4-10): Baseline
- 😊 Happy mood every day
- 6 glasses water/day
- Activity every other day
- 7.5 hours sleep
- **Purpose:** Establish normal baseline

### Week 2 (Feb 11-17): Stress Onset
- Days 1-2: Normal
- Days 3-7: 😟 Stressed (work)
- Reduced water (2 glasses/day)
- Less activity
- Poor sleep (5.5 hours)
- **Purpose:** Start stress pattern

### Week 3 (Feb 18-24): Prolonged Stress
- 😟 Stressed every day (work)
- 1 glass water/day
- Almost no activity (2 activities all week)
- 5 hours sleep
- **Purpose:** Trigger prolonged stress + inactivity cycle

### Week 4 (Feb 25-Mar 3): Recovery
- Days 1-2: Still stressed
- Days 3-7: 😊 Happy
- 4 glasses water/day
- Daily activity (meditation)
- 7 hours sleep
- **Purpose:** Show improvement + build streak

### Days 29-30 (Mar 4-5): Recent
- 😊 Happy
- 4 glasses water/day
- Activity daily
- 7+ hours sleep
- **Purpose:** Maintain positive trend

## Expected Insights on March 6

When user logs in on March 6, 2026:

1. **Prolonged Stress Pattern** ✅
   - Detected: 7+ consecutive stressed days (Feb 13-24)
   - Reason: "work"
   - Will show if user mentions stress

2. **Stress-Inactivity Cycle** ✅
   - Detected: Stress + 60% activity drop
   - Will show proactively after mood logging

3. **Activity Decline** ✅
   - Detected: 60% drop from baseline
   - Will show when suggesting activities

4. **Activity Streak** ✅
   - Detected: 5 consecutive active days (Feb 27-Mar 3)
   - Will show as positive reinforcement

5. **Improvement Trend** ✅
   - Detected: Mood improved, activity increased
   - Will show when user asks about progress

6. **Proven Solution** ✅
   - Detected: Meditation completed 8+ times
   - Will prioritize meditation for stress

## Personalization Effects

### Activity Suggestions
- **Meditation** will be suggested first (proven effective)
- **Exercise** will be suggested second
- **Breathing** will be suggested third

### Response Tone
- Empathetic for stress (acknowledges prolonged pattern)
- Encouraging for improvement (celebrates streak)
- Supportive for decline (gentle nudge)

### Timing
- Won't overwhelm with insights
- Shows most relevant insight first
- Rate-limited to prevent fatigue

## How to Verify

### Check Database
```sql
-- Check mood logs
SELECT created_at, mood_emoji, reason 
FROM mood_logs 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 30;

-- Check activities
SELECT created_at, activity_type, duration_minutes 
FROM activity_logs 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 20;

-- Check water logs
SELECT created_at, quantity, unit 
FROM health_activities 
WHERE user_id = 1 AND activity_type = 'water'
ORDER BY created_at DESC 
LIMIT 30;
```

### Test Insights
```bash
# Run insight generator directly
cd backend
python -c "
from app.services.insight_generator import get_insight_generator
from app.services.pattern_detector import PatternDetector

detector = PatternDetector()
generator = get_insight_generator()

patterns = detector.detect_all_patterns(user_id=1)
insights = generator.generate_insights(user_id=1)

for insight in insights:
    print(f'{insight.insight_type}: {insight.message}')
"
```

## Summary

The 30-day data creates a realistic user journey:
1. **Normal baseline** (Week 1)
2. **Stress develops** (Week 2)
3. **Prolonged stress + inactivity** (Week 3) → Triggers critical insights
4. **Recovery begins** (Week 4) → Triggers positive insights
5. **Improvement continues** (Days 29-30) → Maintains positive trend

This allows testing of ALL insight types and personalization features in a realistic scenario.
