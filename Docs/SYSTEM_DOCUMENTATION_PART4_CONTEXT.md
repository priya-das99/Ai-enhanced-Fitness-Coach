# MoodCapture System Documentation - Part 4: Context-Aware Chat & Memory

## 5. Context-Aware Chat System

### Memory Architecture

The system uses **3-layer memory system**:

```
Layer 1: Short-term (Session Memory) - Current conversation
Layer 2: Medium-term (Recent History) - Last 10 messages
Layer 3: Long-term (User Profile) - Behavioral patterns
```

### Layer 1: Session Memory (In-Memory)

**File**: `backend/app/services/session_tracker.py`

```python
# Stored in memory during active session
session_state = {
    "user_id": 18,
    "current_workflow": "mood_logging",
    "awaiting_input": "mood_reason",
    "temp_data": {
        "mood_emoji": "😊",
        "partial_data": {}
    },
    "last_activity": "2026-02-27 10:00:00"
}
```

**Purpose**: Track current conversation state
**Lifetime**: Until session ends (30 min timeout)
**Storage**: Python dictionary in memory

### Layer 2: Recent History (Database)

**Table**: `chat_messages`
**File**: `backend/app/repositories/chat_repository.py`

```python
def get_conversation_history(user_id: int, limit: int = 10):
    """
    Retrieves last N messages for context
    
    Used for:
    - Understanding conversation flow
    - Resolving ambiguous references ("it", "that")
    - Maintaining conversation continuity
    """
    
    # Query
    SELECT message, sender, timestamp, metadata
    FROM chat_messages
    WHERE user_id = ?
    ORDER BY timestamp DESC
    LIMIT 10
```

**Example Context**:
```python
history = [
    {"sender": "user", "message": "I'm feeling stressed"},
    {"sender": "bot", "message": "What's causing the stress?"},
    {"sender": "user", "message": "Work deadlines"},
    {"sender": "bot", "message": "Here are some activities..."},
    {"sender": "user", "message": "Show me the first one"}  # "first one" needs context
]
```

### Layer 3: Long-term Memory (Aggregated Data)

**Tables**: 
- `user_behavior_metrics` - Behavioral patterns
- `user_activity_history` - Past activities
- `mood_logs` - Mood history

**File**: `backend/app/services/user_data_analyzer.py`

```python
class UserDataAnalyzer:
    def get_user_profile(user_id: int):
        """
        Builds comprehensive user profile
        
        Returns:
        {
            "mood_patterns": {
                "most_common_mood": "😊",
                "stress_triggers": ["work", "family"],
                "best_time_for_activities": "evening"
            },
            "activity_preferences": {
                "favorite_activities": ["meditation", "yoga"],
                "completion_rate": 0.75,
                "preferred_duration": "short"
            },
            "behavioral_metrics": {
                "avg_sleep": 7.5,
                "avg_water": 6.0,
                "exercise_frequency": 3
            }
        }
        """
```

### Context-Aware Response Engine

**File**: `backend/app/services/context_aware_response_engine.py`

```python
class ContextAwareResponseEngine:
    def generate_response(user_id, message, history):
        """
        Generates contextually appropriate responses
        
        Steps:
        1. Load user profile (long-term memory)
        2. Analyze recent history (medium-term)
        3. Check session state (short-term)
        4. Detect context requirements
        5. Generate personalized response
        """
        
        # Example: User says "yes"
        if message.lower() == "yes":
            # Check what we asked
            last_bot_message = history[-1]
            
            if "Would you like suggestions?" in last_bot_message:
                return get_suggestions(user_id)
            elif "Want to log mood?" in last_bot_message:
                return show_mood_selector()
            elif "Continue challenge?" in last_bot_message:
                return show_challenge_progress()
```

### Context Detection

**File**: `backend/chat_assistant/context_detector.py`

```python
def detect_context_needs(message: str, history: list) -> dict:
    """
    Identifies what context is needed
    
    Detects:
    - Pronouns: "it", "that", "this", "them"
    - References: "the first one", "last activity"
    - Implicit context: "yes", "no", "sure"
    - Follow-ups: "tell me more", "what else"
    """
    
    context_signals = {
        "needs_reference": ["it", "that", "this", "them"],
        "needs_confirmation": ["yes", "no", "sure", "okay"],
        "needs_history": ["again", "last time", "before"],
        "needs_clarification": ["which", "what", "how"]
    }
```

### Memory Usage Optimization

**Strategy 1: Selective Context Loading**
```python
# Don't load everything for every message
if is_simple_command(message):
    # "log mood" - no context needed
    context = None
elif needs_recent_context(message):
    # "yes" - load last 3 messages
    context = get_history(limit=3)
elif needs_full_context(message):
    # "how am I doing?" - load full profile
    context = get_full_profile(user_id)
```

**Strategy 2: Context Caching**
```python
# Cache user profile for 5 minutes
@cache(ttl=300)
def get_user_profile(user_id):
    # Expensive query
    return build_profile(user_id)
```

**Strategy 3: Lazy Loading**
```python
# Only load what's needed
def process_message(user_id, message):
    # Always load
    basic_context = get_session_state(user_id)
    
    # Load on demand
    if needs_history:
        history = get_conversation_history(user_id)
    
    if needs_profile:
        profile = get_user_profile(user_id)
```

### Context-Aware Features

#### 1. Pronoun Resolution
```python
User: "I want to try meditation"
Bot: "Great! Here's a 10-minute guided meditation"
User: "Start it"  # "it" = meditation

# System resolves "it" using context
last_suggestion = get_last_suggestion(user_id)
start_activity(last_suggestion)
```

#### 2. Implicit Confirmation
```python
Bot: "Would you like to log your mood?"
User: "sure"  # Implicit yes

# System understands context
if last_question_was_yes_no():
    treat_as_confirmation()
```

#### 3. Conversation Continuity
```python
User: "I'm stressed"
Bot: "What's causing the stress?"
User: "Work"  # Continues previous topic

# System maintains topic
current_topic = get_active_topic(user_id)  # "stress"
save_mood_with_reason(user_id, "😟", "work")
```

### Files Involved

**Core Context System**:
- `backend/app/services/context_aware_response_engine.py`
- `backend/chat_assistant/context_detector.py`
- `backend/app/services/session_tracker.py`

**Memory Management**:
- `backend/app/repositories/chat_repository.py`
- `backend/app/services/user_data_analyzer.py`
- `backend/chat_assistant/user_history.py`

**State Management**:
- `backend/chat_assistant/conversation_state.py`
- `backend/chat_assistant/unified_state.py`
