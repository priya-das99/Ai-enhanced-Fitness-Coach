# How Insights Are Calculated - Complete Technical Guide

## 🎯 Overview

Insights are calculated using a **3-layer deterministic system** that analyzes user history through rule-based logic (NO AI/LLM for analysis - only for natural language phrasing).

```
User Data → Pattern Detection → Insight Generation → LLM Phrasing → User
```

---

## 📊 Layer 1: Data Collection

### Data Sources

The system analyzes data from multiple tables:

#### 1. Mood Logs (`mood_logs`)
```sql
SELECT mood_emoji, reason, timestamp
FROM mood_logs
WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
```

**Collected Metrics:**
- Mood emoji (😊 😌 😟 😢 😭 😡)
- Reason for mood (work, stress, tired, etc.)
- Timestamp (for pattern detection)
- Frequency of negative moods
- Consecutive negative days

#### 2. Activity History (`user_activity_history`)
```sql
SELECT activity_id, activity_name, duration_minutes, timestamp, day_of_week
FROM user_activity_history
WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
```

**Collected Metrics:**
- Activity frequency
- Activity types
- Duration patterns
- Day-of-week preferences
- Time-of-day preferences
- Activity streaks

#### 3. Health Activities (`health_activities`)
```sql
SELECT activity_type, value, unit, timestamp
FROM health_activities
WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
```

**Collected Metrics:**
- Sleep hours (average, consistency)
- Water intake (glasses per day)
- Exercise frequency (sessions per week)
- Weekly trends
- Baseline comparisons

#### 4. Suggestion History (`suggestion_history`)
```sql
SELECT suggestion_key, interaction_type, shown_at
FROM suggestion_history
WHERE user_id = ? AND shown_at >= datetime('now', '-7 days')
```

**Collected Metrics:**
- Acceptance rate (% of suggestions accepted)
- Rejection rate
- Ignored suggestions
- Fatigue patterns (repeated suggestions)

#### 5. Challenge Progress (`user_challenges`, `challenge_progress`)
```sql
SELECT challenge_id, status, progress, started_at
FROM user_challenges
WHERE user_id = ? AND status = 'active'
```

**Collected Metrics:**
- Active challenges
- Progress percentages
- Completion rates
- Struggling challenges

---

## 🔍 Layer 2: Pattern Detection

### PatternDetector Service

The `PatternDetector` analyzes raw data to identify behavioral patterns using **rule-based logic**.

### Pattern Categories

#### 1. Mood Patterns

**Consecutive Negative Days**
```python
# Algorithm
negative_moods = ['😟', '😰', '😢', '😭', '😡', '😤']
consecutive_count = 0
max_consecutive = 0

for mood_log in recent_moods:
    if mood_log.emoji in negative_moods:
        consecutive_count += 1
        max_consecutive = max(max_consecutive, consecutive_count)
    else:
        consecutive_count = 0

# Result
has_prolonged_stress = max_consecutive >= 3
```

**Recurring Reason**
```sql
SELECT reason, COUNT(*) as count
FROM mood_logs
WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
GROUP BY reason
ORDER BY count DESC
LIMIT 1
```

**Output:**
```python
{
    'consecutive_negative_days': 4,
    'has_prolonged_stress': True,
    'recurring_reason': 'work',
    'recurring_reason_count': 8
}
```

---

#### 2. Activity Patterns

**Activity Decline Detection**
```python
# Current week activity count
current_week = count_activities(last_7_days)

# Baseline (average of previous 3 weeks)
baseline = average_activities(days_8_to_30) / 3

# Calculate drop percentage
if baseline > 0:
    drop_percentage = ((baseline - current_week) / baseline) * 100
    has_decline = drop_percentage >= 50
else:
    drop_percentage = 0
    has_decline = False
```

**Activity Streak Calculation**
```python
# Algorithm
def calculate_streak(activity_dates):
    streak = 0
    expected_date = today
    
    for date in sorted_dates_descending:
        if date == expected_date:
            streak += 1
            expected_date = expected_date - 1_day
        else:
            break
    
    return streak

# Example
dates = ['2026-03-03', '2026-03-02', '2026-03-01', '2026-02-28']
streak = 4  # 4 consecutive days
```

