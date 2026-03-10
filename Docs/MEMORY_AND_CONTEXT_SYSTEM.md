# 🧠 Memory & Context System - Complete Deep Dive

## 📊 Overview: Three Types of Memory

MoodCapture uses a **3-layer memory system**:

```
1. USER HISTORY (Long-term, Database)
   └─ Activities, moods, preferences over 30+ days
   
2. CONVERSATION HISTORY (Short-term, In-memory)
   └─ Last 10-20 messages in current session
   
3. SEMANTIC MEMORY (Session, In-memory)
   └─ Meaning/focus of current conversation
```

---

## 🗄️ Layer 1: USER HISTORY (Database Storage)

### Where It's Saved:

**Database Tables:**
1. `user_activity_history` - Completed activities
2. `suggestion_history` - Shown/accepted suggestions
3. `moods` - Mood logs
4. `activities` - Activity logs (water, sleep, etc.)

### File: `user_history.py`

**Key Functions:**

#### 1. `save_activity_to_history()`
```python
def save_activity_to_history(
    user_id, activity_id, activity_name,
    mood_emoji, reason, completed,
    duration_minutes, user_rating,
    energy_before, energy_after,
    satisfaction_score, would_repeat
):
    # Saves to user_activity_history table
    INSERT INTO user_activity_history 
    (user_id, activity_id, activity_name, mood_emoji, reason,
     completed, duration_minutes, timestamp, day_of_week, time_of_day)
    VALUES (...)
```

**What's Stored:**
- Activity ID and name
- Mood and reason when activity was done
- Completion status
- Duration
- User ratings (1-5 stars)
- Energy levels (before/after)
- Timestamp, day of week, time of day

#### 2. `get_activity_stats()`
```python
def get_activity_stats(user_id, days=30):
    # Returns aggregated statistics:
    return {
        'activity_counts': {
            'meditation': {'name': 'Meditation', 'count': 15},
            'breathing': {'name': 'Breathing', 'count': 10}
        },
        'time_preferences': {
            'morning': {'meditation': 8, 'breathing': 5},
            'evening': {'meditation': 7}
        },
        'day_preferences': {
            'Monday': {'meditation': 3},
            'Tuesday': {'breathing': 2}
        },
        'reason_preferences': {
            'work stress': {'breathing': 5, 'meditation': 3},
            'anxiety': {'meditation': 4}
        }
    }
```

#### 3. `get_recent_activities()`
```python
def get_recent_activities(user_id, limit=5):
    # Returns last 5 completed activities
    return [
        {'activity_id': 'meditation', 'activity_name': 'Meditation', 'timestamp': '...'},
        {'activity_id': 'breathing', 'activity_name': 'Breathing', 'timestamp': '...'}
    ]
```

---

## 💬 Layer 2: CONVERSATION HISTORY (In-Memory)

### Where It's Stored:

**File:** `unified_state.py`
**Class:** `WorkflowState`
**Attribute:** `conversation_history: List[Dict[str, str]]`

### Structure:

```python
conversation_history = [
    {'role': 'user', 'content': "I'm feeling stressed"},
    {'role': 'assistant', 'content': "I understand. What's causing the stress?"},
    {'role': 'user', 'content': "Work deadlines"},
    {'role': 'assistant', 'content': "Here are some activities..."}
]
```

### Key Methods:

#### 1. `add_message()`
```python
def add_message(self, role: str, content: str):
    """Add message to conversation history"""
    self.conversation_history.append({
        'role': role,
        'content': content
    })
    # Keep only last 20 messages (10 exchanges)
    if len(self.conversation_history) > 20:
        self.conversation_history = self.conversation_history[-20:]
```

#### 2. `get_conversation_history()`
```python
def get_conversation_history(self, limit: int = 10):
    """Get recent conversation history"""
    return self.conversation_history[-limit:]
```

### Persistence:

**On Login:**
```python
# chat_engine_workflow.py line 82-97
if len(workflow_state.conversation_history) == 0:
    # Load from database
    db_messages = chat_repo.get_recent_messages(user_id, limit=10)
    for msg in db_messages:
        workflow_state.conversation_history.append({
            'role': 'user' if msg['sender'] == 'user' else 'assistant',
            'content': msg['message']
        })
```

**On Each Message:**
```python
# chat_engine_workflow.py line 104-105
workflow_state.add_message('user', message)
# ... process ...
workflow_state.add_message('assistant', response.message)
```

---

## 🎯 Layer 3: SEMANTIC MEMORY (Session Summary)

### Where It's Stored:

**File:** `session_summary.py`
**Class:** `SessionSummary`
**Part of:** `WorkflowState.session_summary`

### Purpose:

**NOT** raw messages, but **MEANING**:
- What is the user focused on?
- What are their preferences?
- What's the current context?

### Structure:

```python
class SessionSummary:
    current_focus: Optional[str]  # "hydration", "mood", "sleep", etc.
    preferences: Dict[str, str]   # {"water_unit": "glasses"}
    last_updated: datetime
```

### Key Methods:

