# LLM API Call Locations - Complete Reference

## Overview
This document lists ALL locations in the codebase where LLM (OpenAI) API calls are made.

---

## 🎯 User-Facing API Endpoints That Trigger LLM

### 1. POST `/api/v1/chat/message` 
**File**: `backend/app/api/v1/endpoints/chat.py`

**When LLM is Called**:
- When user sends ambiguous messages that can't be handled by rules
- When generating conversational responses
- When detecting complex intents

**Flow**:
```
User sends message
  ↓
ChatService.process_message()
  ↓
WorkflowRegistry.route_message()
  ↓
[One of the workflows below calls LLM]
```

---

## 📍 Code Locations That Call LLM

### Location 1: Intent Detection
**File**: `backend/chat_assistant/llm_intent_detector.py`
**Function**: `detect_intent_with_llm()`
**When**: When rule-based intent detection fails
**Call Type**: `intent_detection`

```python
# Line ~50
response = llm_service.call(
    prompt=f"User said: '{message}'. Detect intent...",
    max_tokens=20,
    temperature=0.1
)
```

**Triggered By**:
- Ambiguous messages like "I want to track something"
- Complex queries like "How am I doing?"
- Context-dependent messages like "yes" or "sure"

---

### Location 2: Mood Extraction
**File**: `backend/chat_assistant/mood_extractor.py`
**Function**: `extract_mood_with_llm()`
**When**: When extracting mood from text
**Call Type**: `mood_extraction`

```python
# Line ~115
response = llm_service.call(
    prompt=f"Extract mood from: '{message}'",
    max_tokens=20,
    temperature=0.1
)
```

**Triggered By**:
- User says "I'm feeling stressed"
- User describes emotional state in text

---

### Location 3: Mood Workflow Responses
**File**: `backend/chat_assistant/mood_workflow.py`
**Function**: `handle()` - Multiple locations
**When**: Generating empathetic responses
**Call Type**: `response_generation`

```python
# Line ~433
msg = llm_service.call(
    prompt=f"User is feeling {mood}. Respond empathetically...",
    system_message="You are a supportive wellness assistant.",
    max_tokens=50,
    temperature=0.7
)
```

**Triggered By**:
- After user logs mood
- When asking follow-up questions
- When providing encouragement

---

### Location 4: Activity Workflow Responses
**File**: `backend/chat_assistant/activity_workflow.py`
**Function**: `handle()` - Multiple locations
**When**: Responding to activity logging
**Call Type**: `response_generation`

```python
# Line ~813
message = llm_service.call(
    prompt=f"User logged {activity}. Respond encouragingly...",
    system_message="You are a supportive wellness assistant.",
    max_tokens=50,
    temperature=0.7
)
```

**Triggered By**:
- User logs water, sleep, exercise
- User completes an activity
- User asks about activities

---

### Location 5: General Conversation
**File**: `backend/chat_assistant/domain/llm/response_phraser.py`
**Function**: `phrase_general_response()`
**When**: Handling general chat
**Call Type**: `response_generation`

```python
# Line ~82
text = llm_service.call(
    prompt=user_message,
    system_message="You are MoodCapture, a calm and supportive wellness assistant.",
    max_tokens=100,
    temperature=0.7
)
```

**Triggered By**:
- User asks questions
- User makes general statements
- Fallback for unhandled messages

---

### Location 6: Activity Chat Handler
**File**: `backend/chat_assistant/activity_chat_handler.py`
**Function**: Multiple functions
**When**: Responding to activity-related queries
**Call Type**: `response_generation`

```python
# Line ~155
response_text = llm_service.call(
    prompt=f"User asked about {activity}...",
    max_tokens=50,
    temperature=0.7
)
```

**Triggered By**:
- User asks "What activities can help?"
- User requests suggestions
- User asks about specific activities

---

### Location 7: Insight Generation (Background Job)
**File**: `backend/app/services/llm_insight_generator.py`
**Function**: `generate_insights()`
**When**: Daily insight generation (cron job)
**Call Type**: `insight_generation`

```python
# Line ~53
message = llm_service.call(
    prompt=f"Generate insights from user data: {patterns}",
    temperature=0.7,
    max_tokens=200
)
```

**Triggered By**:
- Daily cron job (midnight)
- Manual insight generation
- On-demand analysis

---

### Location 8: Smart Suggestions (Legacy)
**File**: `backend/chat_assistant/smart_suggestions.py`
**Function**: `generate_suggestions_with_llm()`
**When**: Generating activity suggestions (rarely used)
**Call Type**: `suggestion_generation`