**Day-of-Week Analysis**
```sql
SELECT day_of_week, COUNT(*) as activity_count
FROM user_activity_history
WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
GROUP BY day_of_week
ORDER BY activity_count DESC
```

**Output:**
```python
{
    'current_week_count': 5,
    'baseline_per_week': 10,
    'activity_drop': True,
    'activity_drop_percentage': 50,
    'streak': 7,
    'has_streak': True,
    'most_active_day': 'Monday',
    'least_active_day': 'Thursday'
}
```

---

#### 3. Engagement Patterns

**Suggestion Acceptance Rate**
```python
# Last 7 days
total_shown = count_suggestions_shown(last_7_days)
total_accepted = count_suggestions_accepted(last_7_days)

acceptance_rate = (total_accepted / total_shown * 100) if total_shown > 0 else 0
low_engagement = acceptance_rate < 30 and total_shown >= 10
```

**Output:**
```python
{
    'acceptance_rate': 25.5,
    'low_acceptance': True,
    'total_shown': 15,
    'total_accepted': 4,
    'total_rejected': 3,
    'total_ignored': 8
}
```

---

#### 4. Effectiveness Patterns

**Best Activity Detection**
```sql
-- Find activity with highest rating and frequency
SELECT activity_id, activity_name, 
       COUNT(*) as times_done,
       AVG(user_rating) as avg_rating
FROM user_activity_history
WHERE user_id = ? 
  AND timestamp >= datetime('now', '-30 days')
  AND completed = 1
  AND user_rating IS NOT NULL
GROUP BY activity_id
HAVING times_done >= 3
ORDER BY avg_rating DESC, times_done DESC
LIMIT 1
```

**Best for Stress**
```sql
-- Find activity that works best when stressed
SELECT activity_id, activity_name,
       COUNT(*) as times_done,
       AVG(user_rating) as avg_rating
FROM user_activity_history
WHERE user_id = ?
  AND (reason LIKE '%stress%' OR reason LIKE '%anxious%')
  AND user_rating IS NOT NULL
GROUP BY activity_id
HAVING times_done >= 2
ORDER BY avg_rating DESC
LIMIT 1
```

**Output:**
```python
{
    'best_activity': {
        'id': 'meditation',
        'name': 'Meditation',
        'times_done': 6,
        'avg_rating': 4.5
    },
    'best_for_stress': {
        'id': 'breathing',
        'name': 'Breathing Exercise',
        'times_done': 7,
        'avg_rating': 4.8
    }
}
```

---

## 💡 Layer 3: Insight Generation

### InsightGenerator Service

Converts detected patterns into **structured insight objects** using deterministic rules.

### Insight Rules & Thresholds

#### Rule 1: Prolonged Stress Pattern (Priority 1)
```python
RULE = {
    'threshold': {
        'consecutive_stressed_days': 3
    },
    'severity_levels': {
        'moderate': 3,  # 3-4 days
        'high': 5       # 5+ days
    },
    'priority': 1,  # Highest
    'context': 'stress'
}

# Check
if consecutive_negative_days >= 3:
    severity = 'high' if consecutive_negative_days >= 5 else 'moderate'
    
    insight = InsightObject(
        insight_type='prolonged_stress_pattern',
        severity=severity,
        priority=1,
        data={
            'consecutive_days': 4,
            'recurring_reason': 'work'
        },
        context='stress'
    )
```

---

#### Rule 2: Activity Decline (Priority 2)
```python
RULE = {
    'threshold': {
        'activity_drop_percentage': 50
    },
    'severity_levels': {
        'moderate': 50,  # 50-74% drop
        'high': 75       # 75%+ drop
    },
    'priority': 2,
    'context': 'activity'
}

# Check
if activity_drop_percentage >= 50:
    severity = 'high' if activity_drop_percentage >= 75 else 'moderate'
    
    insight = InsightObject(
        insight_type='activity_decline',
        severity=severity,
        priority=2,
        data={
            'drop_percentage': 60,
            'current_week': 5,
            'baseline': 10
        },
        context='activity'
    )
```

---

