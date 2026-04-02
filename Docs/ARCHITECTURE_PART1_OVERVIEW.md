# 🏗️ MoodCapture Chat Assistant - Architecture Deep Dive (Part 1)

## 📋 Table of Contents
- Part 1: Overview & Data Flow (this file)
- Part 2: Core Components (ARCHITECTURE_PART2_CORE.md)
- Part 3: Workflows (ARCHITECTURE_PART3_WORKFLOWS.md)
- Part 4: LLM & Suggestions (ARCHITECTURE_PART4_LLM.md)
- Part 5: Utilities & Helpers (ARCHITECTURE_PART5_UTILS.md)

---

## 🎯 System Overview

MoodCapture uses a **workflow-based architecture** where:
1. User sends message via API
2. LLM detects intent
3. Appropriate workflow handles the conversation
4. Response is generated with suggestions
5. Data is stored in database

---

## 📊 Complete File List (38 files)

### Core Engine (Entry Points)
1. `chat_engine_workflow.py` - Main chat engine (LLM-based routing)
2. `chat_engine_with_suggestions.py` - Enhanced engine with suggestions

### Workflow System
3. `workflow_base.py` - Base class for all workflows
4. `workflow_registry.py` - Registers and routes to workflows
5. `activity_workflow.py` - Handles activity logging
6. `mood_workflow.py` - Handles mood logging
7. `challenges_workflow.py` - Handles challenge tracking
8. `activity_query_workflow.py` - Handles activity suggestions
9. `general_workflow.py` - Handles general chat
10. `example_workflow.py` - Example/template workflow

### State Management
11. `unified_state.py` - Manages conversation state
12. `conversation_state.py` - Tracks conversation context
13. `session_summary.py` - Summarizes sessions

### LLM Integration
14. `llm_service.py` - OpenAI API integration
15. `llm_service_with_tracking.py` - LLM with token tracking
16. `llm_intent_detector.py` - Detects user intent via LLM
17. `domain/llm/intent_extractor.py` - Extracts structured intent
18. `domain/llm/response_phraser.py` - Phrases responses naturally
19. `domain/llm/suggestion_ranker.py` - Ranks suggestions by relevance

### Suggestions System
20. `intelligent_suggestions.py` - Smart suggestion engine
21. `smart_suggestions.py` - Context-aware suggestions
22. `action_suggestions.py` - Actionable suggestions
23. `content_suggestions.py` - Content recommendations
24. `predefined_activities.py` - Predefined activity database

### Context & Detection
25. `context_detector.py` - Detects conversation context
26. `context_builder_simple.py` - Builds context for LLM
27. `conversation_depth_tracker.py` - Tracks conversation depth

### Mood System
28. `mood_handler.py` - Handles mood-related logic
29. `mood_extractor.py` - Extracts mood from text
30. `mood_categories.py` - Mood classification

### Activity System
31. `activity_chat_handler.py` - Handles activity conversations
32. `activity_intent_detector.py` - Detects activity intents
33. `health_activity_logger.py` - Logs health activities

### Response Generation
34. `response_templates.py` - Response templates
35. `response_phrasing.py` - Natural language phrasing
36. `response_validation.py` - Validates responses
37. `response_validator.py` - Response validation logic

### Safety & Utilities
38. `guardrails.py` - Safety checks and content filtering
39. `safety_layer.py` - Additional safety layer
40. `user_history.py` - User history management

---

