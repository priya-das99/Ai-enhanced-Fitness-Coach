# How Multi-Intent Works

## Overview

The system can handle messages with multiple intents like:
- "I drank 2 glasses of water, And I am feeling not happy"
- "I'm stressed about work and I drank 3 glasses of water"

It detects BOTH intents and processes them sequentially.

## Step-by-Step Flow

### Example: "I'm stressed about work and I drank 3 glasses of water"

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User sends message                                  │
│ "I'm stressed about work and I drank 3 glasses of water"    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Intent Detection (LLM-based)                        │
│                                                              │
│ File: chat_engine_workflow.py → _detect_intent()            │
│ Uses: domain/llm/intent_extractor.py                        │
│                                                              │
│ LLM analyzes message and returns:                           │
│   {                                                          │
│     "primary_intent": "mood_logging",                       │
│     "secondary_intent": "activity_logging",                 │
│     "confidence": "high",                                    │
│     "entities": {                                            │
│       "mood_emoji": "😟",                                    │
│       "activity_type": "water",                              │
│       "quantity": 3,                                         │
│       "unit": "glasses"                                      │
│     }                                                        │
│   }                                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Check if multi-intent enabled                       │
│                                                              │
│ File: chat_engine_workflow.py (line 301)                    │
│                                                              │
│ if self.enable_multi_intent and secondary_intent:           │
│     return self._handle_multi_intent_message(...)           │
│                                                              │
│ ✅ Multi-intent is ENABLED (line 34)                        │
│ ✅ Secondary intent exists: "activity_logging"              │
│                                                              │
│ → Proceed to multi-intent handler                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Multi-Intent Handler                                │
│                                                              │
│ File: chat_engine_workflow.py → _handle_multi_intent_message│
│ (line 425)                                                   │
│                                                              │
│ Strategy: Sequential Execution                               │
│   1. Execute PRIMARY workflow first                          │
│   2. If primary completes → execute SECONDARY                │
│   3. If primary needs input → defer secondary                │
│   4. Merge responses                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Execute PRIMARY Workflow (mood_logging)             │
│                                                              │
│ File: mood_workflow.py → start()                            │
│                                                              │
│ 5a. Extract mood and reason:                                │
│     - Calls: mood_reason_extractor.py                       │
│     - Result: mood=😟, reason="work", confidence="high"     │
│                                                              │
│ 5b. Save mood to database:                                  │
│     - mood_handler.py → save_mood_log()                     │
│     - Logs: user_id=1, mood=😟, reason="work"              │
│                                                              │
│ 5c. Get suggestions:                                        │
│     - smart_suggestions.py → get_smart_suggestions()        │
│     - Returns: 3 work-related activities                     │
│                                                              │
│ 5d. Return response:                                        │
│     {                                                        │
│       "message": "Here are activities for work:",            │
│       "actions": [3 suggestions],                            │
│       "completed": True,  ← KEY! Allows secondary           │
│       "next_state": "idle"                                   │
│     }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Check if PRIMARY completed                          │
│                                                              │
│ File: chat_engine_workflow.py (line 456)                    │
│                                                              │
│ if not primary_response.completed:                          │
│     # Primary needs input, defer secondary                   │
│     return primary_result                                    │
│                                                              │
│ ✅ Primary completed = True                                 │
│ → Continue to secondary workflow                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Reset state for SECONDARY workflow                  │
│                                                              │
│ File: chat_engine_workflow.py (line 467)                    │
│                                                              │
│ workflow_state.complete_workflow()                          │
│                                                              │
│ This clears the mood workflow state so activity workflow    │
│ can start fresh                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 8: Execute SECONDARY Workflow (activity_logging)       │
│                                                              │
│ File: activity_workflow.py → start()                        │
│                                                              │
│ 8a. Detect activity from message:                           │
│     - Uses: activity_intent_detector.py                     │
│     - Detects: "water", quantity=3, unit="glasses"          │
│                                                              │
│ 8b. Log water to database:                                  │
│     - health_activity_logger.py → log_water()               │
│     - Logs: user_id=1, quantity=3, unit="glasses"           │
│                                                              │
│ 8c. Return response:                                        │
│     {                                                        │
│       "message": "Logged 3 glasses of water!",               │
│       "completed": True,                                     │
│       "next_state": "idle"                                   │
│     }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 9: Merge Responses                                     │
│                                                              │
│ File: chat_engine_workflow.py (line 475-483)                │
│                                                              │
│ if secondary_response.completed:                            │
│     # Both completed - merge messages                        │
│     primary_result['message'] =                              │
│         f"{primary_result['message']} "                      │
│         f"{secondary_result['message']}"                     │
│     workflow_state.complete_workflow()                      │
│     return primary_result                                    │
│                                                              │
│ Final response:                                              │
│   {                                                          │
│     "message": "Here are activities for work: "              │
│                "Logged 3 glasses of water!",                 │
│     "actions": [3 mood suggestions],                         │
│     "completed": True,                                       │
│     "state": "idle"                                          │
│   }                                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 10: User sees result                                   │
│                                                              │
│ UI displays:                                                 │
│   • Message: "Here are activities for work: Logged 3        │
│     glasses of water!"                                       │
│   • 3 suggestion buttons (meditation, yoga, etc.)            │
│                                                              │
│ Database has:                                                │
│   • Mood log: 😟 with reason "work"                         │
│   • Water log: 3 glasses                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Intent Extractor
**File:** `backend/chat_assistant/domain/llm/intent_extractor.py`