#### Rule 3: Stress-Inactivity Cycle (Priority 1)
```python
RULE = {
    'threshold': {
        'consecutive_stressed_days': 3,
        'activity_drop_percentage': 40
    },
    'severity_levels': {
        'high': 1  # Always high if detected
    },
    'priority': 1,  # Highest - dangerous pattern
    'context': 'stress'
}

# Check (BOTH conditions must be true)
if (consecutive_stressed_days >= 3 AND activity_drop_percentage >= 40):
    insight = InsightObject(
        insight_type='stress_inactivity_cycle',
        severity='high',
        priority=1,
        data={
            'stressed_days': 4,
            'activity_drop': 60
        },
        context='stress'
    )
```

---

#### Rule 4: Proven Solution Available (Priority 1)
```python
RULE = {
    'threshold': {
        'best_activity_exists': True,
        'current_stressed': True
    },
    'priority': 1,
    'context': 'stress'
}

# Check
if best_for_stress_exists AND currently_stressed:
    insight = InsightObject(
        insight_type='proven_solution_available',
        severity='moderate',
        priority=1,
        data={
            'activity_name': 'Meditation',
            'activity_id': 'meditation',
            'times_done': 6,
            'avg_rating': 4.5
        },
        context='stress'
    )
```

---

#### Rule 5: Low Engagement (Priority 3)
```python
RULE = {
    'threshold': {
        'acceptance_rate': 30,
        'min_shown': 10
    },
    'severity_levels': {
        'moderate': 30,  # 15-30% acceptance
        'high': 15       # <15% acceptance
    },
    'priority': 3,
    'context': 'engagement'
}

# Check
if acceptance_rate < 30 AND total_shown >= 10:
    severity = 'high' if acceptance_rate < 15 else 'moderate'
    
    insight = InsightObject(
        insight_type='low_engagement',
        severity=severity,
        priority=3,
        data={
            'acceptance_rate': 25.5
        },
        context='engagement'
    )
```

---

#### Rule 6: Activity Streak (Priority 4)
```python
RULE = {
    'threshold': {
        'streak_days': 7
    },
    'severity_levels': {
        'low': 7,       # 7-13 days
        'moderate': 14  # 14+ days
    },
    'priority': 4,  # Lower - celebration
    'context': 'celebration'
}

# Check
if streak >= 7:
    severity = 'moderate' if streak >= 14 else 'low'
    
    insight = InsightObject(
        insight_type='activity_streak',
        severity=severity,
        'priority': 4,
        data={
            'streak_days': 7
        },
        context='celebration'
    )
```

---

### Insight Priority System

When multiple insights are available, they're ranked by priority:

```python
Priority 1 (Critical) 🔴
├─ stress_inactivity_cycle       # Dangerous pattern
├─ prolonged_stress_pattern      # 3+ stressed days
└─ proven_solution_available     # We know what works

Priority 2 (Important) 🟡
└─ activity_decline              # 50%+ drop

Priority 3 (Helpful) 🟢
└─ low_engagement                # <30% acceptance

Priority 4 (Positive) 🔵
└─ activity_streak               # 7+ day streak
```

---

## ⏰ Layer 4: Rate Limiting & Filtering

### Rate Limiting Rules

**24-Hour Cooldown**
```python
def apply_rate_limiting(user_id, insights):
    cache = insight_cache[user_id]  # {insight_type: last_shown_timestamp}
    now = datetime.now()
    filtered = []
    
    for insight in insights:
        last_shown = cache.get(insight.insight_type)
        
        if last_shown:
            time_since = now - last_shown
            if time_since < timedelta(hours=24):
                continue  # Skip - shown too recently
        
        filtered.append(insight)
    
    return filtered
```

**Session Limit**
```python
# Max 1 insight per session
insights_this_session = session_tracker.get_count(user_id)

if insights_this_session >= 1:
    return []  # No more insights this session
```

**Mood Log Frequency**
```python
# Max 1 insight per 3 mood logs
mood_logs_since_last_insight = tracker.get_mood_count(user_id)

if mood_logs_since_last_insight < 3:
    return []  # Wait for more mood logs
```

---

### Context Filtering

```python
def filter_by_context(insights, current_context):
    # Map user context to insight context
    context_map = {
        'stressed': 'stress',
        'tired': 'activity',
        'bored': 'engagement'
    }
    
    target = context_map.get(current_context, current_context)
    
    # Prioritize matching context
    matching = [i for i in insights if i.context == target]
    others = [i for i in insights if i.context != target]
    
    return matching + others  # Matching first, then others
```