#### 1. `set_focus()`
```python
def set_focus(self, focus: Optional[str]):
    """Set current conversation focus"""
    # Valid values: "hydration", "mood", "sleep", "exercise", "weight"
    self.current_focus = focus
    self.last_updated = datetime.now()
```

#### 2. `set_preference()`
```python
def set_preference(self, key: str, value: str):
    """Set user preference"""
    # Example: preferences["water_unit"] = "glasses"
    self.preferences[key] = value
```

#### 3. `to_prompt()` - **CRITICAL FOR LLM**
```python
def to_prompt(self) -> str:
    """Generate natural language summary for LLM (max 150 chars)"""
    
    # Example output:
    # "The user is focused on hydration tracking and prefers logging water in glasses."
    
    parts = []
    
    if self.current_focus:
        focus_text = {
            "hydration": "hydration tracking",
            "mood": "mood logging",
            "sleep": "sleep tracking"
        }.get(self.current_focus)
        parts.append(f"The user is focused on {focus_text}")
    
    if self.preferences:
        if "water_unit" in self.preferences:
            parts.append(f"prefers logging water in {self.preferences['water_unit']}")
    
    return ". ".join(parts) + "."
```

#### 4. `is_stale()` & `clear_if_stale()`
```python
def is_stale(self) -> bool:
    """Check if summary is older than 1 hour"""
    return (datetime.now() - self.last_updated) > timedelta(hours=1)

def clear_if_stale(self):
    """Clear focus if stale, keep preferences"""
    if self.is_stale():
        self.current_focus = None
        # Preferences kept - assumed stable
```

---

## 🔄 Complete Flow: How Context is Built and Passed to LLM

### Step-by-Step Process:

```
User Message: "I'm stressed about work"
    ↓
1. LOAD WORKFLOW STATE (unified_state.py)
    ├─ conversation_history (last 20 messages)
    └─ session_summary (current focus + preferences)
    ↓
2. BUILD CONTEXT (context_builder_simple.py)
    ├─ Time context (hour, day, is_work_hours)
    ├─ User history (get_activity_stats, get_recent_activities)
    └─ Mood history (get_user_mood_logs)
    ↓
3. PREPARE LLM INPUT
    ├─ System message
    ├─ Semantic summary (session_summary.to_prompt())
    ├─ Conversation history (last 3-6 messages)
    └─ Current user message
    ↓
4. CALL LLM (llm_service.py)
    ├─ Detect intent
    ├─ Extract entities
    └─ Generate response
    ↓
5. SAVE TO MEMORY
    ├─ Add to conversation_history
    ├─ Update session_summary focus
    └─ Save to database (chat_repository)
```

---

## 📝 Example: Complete Context Building

### Scenario: User says "I'm stressed about work"

#### Step 1: Load Workflow State
```python
workflow_state = get_workflow_state(user_id=1)

# Contains:
workflow_state.conversation_history = [
    {'role': 'user', 'content': 'Hello'},
    {'role': 'assistant', 'content': 'Hi! How are you?'},
    {'role': 'user', 'content': "I'm stressed about work"}
]

workflow_state.session_summary.current_focus = "mood"
workflow_state.session_summary.preferences = {}
```

#### Step 2: Build Context
```python
context = build_context(user_id=1)

# Returns:
{
    # Time context
    'hour': 14,
    'day_of_week': 'Monday',
    'is_weekend': False,
    'is_work_hours': True,
    'time_period': 'afternoon',
    
    # User history
    'has_activity_history': True,
    'favorite_activities': [
        {'id': 'meditation', 'name': 'Meditation', 'count': 15},
        {'id': 'breathing', 'name': 'Breathing', 'count': 10}
    ],
    'recent_activities': [
        {'activity_id': 'meditation', 'timestamp': '2026-03-03 09:00:00'}
    ],
    'time_preferences': {
        'morning': {'meditation': 8},
        'afternoon': {'breathing': 5}
    },
    'reason_preferences': {
        'work stress': {'breathing': 5, 'meditation': 3}
    },
    
    # Mood history
    'has_mood_history': True,
    'recent_mood_trend': 'negative'
}
```

#### Step 3: Prepare LLM Prompt
```python
# Build messages for LLM
messages = []

# 1. System message
messages.append({
    'role': 'system',
    'content': 'You are a supportive wellness assistant.'
})

# 2. Semantic summary
summary = workflow_state.session_summary.to_prompt()
if summary:
    messages.append({
        'role': 'system',
        'content': f"Context: {summary}"
    })
    # Output: "Context: The user is focused on mood logging."

# 3. Conversation history (last 3 messages)
history = workflow_state.get_conversation_history(limit=3)
messages.extend(history)
# Adds:
# {'role': 'user', 'content': 'Hello'}
# {'role': 'assistant', 'content': 'Hi! How are you?'}

# 4. Current message
messages.append({
    'role': 'user',
    'content': "I'm stressed about work"
})

# Final messages array:
[
    {'role': 'system', 'content': 'You are a supportive wellness assistant.'},
    {'role': 'system', 'content': 'Context: The user is focused on mood logging.'},
    {'role': 'user', 'content': 'Hello'},
    {'role': 'assistant', 'content': 'Hi! How are you?'},
    {'role': 'user', 'content': "I'm stressed about work"}
]
```

