# Complete Insight Factors - What's Actually Analyzed

## 🎯 Summary

The proactive insights analyze **5 major factors**, not just mood:

1. ✅ **Mood Patterns** (stress, consecutive negative days)
2. ✅ **Activity Patterns** (decline, streaks)
3. ✅ **Sleep Patterns** (hours, decline)
4. ✅ **Water Intake** (glasses, decline)
5. ✅ **Combined Patterns** (stress + inactivity cycle)

---

## 📊 All Factors Analyzed

### 1. Mood Patterns ✅

**What's Tracked:**
- Consecutive days of negative mood (😟, 😰, 😢, 😭, 😡, 😤)
- Recurring stress reasons (work, family, health, etc.)
- Mood frequency and intensity

**Insights Generated:**
- **Prolonged Stress Pattern**
  - Trigger: 3+ consecutive stressed days
  - Example: "I've noticed you've been stressed for 6 consecutive days, mostly about work"

**Code:**
```python
# backend/app/services/pattern_detector.py
def _detect_mood_patterns(self, conn, user_id):
    # Counts consecutive negative mood days
    # Identifies recurring reasons
```

---

### 2. Activity Patterns ✅

**What's Tracked:**
- Current week activity count
- Baseline activity level (last 30 days average)
- Activity decline percentage
- Activity streaks (consecutive days)

**Insights Generated:**
- **Activity Decline**
  - Trigger: 50%+ drop from baseline
  - Example: "Your activity has declined 64% - from 2.8 activities to just 1 in the last week"

- **Activity Streak** (Positive)
  - Trigger: 3+ consecutive days
  - Example: "You're on a 7-day activity streak! Keep it going!"

**Code:**
```python
# backend/app/services/pattern_detector.py
def _detect_activity_patterns(self, conn, user_id):
    # Compares current week to baseline
    # Calculates decline percentage
    # Tracks consecutive activity days
```

---

### 3. Sleep Patterns ✅

**What's Tracked:**
- Average sleep hours (current week)
- Baseline sleep hours (previous 3 weeks)
- Sleep decline percentage

**Insights Generated:**
- **Sleep Decline**
  - Trigger: 15%+ decrease in sleep hours
  - Example: "Your sleep has decreased to 5.9 hours, down from 7.1 hours"
  - Shows as supplementary info with stress patterns

**Code:**
```python
# backend/app/services/pattern_detector.py
def _detect_health_patterns(self, conn, user_id):
    # Calculates current vs baseline sleep
    # Detects 15%+ decline
```

---

### 4. Water Intake Patterns ✅

**What's Tracked:**
- Average glasses per day (current week)
- Baseline water intake (previous 3 weeks)
- Water decline percentage

**Insights Generated:**
- **Water Decline**
  - Trigger: 50%+ decrease in water intake
  - Example: "Your water intake has dropped 81% - averaging only 1.3 glasses per day, down from 6.6"
  - Links to stress impact: "Dehydration can worsen stress"

**Code:**
```python
# backend/app/services/pattern_detector.py
def _detect_health_patterns(self, conn, user_id):
    # Calculates current vs baseline water
    # Detects 50%+ decline
```

---

### 5. Combined Patterns ✅

**What's Tracked:**
- Stress + Activity decline together
- Stress + Sleep decline together
- Multiple declining factors

**Insights Generated:**
- **Stress-Inactivity Cycle** (Highest Priority)
  - Trigger: 3+ days stress + 40%+ activity drop
  - Example: "I've noticed you've been stressed for 6 days and your activity has dropped 64%. This pattern can make things harder. Let's break it together."

**Code:**
```python
# backend/app/services/insight_generator.py
def _check_stress_inactivity_cycle(self, patterns):
    # Checks both stress AND activity decline
    # Highest priority pattern
```

---

## 🔍 How Factors Combine in Insights

### Example: insight_test User

**Data Detected:**
```
Mood: 6 consecutive stressed days (about work)
Activity: 15 activities this week (normal)
Sleep: 5.9 hours (down from 7.1 hours = 17% decline)
Water: 1.0 glasses (no decline detected)
```

**Insight Shown:**
```
💡 I've noticed you've been stressed for 6 consecutive days, 
mostly about work. Let's work on this together.

I also see your sleep has decreased to 5.9 hours (from 7.1). 
This can affect how you feel.
```

**Why These Factors:**
- ✅ Stress pattern (primary concern)
- ✅ Sleep decline (supplementary - explains why stress persists)
- ✗ Activity (normal, not mentioned)
- ✗ Water (normal, not mentioned)

---

## 📋 Complete Factor Checklist

When you log a stressed mood, the system checks:

- [x] **Mood History** - How many consecutive stressed days?
- [x] **Stress Reason** - What's the recurring cause?
- [x] **Activity Level** - Has it dropped significantly?
- [x] **Sleep Hours** - Are you getting less sleep?
- [x] **Water Intake** - Are you drinking less water?
- [x] **Combined Patterns** - Stress + inactivity cycle?
- [x] **Proven Solutions** - What activities helped before?

