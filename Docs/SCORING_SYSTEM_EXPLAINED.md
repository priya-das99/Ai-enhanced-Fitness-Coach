# 🎯 Suggestion Scoring System - Complete Breakdown

## Overview

The scoring system uses **multiple factors** to rank suggestions from 0-100+ points. Higher score = better match for user's situation.

---

## Scoring Factors (7 Categories)

### 1. Reason Matching (+10 to +15 points)
**What:** Does the activity help with the user's specific reason?

**How it works:**
Each activity has a `best_for` list of keywords:
```python
"breathing": {
    "best_for": ["stress", "anxiety", "work", "quick relief"]
}

"call_friend": {
    "best_for": ["loneliness", "friend", "relationship", "support"]
}
```

**Scoring logic:**
```python
if reason:
    reason_lower = reason.lower()  # "work deadline"
    for keyword in activity['best_for']:
        if keyword in reason_lower:
            score += 10  # Match found!
```

**Examples:**

| User Reason | Activity | Keywords Matched | Points |
|-------------|----------|------------------|--------|
| "work deadline" | breathing | "work" ✓ | +10 |
| "work deadline" | take_break | "work" ✓ | +10 |
| "work deadline" | call_friend | none ✗ | 0 |
| "feeling lonely" | call_friend | "loneliness" ✓ | +10 |
| "relationship fight" | call_friend | "relationship" ✓ | +10 |
| "relationship fight" | journaling | "relationship" ✓ | +10 |

**Why this matters:**
- User says "work stress" → Activities tagged for "work" get boosted
- User says "lonely" → Social activities get boosted
- Ensures suggestions are relevant to the problem

---

### 2. Time of Day Matching (+3 to +5 points)
**What:** Is this activity appropriate for the current time?

**Time periods:**
- Morning: 6 AM - 11 AM
- Afternoon: 12 PM - 5 PM
- Evening: 6 PM - 9 PM
- Night: 10 PM - 5 AM

**Scoring logic:**
```python
time_period = context.get('time_period')  # 'morning', 'afternoon', etc.

if time_period == 'morning':
    if activity_id in ['stretching', 'breathing', 'short_walk']:
        score += 5  # Good morning activities
        
elif time_period == 'afternoon':
    if activity_id in ['take_break', 'short_walk', 'breathing']:
        score += 5  # Good afternoon activities
        
elif time_period == 'evening':
    if activity_id in ['meditation', 'breathing', 'stretching']:
        score += 5  # Good evening activities
        
elif time_period == 'night':
    if activity_id in ['breathing', 'meditation']:
        score += 5  # Good night activities
```

**Examples:**

| Time | Activity | Appropriate? | Points |
|------|----------|--------------|--------|
| 7 AM (morning) | stretching | ✓ Wake up body | +5 |
| 7 AM (morning) | power_nap | ✗ Too early | 0 |
| 3 PM (afternoon) | take_break | ✓ Mid-day refresh | +5 |
| 8 PM (evening) | meditation | ✓ Wind down | +5 |
| 8 PM (evening) | seven_minute_workout | ✗ Too energizing | 0 |
| 11 PM (night) | breathing | ✓ Calm before sleep | +5 |
| 11 PM (night) | short_walk | ✗ Too active | 0 |

**Why this matters:**
- Energizing activities in morning
- Calming activities in evening
- Respects natural circadian rhythm

---

### 3. Work Hours Constraint (+3 to +10 points)
**What:** Can the user do this activity during work hours?

**Work hours:** 9 AM - 5 PM on weekdays

**Activity properties:**
```python
"breathing": {
    "work_friendly": True  # Can do at desk
}

"short_walk": {
    "work_friendly": False  # Need to leave workspace
}
```

**Scoring logic:**
```python
is_work_hours = context.get('is_work_hours')  # True/False

if is_work_hours and activity['work_friendly']:
    score += 10  # Can do at work!
elif not is_work_hours:
    score += 3   # Not at work, more flexibility
```

**Examples:**

