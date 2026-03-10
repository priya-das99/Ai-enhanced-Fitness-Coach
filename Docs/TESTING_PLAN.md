# 🧪 MoodCapture Chat Assistant - Testing Plan

## 📋 Overview

This document outlines all implemented use cases and how to test them systematically.

---

## 🎯 Implemented Use Cases

### ✅ 1. MOOD LOGGING
**Workflow:** `MoodWorkflow`  
**Intents:** `mood_logging`, `log_mood`, `feeling`

**What it does:**
- User expresses their mood
- System detects mood emoji
- Asks for reason (if negative mood)
- Logs mood to database
- Provides empathetic response
- Suggests activities based on mood

**Test Cases:**

| # | User Input | Expected Behavior |
|---|------------|-------------------|
| 1.1 | "I'm feeling happy" | Detects 😊, logs mood, congratulates |
| 1.2 | "I'm stressed" | Detects 😰, asks for reason |
| 1.3 | "About work deadlines" | Logs reason, suggests stress-relief activities |
| 1.4 | "I feel sad" | Detects 😢, asks for reason, shows empathy |
| 1.5 | "😊" (emoji only) | Recognizes emoji, logs mood |

---

### ✅ 2. ACTIVITY LOGGING
**Workflow:** `ActivityWorkflow`  
**Intents:** `activity_logging`, `log_activity`, `track_activity`

**What it does:**
- Logs water intake
- Logs sleep hours
- Logs exercise/workouts
- Logs weight
- Updates challenge progress
- Provides encouragement

**Test Cases:**

| # | User Input | Expected Behavior |
|---|------------|-------------------|
| 2.1 | "I drank 8 glasses of water" | Logs water, updates hydration challenge |
| 2.2 | "I slept 7 hours" | Logs sleep, checks sleep challenge |
| 2.3 | "I did a 30 minute workout" | Logs exercise, updates exercise challenge |
| 2.4 | "Log water" | Asks "How many glasses?" |
| 2.5 | "8 glasses" | Logs the amount |
| 2.6 | "I weigh 70kg" | Logs weight |

---

### ✅ 3. CHALLENGES TRACKING
**Workflow:** `ChallengesWorkflow`  
**Intents:** `challenges`, `view_challenges`, `challenge_progress`

**What it does:**
- Shows active challenges
- Displays progress bars
- Shows points earned
- Provides motivation
- Suggests next actions

**Test Cases:**

| # | User Input | Expected Behavior |
|---|------------|-------------------|
| 3.1 | "How am I doing?" | Shows all challenges + progress + insights |
| 3.2 | "Show my challenges" | Lists active challenges with progress |
| 3.3 | "What challenges do I have?" | Shows challenge details |
| 3.4 | "My progress" | Shows progress with insights |
| 3.5 | "How's my meditation challenge?" | Shows specific challenge progress |

---

### ✅ 4. ACTIVITY QUERIES
**Workflow:** `ActivityQueryWorkflow`  
**Intents:** `activity_query`, `suggest_activity`, `what_should_i_do`

**What it does:**
- Suggests activities based on mood
- Recommends wellness content
- Provides personalized suggestions
- Considers user history

**Test Cases:**

| # | User Input | Expected Behavior |
|---|------------|-------------------|
| 4.1 | "What should I do?" | Suggests activities based on context |
| 4.2 | "I'm bored" | Suggests engaging activities |
| 4.3 | "Suggest something for stress" | Recommends stress-relief activities |
| 4.4 | "What can help me relax?" | Suggests relaxation activities |

---

### ✅ 5. GENERAL CONVERSATION
**Workflow:** `GeneralWorkflow`  
**Intents:** `greeting`, `general_chat`, `question`

**What it does:**
- Handles greetings
- Answers general questions
- Provides friendly responses
- Maintains conversation context

**Test Cases:**

| # | User Input | Expected Behavior |
|---|------------|-------------------|
| 5.1 | "Hello" | Friendly greeting response |
| 5.2 | "Hi" | Welcomes user |
| 5.3 | "How are you?" | Responds appropriately |
| 5.4 | "Thank you" | Acknowledges gratitude |
| 5.5 | "What can you do?" | Explains capabilities |

---

## 🔧 Testing Approach

### Phase 1: Unit Testing (Individual Workflows)
Test each workflow in isolation using Python scripts.

### Phase 2: Integration Testing (Full Flow)
Test complete user journeys through the UI.

