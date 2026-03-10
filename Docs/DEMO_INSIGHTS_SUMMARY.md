# 📊 Demo User Insights Summary

## 🎯 Current Insights Available

The demo user currently has **2 active insights**:

### 1. 🔥 Activity Streak (Moderate Priority)
- **Message**: "You're on a 31-day activity streak! Keep it going!"
- **Severity**: Moderate (🟡)
- **Data**: 31 consecutive days of activity

### 2. 📈 Activity Improvement (Low Priority)
- **Message**: "You're 28% more active this week! (23 activities vs 18.0 baseline)"
- **Severity**: Low (🟢)
- **Data**: 27.8% increase in activity

---

## ⏰ When Insights Appear

### ✅ Automatic Triggers

1. **After Mood Logging** (negative mood + reason)
   - User logs: 😟 😰 😢 😭 😡 😤 😔
   - Must provide a reason
   - Example: "I'm feeling stressed about work"

2. **After Activity Logging** (sleep or exercise)
   - User logs sleep: "I slept 7 hours"
   - User logs exercise: "I did a workout"

3. **After Button Activity**
   - User clicks activity completion button
   - Example: "Complete Meditation" button

4. **User Asks Progress** ⭐ **EASIEST TO TRIGGER**
   - "How am I doing?"
   - "Show my progress"
   - "My trends"
   - "Am I improving?"

5. **Engagement Drop**
   - System detects low engagement (<30% acceptance rate)

---

## 🚫 Timing Restrictions

Insights will **NOT** show if:

- ❌ Already shown 1 insight this session
- ❌ Shown within last 24 hours
- ❌ Less than 3 mood logs since last insight
- ❌ User is venting emotionally
- ❌ User is in clarification flow

**Exception**: High-priority insights (stress patterns) can show after 12 hours instead of 24.

---

## 💬 What Demo User Will See

### When asking "How am I doing?"

```
🔥 You're on a 31-day activity streak! Keep it going!
📈 You're 28% more active this week! (23 activities vs 18.0 baseline)

🎯 Challenges:
Total Points: 1032 | Completed: 4

📈 Making Progress:
  • 7-Day Hydration Challenge: 53%
  • Mindfulness Week: 64%
  • Sleep Better Challenge: 73%

Great momentum! Keep it up! 🚀
```

### After Logging Negative Mood

If patterns detected:
```
💡 Meditation helped you before (rated 4.5/5) - would you like to try that?
```

Or:
```
🔴 You've been stressed for 3 days and your activity dropped 45%.
Let's work together to break this pattern.
```

---

## 🎮 How to Test in Demo

### Quick Test (Easiest):
1. Login as demo user
2. Type: **"How am I doing?"**
3. ✅ See activity streak + improvement + challenges

### Full Test:
1. Log a negative mood: "I'm feeling stressed"
2. Provide reason: "work deadlines"
3. ✅ May see stress pattern insight

### Activity Test:
1. Click "Log Sleep" button
2. Enter hours: "7"
3. ✅ May see sleep pattern insight

---

## 📊 Insight Types Available

| Type | Severity | Priority | When Shown |
|------|----------|----------|------------|
| Activity Streak | 🟡 Moderate | 4 | Progress queries |
| Improvement Trend | 🟢 Low | 4 | Progress queries |
| Stress Pattern | 🔴 High | 1-2 | After mood logs |
| Activity Decline | 🟡 Moderate | 3 | Progress queries |
| Proven Solution | 🟢 Low | 4 | After negative mood |
| Health Patterns | 🟡 Moderate | 3 | After health logs |

---

## 🎯 Challenge Progress Insights

Always shown when user asks "How am I doing?":

- **Almost There** (80%+): "🔥 You're crushing it! Finish strong! 💪"
- **Making Progress** (30-80%): "Great momentum! Keep it up! 🚀"
- **Just Started** (<30%): "Every journey starts with a single step! 🌟"

Current demo user challenges:
- 7-Day Hydration Challenge: 53% ✅
- Mindfulness Week: 64% ✅
- Sleep Better Challenge: 73% ✅

---

## 🚀 Best Way to See Insights NOW

**Just type: "How am I doing?"**

This will immediately show:
- ✅ 31-day activity streak
- ✅ 28% activity improvement
- ✅ All 3 challenge progress bars
- ✅ Motivational message

No waiting, no restrictions! 🎉