| Time | Activity | Work Friendly? | Points |
|------|----------|----------------|--------|
| 2 PM (work) | breathing | ✓ Yes | +10 |
| 2 PM (work) | meditation | ✓ Yes | +10 |
| 2 PM (work) | short_walk | ✗ No | 0 |
| 2 PM (work) | power_nap | ✗ No | 0 |
| 7 PM (home) | breathing | ✓ Yes | +3 |
| 7 PM (home) | short_walk | ✗ No | +3 |

**Why this matters:**
- During work: Only suggest desk-friendly activities
- After work: All activities available
- Practical constraints matter

---

### 4. User Favorites (+8 to +12 points)
**What:** Has the user completed this activity before and liked it?

**Data source:** `user_activity_history` table

**Scoring logic:**
```python
favorites = context.get('favorite_activities', [])
# favorites = [
#     {'id': 'meditation', 'completion_count': 15},
#     {'id': 'journaling', 'completion_count': 10},
#     {'id': 'short_walk', 'completion_count': 8}
# ]

for fav in favorites:
    if fav['id'] == activity_id:
        score += 12  # User loves this!
```

**How favorites are determined:**
```sql
-- Top 3 most completed activities
SELECT activity_id, COUNT(*) as completion_count
FROM user_activity_history
WHERE user_id = ?
AND completed = 1
GROUP BY activity_id
ORDER BY completion_count DESC
LIMIT 3
```

**Examples:**

| User | Activity | Completion Count | Is Favorite? | Points |
|------|----------|------------------|--------------|--------|
| User A | meditation | 15 times | ✓ Yes | +12 |
| User A | journaling | 10 times | ✓ Yes | +12 |
| User A | breathing | 2 times | ✗ No | 0 |
| User B | short_walk | 20 times | ✓ Yes | +12 |
| User B | meditation | 0 times | ✗ No | 0 |

**Why this matters:**
- People stick with what works for them
- Personalization based on actual behavior
- Higher engagement when suggesting favorites

---

### 5. Time Preferences (+2 to +6 points)
**What:** Does the user typically do this activity at this time of day?

**Data source:** `user_activity_history` with `time_of_day` field

**Scoring logic:**
```python
time_prefs = context.get('time_preferences', {}).get(time_period, {})
# time_prefs = {
#     'meditation': 0.8,  # Does meditation 80% of mornings
#     'stretching': 0.6,  # Does stretching 60% of mornings
#     'breathing': 0.3    # Does breathing 30% of mornings
# }

if activity_id in time_prefs:
    score += time_prefs[activity_id] * 2  # Scale to points
```

**How preferences are calculated:**
```sql
-- For morning activities
SELECT 
    activity_id,
    COUNT(*) * 1.0 / (SELECT COUNT(DISTINCT date) FROM user_activity_history WHERE time_of_day = 'morning') as frequency
FROM user_activity_history
WHERE user_id = ?
AND time_of_day = 'morning'
GROUP BY activity_id
```

**Examples:**

| User | Time | Activity | Frequency | Points |
|------|------|----------|-----------|--------|
| User A | Morning | meditation | 80% (0.8) | +1.6 |
| User A | Morning | stretching | 60% (0.6) | +1.2 |
| User A | Afternoon | take_break | 90% (0.9) | +1.8 |
| User B | Evening | journaling | 70% (0.7) | +1.4 |

**Why this matters:**
- People have routines (meditation every morning)
- Suggesting activities at their usual time increases acceptance
- Respects user habits

---

### 6. Reason Preferences (+3 to +9 points)
**What:** When the user has THIS problem, what do they usually do?

**Data source:** `user_activity_history` with `reason` field

**Scoring logic:**
```python
reason_prefs = context.get('reason_preferences', {}).get(reason, {})
# reason_prefs = {
#     'breathing': 0.7,    # 70% of time for work stress
#     'take_break': 0.5,   # 50% of time for work stress
#     'meditation': 0.3    # 30% of time for work stress
# }

if activity_id in reason_prefs:
    score += reason_prefs[activity_id] * 3  # Scale to points
```