### Phase 3: Edge Case Testing
Test error handling and unusual inputs.

---

## 📝 Test Execution Plan

### STEP 1: Verify Setup ✅
```bash
python check_demo_ready.py
```

**Expected:** All checks pass

---

### STEP 2: Test Mood Logging Workflow

**Script:** `test_mood_workflow.py`

```python
# Test 1: Happy mood
User: "I'm feeling happy"
Expected: Mood logged, positive response

# Test 2: Stressed mood
User: "I'm stressed"
Expected: Asks for reason

# Test 3: Provide reason
User: "About work"
Expected: Logs reason, suggests activities
```

**How to test:**
1. Run: `python backend/test_mood_workflow.py`
2. Or test via UI: Login → Type "I'm feeling happy"

---

### STEP 3: Test Activity Logging Workflow

**Script:** `test_activity_workflow.py`

```python
# Test 1: Water logging
User: "I drank 8 glasses of water"
Expected: Logs water, updates challenge

# Test 2: Sleep logging
User: "I slept 7 hours"
Expected: Logs sleep

# Test 3: Exercise logging
User: "I did a workout"
Expected: Logs exercise
```

**How to test:**
1. Run: `python backend/test_activity_workflow.py`
2. Or test via UI: Login → Type "I drank 8 glasses"

---

### STEP 4: Test Challenges Workflow

**Script:** `test_challenge_chat.py` (already exists)

```python
# Test 1: View challenges
User: "How am I doing?"
Expected: Shows challenges + progress + insights

# Test 2: List challenges
User: "Show my challenges"
Expected: Lists all active challenges
```

**How to test:**
1. Run: `python backend/test_challenge_chat.py`
2. Or test via UI: Login → Type "How am I doing?"

---

### STEP 5: Test Activity Queries

**Script:** `test_activity_queries.py`

```python
# Test 1: General query
User: "What should I do?"
Expected: Suggests activities

# Test 2: Specific query
User: "What can help me relax?"
Expected: Suggests relaxation activities
```

---

### STEP 6: Test General Conversation

**Script:** `test_general_workflow.py`

```python
# Test 1: Greeting
User: "Hello"
Expected: Friendly greeting

# Test 2: Question
User: "What can you do?"
Expected: Explains capabilities
```

---

### STEP 7: Test Full User Journey (UI)

**Journey 1: New User Experience**
1. Open app → See landing page ✅
2. Click "Get Started" → See login ✅
3. Login as demo → See chat interface ✅
4. Say "Hello" → Get greeting ✅
5. Say "I'm feeling happy" → Mood logged ✅
6. Say "I drank 8 glasses" → Activity logged ✅
7. Say "How am I doing?" → See challenges ✅

**Journey 2: Stressed User**
1. Login ✅
2. Say "I'm stressed" → Asked for reason ✅
3. Say "About work" → Get empathy + suggestions ✅
4. Click suggested activity → Activity logged ✅
5. Say "How am I doing?" → See progress ✅

---

## 🐛 Known Issues to Test

Based on your comment "some things don't work", let's identify what might be broken:

### Potential Issues:

1. **LLM Intent Detection**
   - May not always detect correct intent
   - Test: Try ambiguous messages

2. **Multi-turn Conversations**
   - State management between messages
   - Test: Start mood logging, then switch topics

3. **Button Actions**
   - Activity completion buttons
   - Test: Click buttons in UI

4. **Challenge Progress Updates**
   - May not update in real-time
   - Test: Log activity, check challenge progress

5. **Insights Display**
   - May not show when expected
   - Test: Ask "How am I doing?" multiple times

---

## 📊 Test Results Template

```
USE CASE: [Name]
TEST #: [Number]
INPUT: [User message]
EXPECTED: [Expected behavior]
ACTUAL: [What actually happened]
STATUS: ✅ PASS / ❌ FAIL
NOTES: [Any observations]
```

---

## 🚀 Next Steps

1. **Review this plan** - Confirm these are the use cases you want to test
2. **I'll create test scripts** - For each workflow
3. **Run tests systematically** - One use case at a time
4. **Document failures** - So we can fix them
5. **Retest after fixes** - Ensure everything works

---

## ❓ Questions Before We Start

1. Which use case should we test FIRST?
2. Do you want automated scripts or manual UI testing?
3. Are there specific scenarios that you know are broken?
4. Should we test with the demo user or create a fresh test user?

---

**Ready to start testing?** Let me know which use case to test first, and I'll create the test script!
