# Complete Chat Assistant Test Guide

## What Your Chat Assistant Can Do

Your chat assistant is a comprehensive wellness companion with these capabilities:

### 1. **Activity Suggestions (NEW - LLM-Based)**
- Understands ANY wellness query without keywords
- Provides personalized activity suggestions
- Handles weight, nutrition, exercise, sleep, stress, anxiety, etc.

### 2. **Mood Logging**
- Track emotional state with emoji selector
- Ask follow-up questions about mood reasons
- Provide contextual suggestions based on mood

### 3. **Activity Logging**
- Log water intake
- Log sleep duration
- Log exercise/workouts
- Log weight
- Log meals

### 4. **Challenge Management**
- View active challenges
- Create new challenges
- Track challenge progress
- Get challenge-specific suggestions

### 5. **Smart Suggestions**
- Personalized based on user history
- Context-aware (time of day, recent activities)
- Cooldown system (don't repeat suggestions)
- Weighted scoring (behavior + recency + diversity)

### 6. **Conversation Features**
- Natural language understanding
- Context-aware responses
- Depth tracking (prevents info loops)
- Safety guardrails (stays on-topic)
- Memory (remembers conversation context)

---

## Test Cases - One by One

### TEST 1: Weight Management Query (NEW FIX)
**What it tests:** LLM-based reason extraction for weight-related queries

**Steps:**
1. Login to the app
2. Type: `"im gaining weight how to controll it"`
3. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with weight_management:"
✅ Shows buttons:
   - Track Your Meals
   - Plan Healthy Meals
   - Cardio Workout
   - Strength Training
   - Portion Control
   
❌ Should NOT show: Breathing Exercise, Meditation, Stretching
```

**What this proves:** System understands weight queries and suggests relevant activities

---

### TEST 2: Nutrition Query
**What it tests:** LLM understands nutrition/diet queries

**Steps:**
1. Type: `"want to eat healthier"`
2. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with nutrition:"
✅ Shows nutrition-related activities:
   - Healthy Snack Ideas
   - Track Your Meals
   - Meal Planning
```

---

### TEST 3: Sleep Query
**What it tests:** LLM understands sleep-related queries

**Steps:**
1. Type: `"cant sleep at night"`
2. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with sleep:"
✅ Shows sleep-related activities:
   - Power Nap
   - Meditation
   - Breathing Exercise
```

---

### TEST 4: Stress Query
**What it tests:** LLM understands stress queries

**Steps:**
1. Type: `"feeling really stressed"`
2. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with stress:"
✅ Shows stress-relief activities:
   - Breathing Exercise
   - Meditation
   - Take a Break
   - Short Walk
```

---

### TEST 5: Exercise/Fitness Query
**What it tests:** LLM understands fitness goals

**Steps:**
1. Type: `"need to build muscle"`
2. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with exercise:"
✅ Shows exercise activities:
   - Strength Training
   - 7 Minute Workout
   - Squats Workout
```

---

### TEST 6: Energy Query
**What it tests:** LLM understands energy/fatigue queries

**Steps:**
1. Type: `"no energy in the mornings"`
2. Send message

**Expected Result:**
```
✅ Bot responds: "Here are some activities that might help with energy:"
✅ Shows energy-boosting activities:
   - Short Walk
   - Hydrate
   - Power Nap
   - Stretching
```

---

### TEST 7: Mood Logging Flow
**What it tests:** Complete mood logging workflow

**Steps:**
1. Click "Log Mood" button (or type "log mood")
2. Select emoji: 😟 (worried)
3. Bot asks: "What's making you feel this way?"
4. Type: `"work stress"`
5. Bot provides suggestions

**Expected Result:**
```
✅ Emoji selector appears
✅ Bot asks follow-up question
✅ Bot provides work-stress specific suggestions
✅ Mood is saved to database
```

---

### TEST 8: Activity Logging - Water
**What it tests:** Activity logging workflow

**Steps:**
1. Click "Log Water" button (or type "log water")
2. Bot asks: "How many glasses?"
3. Type: `"2"`
4. Bot confirms

**Expected Result:**
```
✅ Bot asks for quantity
✅ Bot confirms: "Great! Logged 2 glasses of water"
✅ Activity saved to database
```

---

### TEST 9: Activity Logging - Sleep
**What it tests:** Sleep logging workflow

**Steps:**
1. Type: `"log sleep"`
2. Bot asks: "How many hours did you sleep?"
3. Type: `"7"`
4. Bot confirms

**Expected Result:**
```
✅ Bot asks for hours
✅ Bot confirms: "Got it! Logged 7 hours of sleep"
✅ Sleep data saved
```

---

### TEST 10: Challenge Query
**What it tests:** Challenge management

**Steps:**
1. Type: `"view challenges"` or click "View Challenges"
2. Bot shows active challenges

**Expected Result:**
```
✅ Bot lists active challenges
✅ Shows progress for each challenge
✅ Offers to create new challenge if none exist
```

---

### TEST 11: Personalization Test
**What it tests:** Suggestions adapt to user history

**Steps:**
1. Log several water activities over time
2. Type: `"what should i do"`
3. Check suggestions

**Expected Result:**
```
✅ Water-related activities ranked higher
✅ Activities user frequently does appear first
✅ Cooldown prevents recent suggestions from repeating
```

---

### TEST 12: Context Awareness
**What it tests:** Bot remembers conversation context

**Steps:**
1. Type: `"im feeling stressed"`
2. Bot suggests activities
3. Type: `"yes"` (agreeing to try an activity)
4. Bot responds contextually

**Expected Result:**
```
✅ Bot understands "yes" refers to trying an activity
✅ Bot encourages the activity
✅ Bot asks follow-up: "How are you feeling now?"
```

---

### TEST 13: Depth Tracking
**What it tests:** Prevents infinite information loops

**Steps:**
1. Type: `"tell me about breathing"`
2. Bot explains
3. Type: `"tell me more about breathing"`
4. Bot explains more
5. Type: `"more about breathing"`
6. Bot nudges to action

**Expected Result:**
```
✅ After 3 informational responses about same topic
✅ Bot says: "Let's try it! Ready for a breathing exercise?"
✅ Shows action buttons instead of more info
```

---

### TEST 14: Safety Guardrails
**What it tests:** Bot stays on wellness topics

**Steps:**
1. Type: `"what's the weather today"`
2. Bot redirects

**Expected Result:**
```
✅ Bot says: "I'm designed to help with wellness and fitness"
✅ Bot offers wellness options
✅ Doesn't try to answer off-topic questions
```

---

### TEST 15: Rejection Tracking
**What it tests:** Bot stops suggesting after multiple rejections

**Steps:**
1. Bot suggests activities
2. Type: `"no thanks"`
3. Bot suggests again
4. Type: `"not interested"`
5. Bot stops suggesting

**Expected Result:**
```
✅ After 2 rejections, bot says: "No problem! I'm here if you need anything"
✅ Doesn't keep pushing suggestions
✅ Rejection count resets after some time
```

---

### TEST 16: Button Click Flow
**What it tests:** Clicking activity buttons works correctly

**Steps:**
1. Bot shows activity suggestions
2. Click "Breathing Exercise" button
3. Bot responds

**Expected Result:**
```
✅ Bot encourages: "Great choice! Take a few deep breaths..."
✅ Bot asks: "How are you feeling now?"
✅ Shows emoji selector for mood check
```

---

### TEST 17: Greeting Flow
**What it tests:** Initial conversation

**Steps:**
1. Fresh login
2. Type: `"hi"`

**Expected Result:**
```
✅ Bot greets warmly
✅ Bot offers to help with mood/activity tracking
✅ Shows action buttons (Log Mood, Log Water, etc.)
```

---

### TEST 18: Help Query
**What it tests:** User asks what bot can do

**Steps:**
1. Type: `"what can you do"`

**Expected Result:**
```
✅ Bot explains capabilities:
   - Track mood and emotions
   - Log activities (water, sleep, exercise)
   - Get personalized suggestions
   - Monitor challenges
✅ Shows action buttons
```

---

### TEST 19: Edge Case - Typos
**What it tests:** LLM handles typos gracefully

**Steps:**
1. Type: `"im gainin wieght how too controll itt"`
2. Send message

**Expected Result:**
```
✅ Bot still understands: weight_management
✅ Shows relevant weight activities
✅ Doesn't get confused by typos
```

---

### TEST 20: Edge Case - Multiple Concerns
**What it tests:** LLM picks primary concern

**Steps:**
1. Type: `"im stressed about my weight and cant sleep"`
2. Send message

**Expected Result:**
```
✅ Bot identifies primary concern (likely weight or stress)
✅ Shows relevant activities
✅ Doesn't get confused by multiple topics
```

---

## Quick Test Checklist

Run through these quickly to verify everything works:

```
□ Weight query → weight activities
□ Nutrition query → nutrition activities  
□ Sleep query → sleep activities
□ Stress query → stress activities
□ Exercise query → exercise activities
□ Mood logging → emoji selector → follow-up
□ Water logging → quantity question → confirmation
□ Challenge view → shows challenges
□ Button clicks → appropriate responses
□ Context awareness → "yes" understood correctly
□ Safety guardrails → off-topic redirected
□ Personalization → frequent activities ranked higher
```

---

## How to Test

### Option 1: Manual Testing (Recommended)
1. Start your backend: `python start_no_reload.py`
2. Open frontend: `login.html` in browser
3. Login with: username=`ankur`, password=`123456`
4. Go through test cases one by one
5. Check responses match expected results

### Option 2: Automated API Testing
```bash
cd backend
python test_llm_reason_extraction.py  # Tests LLM extraction
python test_complete_flow.py          # Tests full workflows
```

---

## What to Look For

### ✅ Success Indicators
- Relevant activity suggestions for each query type
- Bot understands natural language (not just keywords)
- Personalization based on user history
- Context-aware responses
- Smooth conversation flow

### ❌ Failure Indicators
- Generic activities for specific queries (breathing for weight)
- Bot confused by typos or variations
- Repetitive suggestions
- Off-topic responses
- Broken conversation flow

---

## Summary of Capabilities

| Feature | Status | Test Case |
|---------|--------|-----------|
| Weight queries | ✅ NEW | Test 1 |
| Nutrition queries | ✅ NEW | Test 2 |
| Sleep queries | ✅ | Test 3 |
| Stress queries | ✅ | Test 4 |
| Exercise queries | ✅ NEW | Test 5 |
| Energy queries | ✅ | Test 6 |
| Mood logging | ✅ | Test 7 |
| Activity logging | ✅ | Test 8-9 |
| Challenges | ✅ | Test 10 |
| Personalization | ✅ | Test 11 |
| Context awareness | ✅ | Test 12 |
| Depth tracking | ✅ | Test 13 |
| Safety guardrails | ✅ | Test 14 |
| Rejection tracking | ✅ | Test 15 |
| Button interactions | ✅ | Test 16 |
| Greetings | ✅ | Test 17 |
| Help queries | ✅ | Test 18 |
| Typo handling | ✅ NEW | Test 19 |
| Multiple concerns | ✅ NEW | Test 20 |

---

## Ready to Test?

Start with **Test 1** (Weight Management Query) - this is the one we just fixed!

Let me know which test you want to run first, and I'll guide you through it.