## 🔄 Data Flow: User Message → Response

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER SENDS MESSAGE                                       │
│    "I'm feeling stressed about work"                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. API ENDPOINT (chat.py)                                   │
│    POST /api/v1/chat/message                                │
│    - Validates auth token                                   │
│    - Extracts user_id                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CHAT SERVICE (chat_service.py)                           │
│    - Loads user history                                     │
│    - Calls chat engine                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CHAT ENGINE (chat_engine_workflow.py)                    │
│    - Loads conversation state                               │
│    - Checks for active workflow                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM INTENT DETECTOR (llm_intent_detector.py)             │
│    - Sends message to OpenAI                                │
│    - Gets intent: "mood_logging"                            │
│    - Extracts entities: mood="stressed", reason="work"      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. WORKFLOW REGISTRY (workflow_registry.py)                 │
│    - Maps intent → workflow                                 │
│    - Returns MoodWorkflow instance                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. MOOD WORKFLOW (mood_workflow.py)                         │
│    - Processes mood logging                                 │
│    - Calls mood_extractor to confirm mood                   │
│    - Logs to database                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. SUGGESTION ENGINE (intelligent_suggestions.py)           │
│    - Gets stress-relief activities                          │
│    - Ranks by user history                                  │
│    - Returns top 3 suggestions                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. RESPONSE PHRASER (response_phraser.py)                   │
│    - Generates empathetic response                          │
│    - Adds suggestions naturally                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. RESPONSE VALIDATOR (response_validator.py)              │
│     - Checks for inappropriate content                      │
│     - Validates structure                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. SAVE TO DATABASE (chat_repository.py)                   │
│     - Saves user message                                    │
│     - Saves bot response                                    │
│     - Updates conversation state                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 12. RETURN TO USER                                          │
│     {                                                       │
│       "message": "I understand work stress is tough...",    │
│       "suggestions": [                                      │
│         {"name": "5-min meditation", "type": "meditation"}, │
│         {"name": "Deep breathing", "type": "breathing"}     │
│       ]                                                     │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Components Explained

### 1. Entry Point
**File:** `chat_engine_workflow.py`
**Purpose:** Main orchestrator
**Called by:** `chat_service.py`
**Calls:** LLM intent detector, workflow registry

### 2. Intent Detection
**File:** `llm_intent_detector.py`
**Purpose:** Uses OpenAI to understand user intent
**Input:** User message + conversation history
**Output:** Intent name + extracted entities

### 3. Workflow Routing
**File:** `workflow_registry.py`
**Purpose:** Maps intents to workflows
**Maintains:** Dictionary of intent → workflow

### 4. Workflow Execution
**Files:** `*_workflow.py`
**Purpose:** Handles specific conversation types
**Base class:** `workflow_base.py`

### 5. State Management
**File:** `unified_state.py`
**Purpose:** Tracks conversation across messages
**Stores:** Active workflow, conversation context, user data

---

## 📁 File Organization

```
chat_assistant/
├── Core Engine
│   ├── chat_engine_workflow.py (main orchestrator)
│   └── chat_engine_with_suggestions.py (enhanced version)
│
├── Workflow System
│   ├── workflow_base.py (base class)
│   ├── workflow_registry.py (router)
│   ├── activity_workflow.py
│   ├── mood_workflow.py
│   ├── challenges_workflow.py
│   ├── activity_query_workflow.py
│   └── general_workflow.py
│
├── LLM Integration
│   ├── llm_service.py
│   ├── llm_intent_detector.py
│   └── domain/llm/
│       ├── intent_extractor.py
│       ├── response_phraser.py
│       └── suggestion_ranker.py
│
├── Suggestions
│   ├── intelligent_suggestions.py
│   ├── smart_suggestions.py
│   ├── action_suggestions.py
│   └── content_suggestions.py
│
├── State & Context
│   ├── unified_state.py
│   ├── conversation_state.py
│   ├── context_detector.py
│   └── context_builder_simple.py
│
├── Mood System
│   ├── mood_workflow.py
│   ├── mood_handler.py
│   ├── mood_extractor.py
│   └── mood_categories.py
│
├── Activity System
│   ├── activity_workflow.py
│   ├── activity_chat_handler.py
│   ├── activity_intent_detector.py
│   └── health_activity_logger.py
│
├── Response Generation
│   ├── response_templates.py
│   ├── response_phrasing.py
│   ├── response_validation.py
│   └── response_validator.py
│
└── Utilities
    ├── guardrails.py
    ├── safety_layer.py
    ├── user_history.py
    ├── session_summary.py
    └── predefined_activities.py
```

---

**Continue to Part 2 for detailed component analysis...**