#### Step 4: Call LLM
```python
llm_service = get_llm_service()
response = llm_service.call(
    messages=messages,
    temperature=0.3,
    max_tokens=100
)

# LLM has access to:
# - System role (wellness assistant)
# - Semantic context (focused on mood logging)
# - Recent conversation (Hello exchange)
# - Current message (stressed about work)
# - User history (via context, used by smart_suggestions)
```

#### Step 5: Save to Memory
```python
# 1. Add to conversation history
workflow_state.add_message('assistant', response)

# 2. Update semantic summary
workflow_state.session_summary.set_focus('mood')

# 3. Save to database
chat_repo.save_message(user_id, 'assistant', response)
```

---

## 🎯 How Each Memory Layer is Used

### USER HISTORY (Database)
**Used by:**
- `smart_suggestions.py` - Personalization scoring
- `context_builder_simple.py` - Building context
- `intelligent_suggestions.py` - Activity recommendations

**Example:**
```python
# In smart_suggestions.py
stats = get_activity_stats(user_id, days=30)
user_pref_score = stats['activity_counts'].get(activity_id, {}).get('count', 0) / 10
```

---

### CONVERSATION HISTORY (In-Memory)
**Used by:**
- `llm_intent_detector.py` - Intent detection with context
- `llm_service.py` - Generating contextual responses
- `activity_workflow.py` - Understanding multi-turn conversations

**Example:**
```python
# In llm_intent_detector.py
history = workflow_state.get_conversation_history(limit=6)
llm_service.detect_intent(message, conversation_history=history)
```

---

### SEMANTIC MEMORY (Session Summary)
**Used by:**
- `activity_workflow.py` - Cancellation detection
- `context_detector.py` - Determining current topic
- LLM prompts - Grounding with meaning

**Example:**
```python
# In activity_workflow.py
summary_text = state.session_summary.to_prompt()
if summary_text:
    messages.append({'role': 'system', 'content': f"Context: {summary_text}"})
```

---

## 📊 Memory Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ SEMANTIC MEMORY (Session Summary)                          │
│ - Current focus: "mood"                                     │
│ - Preferences: {"water_unit": "glasses"}                    │
│ - Lifespan: 1 hour                                          │
│ - Purpose: Grounding, consistency                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CONVERSATION HISTORY (In-Memory)                           │
│ - Last 10-20 messages                                       │
│ - Lifespan: Current session                                 │
│ - Purpose: Context, multi-turn conversations                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ USER HISTORY (Database)                                     │
│ - Activities, moods, preferences                            │
│ - Lifespan: 30+ days                                        │
│ - Purpose: Personalization, patterns                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Files Summary

| File | Purpose | Memory Type |
|------|---------|-------------|
| `user_history.py` | Save/load activity history | Database (long-term) |
| `unified_state.py` | Manage conversation state | In-memory (session) |
| `session_summary.py` | Semantic memory | In-memory (session) |
| `context_builder_simple.py` | Build context for LLM | Aggregates all 3 |
| `llm_service.py` | Call OpenAI with context | Uses all 3 |
| `chat_engine_workflow.py` | Orchestrate memory flow | Coordinates all 3 |

---

## 💡 Design Philosophy

### Why 3 Layers?

1. **USER HISTORY (Database)**
   - Persistent across sessions
   - Used for personalization
   - Expensive to query

2. **CONVERSATION HISTORY (In-Memory)**
   - Fast access
   - Recent context
   - Cleared on logout

3. **SEMANTIC MEMORY (Session Summary)**
   - Compressed meaning
   - Reduces token usage
   - Prevents drift

### Benefits:

✅ **Efficiency** - Don't send entire history to LLM
✅ **Relevance** - Recent messages + semantic meaning
✅ **Personalization** - Long-term patterns from database
✅ **Consistency** - Semantic summary prevents drift
✅ **Token optimization** - Max 150 chars for summary

---

## 🎓 Summary

### Where User History is Saved:
- **Database:** `user_activity_history` table
- **File:** `user_history.py`
- **Function:** `save_activity_to_history()`

### How Context is Built:
- **File:** `context_builder_simple.py`
- **Function:** `build_context()`
- **Sources:** User history + time + mood logs

### How Semantic Memory is Created:
- **File:** `session_summary.py`
- **Class:** `SessionSummary`
- **Method:** `to_prompt()` - Converts to natural language

### How It's Passed to LLM:
- **File:** `llm_service.py`
- **Method:** `call(messages=...)`
- **Format:** Array of message objects with roles

### Complete Flow:
```
User Message
    ↓
Load State (conversation_history + session_summary)
    ↓
Build Context (user_history + time + mood)
    ↓
Prepare Messages (system + summary + history + current)
    ↓
Call LLM
    ↓
Save Response (conversation_history + database)
```

**Every piece of context is carefully curated to give LLM the right information without overwhelming it!**

---

**Want me to explain any specific part in more detail?** 🚀