**How preferences are calculated:**
```sql
-- For "work" related stress
SELECT 
    activity_id,
    COUNT(*) * 1.0 / (SELECT COUNT(*) FROM user_activity_history WHERE reason LIKE '%work%') as frequency
FROM user_activity_history
WHERE user_id = ?
AND reason LIKE '%work%'
GROUP BY activity_id
```

**Examples:**

| User | Reason | Activity | Usage Rate | Points |
|------|--------|----------|------------|--------|
| User A | work stress | breathing | 70% (0.7) | +2.1 |
| User A | work stress | take_break | 50% (0.5) | +1.5 |
| User A | relationship | call_friend | 80% (0.8) | +2.4 |
| User B | anxiety | meditation | 90% (0.9) | +2.7 |

**Why this matters:**
- User knows what works for specific problems
- "When I'm stressed about work, breathing helps"
- Pattern recognition from past behavior

---

### 7. Recent Activity Penalty (-5 to -10 points)
**What:** Did the user recently do this activity? If yes, penalize it.

**Data source:** `suggestion_history` and `user_activity_history` tables

**Scoring logic:**
```python
recent_activities = context.get('recent_activities', [])
# recent_activities = [
#     {'activity_id': 'breathing', 'timestamp': '30 minutes ago'},
#     {'activity_id': 'meditation', 'timestamp': '2 hours ago'}
# ]

recent_ids = [a['activity_id'] for a in recent_activities[:2]]

if activity_id in recent_ids:
    score -= 8  # Significant penalty!
```

**Cooldown periods:**
- Last 30 minutes: -10 points (very recent)
- Last 2 hours: -8 points (recent)
- Last 4 hours: -5 points (somewhat recent)

**Examples:**

| Activity | Last Used | Penalty | Reason |
|----------|-----------|---------|--------|
| breathing | 20 min ago | -10 | Too soon! |
| meditation | 1 hour ago | -8 | Still recent |
| journaling | 3 hours ago | -5 | Somewhat recent |
| stretching | Yesterday | 0 | Old enough |
| hydrate | Never | 0 | Never used |

**Why this matters:**
- Prevents repetition fatigue
- Encourages variety
- User won't see same suggestions repeatedly

---

## Complete Scoring Example

### Scenario: Work Stress at 2 PM (Tuesday)

**User Profile:**
- User ID: 10030
- Favorites: meditation (15x), journaling (10x), short_walk (8x)
- Recent: breathing (30 min ago)
- Time preferences: meditation in afternoon (80%)
- Reason preferences: breathing for work stress (70%)

**Input:**
- Mood: 😟 (stressed)
- Reason: "work deadline"
- Time: 2:00 PM (afternoon, work hours)
- Day: Tuesday (weekday)

---

### Activity 1: Breathing

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | "work" in best_for | +10 |
| Time of day | afternoon activity | +5 |
| Work friendly | True, during work | +10 |
| User favorite | Not in top 3 | 0 |
| Time preference | Not typical afternoon | 0 |
| Reason preference | 70% for work stress | +2.1 |
| Recent penalty | Used 30 min ago | -10 |
| **TOTAL** | | **17.1** |

---

### Activity 2: Take Break

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | "work" in best_for | +10 |
| Time of day | afternoon activity | +5 |
| Work friendly | True, during work | +10 |
| User favorite | Not in top 3 | 0 |
| Time preference | Not tracked | 0 |
| Reason preference | Not tracked | 0 |
| Recent penalty | Never used | 0 |
| **TOTAL** | | **25** |

---

### Activity 3: Meditation

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | No "work" keyword | 0 |
| Time of day | Not typical afternoon | 0 |
| Work friendly | True, during work | +10 |
| User favorite | #1 favorite (15x) | +12 |
| Time preference | 80% in afternoon | +1.6 |
| Reason preference | Not for work stress | 0 |
| Recent penalty | Not recent | 0 |
| **TOTAL** | | **23.6** |

---