---

## 🗣️ Layer 5: Natural Language Generation

### LLM Phrasing (NOT Analysis!)

The LLM receives **structured insight data** and converts it to natural language:

```python
# Input to LLM (structured)
insight = {
    'insight_type': 'prolonged_stress_pattern',
    'severity': 'moderate',
    'data': {
        'consecutive_days': 4,
        'recurring_reason': 'work'
    }
}

# LLM Prompt
"""
Convert this insight to natural language:
Pattern: User has been stressed for 4 consecutive days (reason: work)

Rules:
- Be warm and supportive
- Don't mention specific numbers unless natural
- Focus on support, not analysis
- Keep it brief
"""

# LLM Output (natural language)
"I've noticed you've been stressed about work for a few days now. 
Let's find something to help you break this pattern."
```

**Key Point:** The LLM does NOT analyze or decide - it only phrases pre-determined insights in natural language.

---

## 📊 Complete Example: Demo User

### Step 1: Data Collection (31 Days)
```python
mood_logs = 60  # 2 per day
activities = 89  # Various types
health_activities = 259  # Sleep, water, exercise
mood_distribution = {
    'positive': 39 (65%),
    'neutral': 17 (28%),
    'negative': 4 (7%)
}
```

### Step 2: Pattern Detection
```python
patterns = {
    'mood_patterns': {
        'consecutive_negative_days': 0,  # No prolonged stress
        'has_prolonged_stress': False,
        'recurring_reason': None
    },
    'activity_patterns': {
        'current_week_count': 12,
        'baseline_per_week': 12,
        'activity_drop': False,
        'activity_drop_percentage': 0,
        'streak': 31,  # Active all 31 days!
        'has_streak': True,
        'most_active_day': 'Monday' (16 activities),
        'least_active_day': 'Thursday' (6 activities)
    },
    'engagement_patterns': {
        'acceptance_rate': 50,  # Good engagement
        'low_acceptance': False
    }
}
```

### Step 3: Insight Generation
```python
# Available insights (based on patterns)
insights = [
    InsightObject(
        insight_type='activity_streak',
        severity='moderate',
        priority=4,
        data={'streak_days': 31},
        context='celebration'
    ),
    # No stress insights (no prolonged stress detected)
    # No decline insights (activity stable)
    # No engagement issues (50% acceptance rate)
]
```

### Step 4: LLM Phrasing
```python
# Structured insight
{
    'insight_type': 'activity_streak',
    'data': {'streak_days': 31}
}

# Natural language output
"Excellent consistency! You've been active 31 out of 30 days - that's 103%! 
You're building incredibly strong wellness habits."
```

---

## 🎯 Summary

### How Insights Are Calculated

1. **Data Collection** - Query last 30 days of user data
2. **Pattern Detection** - Apply rule-based algorithms to detect patterns
3. **Insight Generation** - Convert patterns to structured insights using thresholds
4. **Rate Limiting** - Filter by 24h cooldown, session limit, mood log frequency
5. **Context Filtering** - Prioritize relevant insights
6. **Priority Sorting** - Order by priority (1=highest)
7. **LLM Phrasing** - Convert structured data to natural language

### Key Principles

✅ **Deterministic** - Same data always produces same insights
✅ **Rule-Based** - No AI/LLM for analysis, only for phrasing
✅ **Threshold-Driven** - Clear numeric thresholds for each insight
✅ **Priority-Based** - Critical insights shown first
✅ **Rate-Limited** - Prevents overwhelming users
✅ **Context-Aware** - Shows relevant insights at right time

### For Demo User

Based on 31 days of data:
- ✅ **Consistency insight** - 31/30 days active (103%)
- ✅ **Monday peak** - Most active on Mondays (16 activities)
- ✅ **Evening preference** - 67% evening activities
- ✅ **Mood distribution** - 65% positive
- ✅ **Health metrics** - 7.6h sleep, 6.9 glasses water
- ❌ **No stress insights** - No prolonged stress detected
- ❌ **No decline insights** - Activity stable

All insights are **data-ready** and calculated using the rules above!
