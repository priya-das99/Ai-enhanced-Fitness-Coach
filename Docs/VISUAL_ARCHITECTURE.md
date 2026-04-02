# Visual Architecture Guide

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                     (frontend/chat.js)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /api/v1/chat/message
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
│                 (app/api/v1/endpoints/chat.py)                  │
│  - Validates JWT token                                          │
│  - Extracts user_id                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CHAT SERVICE                                 │
│                (app/services/chat_service.py)                   │
│  - Loads user history                                           │
│  - Calls chat engine                                            │
│  - Saves messages                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CHAT ENGINE (MAIN ORCHESTRATOR)               │
│            (chat_assistant/chat_engine_workflow.py)             │
│                                                                 │
│  1. Load conversation state (unified_state.py)                  │
│  2. Check for active workflow                                   │
│  3. If no active workflow → Detect intent                       │
│  4. Route to appropriate workflow                               │
│  5. Execute workflow                                            │
│  6. Generate response                                           │
│  7. Save state                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LLM INTENT DETECTOR                            │
│           (chat_assistant/llm_intent_detector.py)               │
│                                                                 │
│  Input: User message + conversation history                     │
│  Process:                                                       │
│    1. Build context (context_builder_simple.py)                 │
│    2. Call OpenAI API (llm_service.py)                          │
│    3. Extract intent (domain/llm/intent_extractor.py)           │
│  Output: Intent + Entities                                      │
│    Example: {                                                   │
│      "intent": "mood_logging",                                  │
│      "entities": {"mood": "stressed", "reason": "work"}         │
│    }                                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WORKFLOW REGISTRY                              │
│           (chat_assistant/workflow_registry.py)                 │
│                                                                 │
│  Intent → Workflow Mapping:                                     │
│    "mood_logging" → MoodWorkflow                                │
│    "activity_logging" → ActivityWorkflow                        │
│    "challenges" → ChallengesWorkflow                            │
│    "activity_query" → ActivityQueryWorkflow                     │
│    "general_chat" → GeneralWorkflow                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW EXECUTION                           │
│                  (Specific *_workflow.py)                       │
│                                                                 │
│  Each workflow inherits from workflow_base.py                   │
│  Methods:                                                       │
│    - start(message, state, user_id)                             │
│    - process(message, state, user_id)                           │
│    - _complete_workflow(message, ...)                           │
│                                                                 │
│  Workflow Types:                                                │
│    ┌──────────────────────────────────────────────┐            │
│    │ MOOD WORKFLOW (mood_workflow.py)             │            │
│    │  1. Extract mood (mood_extractor.py)         │            │
│    │  2. Ask for reason if negative                │            │
│    │  3. Log to database                           │            │
│    │  4. Get suggestions (smart_suggestions.py)    │            │
│    │  5. Generate empathetic response              │            │
│    └──────────────────────────────────────────────┘            │
│                                                                 │
│    ┌──────────────────────────────────────────────┐            │
│    │ ACTIVITY WORKFLOW (activity_workflow.py)     │            │
│    │  1. Detect activity type (activity_intent)   │            │
│    │  2. Extract value (8 glasses, 7 hours)       │            │
│    │  3. Log activity (health_activity_logger)    │            │
│    │  4. Update challenges (challenge_service)    │            │
│    │  5. Return confirmation                       │            │
│    └──────────────────────────────────────────────┘            │
│                                                                 │
│    ┌──────────────────────────────────────────────┐            │
│    │ CHALLENGES WORKFLOW (challenges_workflow.py) │            │
│    │  1. Get challenges (challenge_service)       │            │
│    │  2. Get insights (insight_generator)         │            │
│    │  3. Detect patterns (pattern_detector)       │            │
│    │  4. Format progress message                  │            │
│    │  5. Add action buttons                       │            │
│    └──────────────────────────────────────────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SUGGESTION ENGINE                              │
│         (chat_assistant/intelligent_suggestions.py)             │
│                                                                 │
│  1. Get user context (mood, history, preferences)               │
│  2. Query predefined activities                                 │
│  3. Query wellness content                                      │
│  4. Rank by relevance (domain/llm/suggestion_ranker.py)         │
│  5. Return top 3-5 suggestions                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RESPONSE GENERATION                            │
│          (chat_assistant/response_phrasing.py)                  │
│                                                                 │
│  1. Take workflow output                                        │
│  2. Apply response templates                                    │
│  3. Add natural language phrasing                               │
│  4. Validate response (response_validator.py)                   │
│  5. Check safety (guardrails.py)                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                               │
│              (app/repositories/*_repository.py)                 │
│                                                                 │
│  Save:                                                          │
│    - User message (chat_repository)                             │
│    - Bot response (chat_repository)                             │
│    - Activity data (activity_repository)                        │
│    - Mood data (mood_repository)                                │
│    - Challenge progress (challenge_repository)                  │
│    - Conversation state (unified_state)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RETURN TO USER                               │
│                                                                 │
│  Response Format:                                               │
│  {                                                              │
│    "message": "I understand work stress is tough. Here are...", │
│    "suggestions": [                                             │
│      {                                                          │
│        "id": "meditation_5min",                                 │
│        "name": "5-Minute Meditation",                           │
│        "type": "meditation",                                    │
│        "duration": 5                                            │
│      },                                                         │
│      {                                                          │
│        "id": "deep_breathing",                                  │
│        "name": "Deep Breathing Exercise",                       │
│        "type": "breathing",                                     │
│        "duration": 3                                            │
│      }                                                          │
│    ],                                                           │
│    "action_buttons": [                                          │
│      {                                                          │
│        "id": "start_meditation",                                │
│        "label": "Start Meditation",                             │
│        "action": "log_activity"                                 │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## File Interaction Matrix

| File | Calls | Called By | Data Flow |
|------|-------|-----------|-----------|
| chat_engine_workflow.py | llm_intent_detector, workflow_registry, unified_state | chat_service.py | Message → Intent → Workflow → Response |
| llm_intent_detector.py | llm_service, context_builder | chat_engine | Message → LLM → Intent |
| workflow_registry.py | All *_workflow.py files | chat_engine | Intent → Workflow instance |
| activity_workflow.py | activity_intent_detector, health_activity_logger, challenge_service | workflow_registry | Message → Activity data → DB |
| mood_workflow.py | mood_extractor, mood_handler, smart_suggestions | workflow_registry | Message → Mood → DB + Suggestions |
| challenges_workflow.py | challenge_service, insight_generator, pattern_detector | workflow_registry | Request → Progress data → Formatted response |
| intelligent_suggestions.py | predefined_activities, content_service, user_history | Workflows | Context → Ranked suggestions |
| unified_state.py | None (data store) | All workflows | Stores conversation state |

## Key Decision Points

### 1. Intent Detection (llm_intent_detector.py)
```
User Message
    ↓
Is it about mood? → mood_logging
Is it about activity? → activity_logging
Is it about challenges? → challenges
Is it a question? → activity_query
Is it general? → general_chat
```

### 2. Workflow Selection (workflow_registry.py)
```
Intent
    ↓
mood_logging → MoodWorkflow
activity_logging → ActivityWorkflow
challenges → ChallengesWorkflow
activity_query → ActivityQueryWorkflow
general_chat → GeneralWorkflow
```

### 3. Suggestion Generation (intelligent_suggestions.py)
```
User Context (mood, history, preferences)
    ↓
Query predefined activities
Query wellness content
    ↓
Rank by relevance
    ↓
Return top suggestions
```

---

## Summary: How It All Works Together

1. **User sends message** → API endpoint
2. **Chat service** loads history → calls chat engine
3. **Chat engine** loads state → calls LLM intent detector
4. **LLM** analyzes message → returns intent + entities
5. **Workflow registry** maps intent → workflow
6. **Workflow** processes message → generates response
7. **Suggestion engine** adds recommendations
8. **Response** validated → saved to DB → returned to user

**Every file has a specific role in this flow!**