Uses LLM to detect intents:
```python
def extract_intent(self, message: str) -> dict:
    # Calls OpenAI to analyze message
    # Returns primary + secondary intents
    return {
        'primary_intent': 'mood_logging',
        'secondary_intent': 'activity_logging',
        'entities': {...}
    }
```

### 2. Multi-Intent Handler
**File:** `backend/chat_assistant/chat_engine_workflow.py`

Orchestrates sequential execution:
```python
def _handle_multi_intent_message(self, message, state, user_id,
                                 primary_intent, secondary_intent):
    # 1. Execute primary workflow
    primary_response = primary_workflow.start(message, state, user_id)
    
    # 2. Check if primary completed
    if not primary_response.completed:
        return primary_result  # Defer secondary
    
    # 3. Reset state
    state.complete_workflow()
    
    # 4. Execute secondary workflow
    secondary_response = secondary_workflow.start(message, state, user_id)
    
    # 5. Merge responses
    return merged_result
```

### 3. Mood Workflow (Fixed)
**File:** `backend/chat_assistant/mood_workflow.py`

Now completes immediately when mood+reason extracted:
```python
def start(self, message, state, user_id):
    # Extract mood and reason
    extraction = extract_mood_and_reason(message)
    
    if extraction['confidence'] == 'high':
        # Save mood
        save_mood_log(user_id, mood, reason)
        
        # Get suggestions
        suggestions = get_smart_suggestions(mood, reason, context)
        
        # ✅ FIX: Return completed=True
        return WorkflowResponse(
            message=f"Here are activities for {reason}:",
            actions=suggestions,
            completed=True,  # Allows secondary workflow
            next_state=ConversationState.IDLE
        )
```

## Why It Works Now

### Before Fix:
```
Primary (mood) → completed=False → BLOCKS secondary
                                   ❌ Water never logged
```

### After Fix:
```
Primary (mood) → completed=True → ✅ Allows secondary
Secondary (water) → completed=True → ✅ Water logged
```

## Intent Priority

The system prioritizes intents in this order:

1. **Mood expressions** (if detected) → Primary
2. **Activity logging** (water, sleep, etc.) → Secondary
3. **Activity queries** (meditation, exercise) → Secondary

Example intent combinations:

| Message | Primary | Secondary |
|---------|---------|-----------|
| "I'm stressed about work and I drank water" | mood_logging | activity_logging |
| "I drank water and I'm stressed" | activity_logging | mood_logging |
| "I feel anxious and want to meditate" | mood_logging | activity_query |
| "I'm tired" | mood_logging | none |
| "I drank 3 glasses of water" | activity_logging | none |

## Limitations

1. **Max 2 intents**: System handles primary + secondary only
   - "I'm stressed, drank water, and want to exercise" → Only 2 processed

2. **Sequential execution**: Not parallel
   - Primary must complete before secondary starts

3. **Order matters**: Primary intent is processed first
   - If primary doesn't complete, secondary is deferred

4. **No deferred execution**: If primary blocks, secondary is lost
   - User would need to send another message

## Testing

Run the test to verify:
```bash
cd backend
python test_multi_intent_fix.py
```

Expected output:
```
✅ Workflow completed immediately
✅ Mood suggestions shown
✅ Water logged in background
```

## Files Involved

1. `chat_engine_workflow.py` - Main orchestrator
2. `domain/llm/intent_extractor.py` - Intent detection
3. `mood_workflow.py` - Mood logging (FIXED)
4. `activity_workflow.py` - Activity logging
5. `mood_reason_extractor.py` - Mood+reason extraction
6. `smart_suggestions.py` - Suggestion generation

## Configuration

Multi-intent is enabled by default:
```python
# In chat_engine_workflow.py (line 34)
self.enable_multi_intent = True  # Phase 3: Multi-intent support
```

To disable:
```python
self.enable_multi_intent = False
```