### Activity 4: Journaling

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | No "work" keyword | 0 |
| Time of day | Not typical afternoon | 0 |
| Work friendly | True, during work | +10 |
| User favorite | #2 favorite (10x) | +12 |
| Time preference | Not typical afternoon | 0 |
| Reason preference | Not for work stress | 0 |
| Recent penalty | Not recent | 0 |
| **TOTAL** | | **22** |

---

### Activity 5: Short Walk

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | No "work" keyword | 0 |
| Time of day | afternoon activity | +5 |
| Work friendly | False, can't do at work | 0 |
| User favorite | #3 favorite (8x) | +12 |
| Time preference | Not typical afternoon | 0 |
| Reason preference | Not for work stress | 0 |
| Recent penalty | Not recent | 0 |
| **TOTAL** | | **17** |

---

### Activity 6: Power Nap

| Factor | Calculation | Points |
|--------|-------------|--------|
| Reason match | No "work" keyword | 0 |
| Time of day | Not typical afternoon | 0 |
| Work friendly | False, can't do at work | 0 |
| User favorite | Not in top 3 | 0 |
| Time preference | Not tracked | 0 |
| Reason preference | Not tracked | 0 |
| Recent penalty | Not recent | 0 |
| **TOTAL** | | **0** |

---

## Final Ranking

| Rank | Activity | Score | Why It Won |
|------|----------|-------|------------|
| 1 | Take Break | 25.0 | Work-friendly + reason match + time appropriate |
| 2 | Meditation | 23.6 | User favorite + work-friendly + time preference |
| 3 | Journaling | 22.0 | User favorite + work-friendly |
| 4 | Breathing | 17.1 | Penalized for recent use (-10) |
| 5 | Short Walk | 17.0 | Not work-friendly (0 points) |
| 6 | Power Nap | 0.0 | Not work-friendly + no matches |

**Top 3 sent to LLM for final ranking:**
1. Take Break (25.0)
2. Meditation (23.6)
3. Journaling (22.0)

---

## Scoring Weights Summary

| Factor | Weight | Impact |
|--------|--------|--------|
| Reason match | +10 | High - Must address the problem |
| Work friendly (during work) | +10 | High - Practical constraint |
| User favorite | +12 | High - Proven to work for user |
| Time of day | +5 | Medium - Appropriate timing |
| Time preference | +2-6 | Medium - User habits |
| Reason preference | +3-9 | Medium - Problem-specific habits |
| Recent penalty | -8 to -10 | High - Prevent repetition |

---

## Why This Scoring System Works

### 1. Multi-Dimensional
- Not just one factor (e.g., "most popular")
- Considers context, user, time, constraints

### 2. Personalized
- Uses user's actual history
- Learns from behavior
- Adapts over time

### 3. Practical
- Respects work hours
- Considers time of day
- Prevents repetition

### 4. Balanced
- No single factor dominates
- Multiple paths to high score
- Fallback when no history

### 5. Transparent
- Clear point values
- Explainable results
- Easy to debug

---

## Tuning the Scoring System

Want to adjust the weights? Here's how:

```python
# Current weights
REASON_MATCH_WEIGHT = 10
WORK_FRIENDLY_WEIGHT = 10
FAVORITE_WEIGHT = 12
TIME_OF_DAY_WEIGHT = 5
RECENT_PENALTY = -8

# To make favorites more important:
FAVORITE_WEIGHT = 15  # Increase from 12

# To reduce recent penalty:
RECENT_PENALTY = -5  # Reduce from -8

# To prioritize reason matching:
REASON_MATCH_WEIGHT = 15  # Increase from 10
```

---

## Summary

The scoring system combines:
- **Context** (time, work hours, reason)
- **Personalization** (favorites, preferences)
- **Constraints** (work-friendly, recent use)

Result: Suggestions that are:
- ✅ Relevant to the problem
- ✅ Appropriate for the time
- ✅ Personalized to the user
- ✅ Practical and actionable
- ✅ Varied (not repetitive)

This is why the improved system feels "smart" - it considers everything! 🎯