---

## 🎨 Insight Priority System

### Priority 1 (Shown Proactively):
1. **Stress-Inactivity Cycle** - Stress + activity decline
2. **Prolonged Stress Pattern** - 3+ consecutive days
3. **Proven Solution Available** - Activity that worked before

### Priority 2 (Shown on Request):
4. **Activity Decline** - 50%+ drop
5. **Sleep Decline** - 15%+ drop (shown with stress)
6. **Water Decline** - 50%+ drop (shown with stress)

### Priority 3 (Lower Priority):
7. **Low Engagement** - <30% suggestion acceptance

### Priority 4 (Celebrations):
8. **Activity Streak** - 3+ consecutive days

---

## 💡 Real Examples

### Example 1: Stress + Sleep Decline
```
User Data:
- 6 days stressed about work
- Sleep: 5.9h (was 7.1h)
- Activity: Normal
- Water: Normal

Insight:
"💡 I've noticed you've been stressed for 6 consecutive days, 
mostly about work. Let's work on this together.

I also see your sleep has decreased to 5.9 hours (from 7.1). 
This can affect how you feel."
```

### Example 2: Stress + Activity + Water Decline
```
User Data:
- 10 days stressed
- Activity: 2 (was 15) = 87% decline
- Water: 1.3 glasses (was 6.6) = 81% decline
- Sleep: Normal

Insight:
"💡 I've noticed you've been stressed for 10 consecutive days. 
Your activity has dropped 87% and your water intake has dropped 81%.

This combination can make stress worse. Let's work on breaking 
this pattern together."
```

### Example 3: Activity Streak (Positive)
```
User Data:
- 7 consecutive days with activities
- Mood: Positive
- All metrics: Good

Insight:
"🔥 You're on a 7-day activity streak! You're building a 
great habit. Keep it going!"
```

---

## 🔧 Where Each Factor is Detected

### Pattern Detection:
**File:** `backend/app/services/pattern_detector.py`

```python
def detect_all_patterns(self, user_id):
    return {
        'mood_patterns': self._detect_mood_patterns(),      # ✅ Stress, consecutive days
        'activity_patterns': self._detect_activity_patterns(), # ✅ Decline, streaks
        'health_patterns': self._detect_health_patterns(),   # ✅ Sleep, water
        'engagement_patterns': {...},                        # ✅ Suggestion acceptance
        'effectiveness_patterns': {...}                      # ✅ What works for user
    }
```

### Insight Generation:
**File:** `backend/app/services/insight_generator.py`

```python
def generate_insights(self, user_id):
    patterns = self.pattern_detector.detect_all_patterns(user_id)
    
    insights = []
    
    # Check each factor
    if self._check_prolonged_stress(patterns):           # ✅ Mood
        insights.append(self._create_prolonged_stress_insight())
    
    if self._check_activity_decline(patterns):           # ✅ Activity
        insights.append(self._create_activity_decline_insight())
    
    if self._check_stress_inactivity_cycle(patterns):    # ✅ Combined
        insights.append(self._create_stress_inactivity_cycle_insight())
    
    # Health patterns added to existing insights
    # Sleep and water shown as supplementary info
    
    return insights
```

### Proactive Display:
**File:** `backend/chat_assistant/mood_workflow.py`

```python
# After mood logging
insights = insight_gen.generate_insights(user_id, current_mood=mood_emoji)

# Format with ALL factors
if insight.insight_type == 'prolonged_stress_pattern':
    message = format_stress_insight(insight)
    
    # Add health factors if present
    if health_patterns['sleep_decline']:
        message += format_sleep_decline()
    
    if health_patterns['water_decline']:
        message += format_water_decline()
```

---

## 🎯 Summary

**You asked:** "So you have just added mood based insights and what about other factors?"

**Answer:** The system analyzes **ALL these factors**:

1. ✅ **Mood** - Consecutive stressed days, recurring reasons
2. ✅ **Activity** - Decline percentage, streaks
3. ✅ **Sleep** - Hours, decline from baseline
4. ✅ **Water** - Glasses, decline from baseline
5. ✅ **Combined** - Stress + inactivity cycles

**The proactive insight shows:**
- Primary concern (stress pattern)
- Contributing factors (sleep decline, water decline, activity decline)
- Supportive message
- Actionable suggestions

**It's not just mood-based** - it's a comprehensive analysis of the user's wellbeing across multiple dimensions!

---

## 🧪 Test All Factors

To see different factors in action:

```bash
cd backend
python test_insights_in_progress.py
```

This shows which factors are detected for each test user:
- insight_demo: Stress + Activity decline
- insight_test: Stress + Sleep decline
- demo_user: Activity streak (positive)

Each user demonstrates different factor combinations!