```python
# Line ~980
response = llm_service.call(
    prompt=f"Suggest activities for mood: {mood}",
    max_tokens=100,
    temperature=0.7
)
```

**Triggered By**:
- Fallback when rule-based suggestions fail
- Complex mood/reason combinations

---

### Location 9: Response Phrasing (Legacy)
**File**: `backend/chat_assistant/response_phrasing.py`
**Function**: `phrase_response()`
**When**: Phrasing acknowledgments
**Call Type**: `response_generation`

```python
# Line ~71
response = llm_service.call(
    prompt=f"Acknowledge: {message}",
    max_tokens=30,
    temperature=0.7
)
```

**Triggered By**:
- Acknowledging user actions
- Providing feedback

---

## 📊 LLM Call Frequency by Endpoint

### High Frequency (Every Request)
None - LLM is only called when needed

### Medium Frequency (30-40% of requests)
1. **POST `/api/v1/chat/message`** with ambiguous messages
   - Intent detection: ~30% of messages
   - Response generation: ~10% of messages

### Low Frequency (Scheduled)
1. **Insight Generation** (Background)
   - Once per day per active user
   - Typically runs at midnight

---

## 🔍 How to Track Which API Triggered LLM

### Method 1: Check Real-Time Monitor
```bash
python backend/monitor_llm_realtime.py
```

Shows:
- Timestamp
- User ID
- Call type
- Which feature triggered it

### Method 2: Check Database
```sql
SELECT 
    user_id,
    call_type,
    timestamp,
    context_data
FROM llm_usage_log
ORDER BY timestamp DESC
LIMIT 20;
```

### Method 3: Check Logs
```bash
# LLM calls are logged with this format:
# 🤖 LLM Call: {call_type} | Tokens: {input}→{output} | Cost: ${cost}

grep "🤖 LLM Call" backend/logs/app.log
```

---

## 🎯 Call Type Mapping

| Call Type | Triggered By | File Location |
|-----------|-------------|---------------|
| `intent_detection` | Ambiguous user messages | `llm_intent_detector.py` |
| `mood_extraction` | Mood-related text | `mood_extractor.py` |
| `response_generation` | Need conversational response | Multiple workflows |
| `insight_generation` | Daily cron job | `llm_insight_generator.py` |
| `suggestion_generation` | Complex suggestion needs | `smart_suggestions.py` |

---

## 🚫 What DOESN'T Call LLM

These are handled by rules only:

1. **Simple Commands**
   - "log mood"
   - "log water"
   - "show challenges"
   - Button clicks

2. **Emoji Selection**
   - Mood emoji picker
   - Direct emoji input

3. **Keyword Matches**
   - "I'm feeling stressed" → Detected by keyword
   - "I want to exercise" → Detected by keyword

4. **Structured Data**
   - Activity logging with numbers
   - Challenge progress updates

---

## 💡 Optimization Tips

### Reduce LLM Calls

1. **Improve Rule-Based Detection**
```python
# Add more keywords to avoid LLM
MOOD_KEYWORDS = ["stressed", "anxious", "happy", "sad", ...]
```

2. **Cache Common Queries**
```python
@lru_cache(maxsize=100)
def get_intent(message):
    return llm_service.call(...)
```

3. **Use Structured Responses**
```python
# Instead of LLM for simple acknowledgments
ACKNOWLEDGMENTS = {
    "water": "Great! Staying hydrated 💧",
    "exercise": "Nice work! 💪",
}
```

---

## 📈 Expected LLM Usage

### Per User Per Day
- Messages sent: ~15
- LLM calls: ~5 (33%)
- Tokens used: ~2,500
- Cost: ~$0.002

### Per 1000 Users Per Month
- Total calls: ~150,000
- Total tokens: ~75M
- Total cost: ~$75-100

---

## 🔧 Adding New LLM Calls

If you need to add a new LLM call:

```python
from chat_assistant.llm_service_with_tracking import get_tracked_llm_service

llm = get_tracked_llm_service()

response = llm.call(
    prompt="Your prompt here",
    system_message="You are a helpful assistant",
    max_tokens=100,
    temperature=0.7,
    user_id=user_id,  # For tracking
    call_type="your_feature_name"  # For analytics
)
```

This automatically tracks:
- Token usage
- Cost
- Latency
- Success/failure

---

## Summary

**Total LLM Call Locations**: 9 main locations
**User-Facing APIs**: 1 (`/api/v1/chat/message`)
**Background Jobs**: 1 (Daily insights)
**Average LLM Usage**: 30-40% of user messages
**Primary Use Cases**: Intent detection, response generation, insights

All calls are now tracked automatically with the token tracking system!
