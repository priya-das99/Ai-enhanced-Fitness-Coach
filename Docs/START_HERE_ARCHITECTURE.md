# 🎯 START HERE: Understanding MoodCapture Architecture

## 📚 Documentation Index

I've created comprehensive documentation for you:

1. **START_HERE_ARCHITECTURE.md** (this file) - Quick start guide
2. **ARCHITECTURE_PART1_OVERVIEW.md** - System overview & data flow
3. **COMPLETE_FILE_GUIDE.md** - What each file does (quick reference)
4. **VISUAL_ARCHITECTURE.md** - Visual diagrams and flow charts
5. **ARCHITECTURE_PART2_DETAILED.md** - Detailed file analysis

---

## 🚀 Quick Understanding (5 Minutes)

### The Big Picture
MoodCapture is a **workflow-based chat system** where:
- User sends message
- AI detects intent
- Appropriate workflow handles it
- Response generated with suggestions
- Data saved to database

### 5 Core Components

1. **Chat Engine** (`chat_engine_workflow.py`)
   - Main orchestrator
   - Routes messages to workflows

2. **LLM Intent Detector** (`llm_intent_detector.py`)
   - Uses OpenAI to understand user intent
   - Returns: "mood_logging", "activity_logging", etc.

3. **Workflow Registry** (`workflow_registry.py`)
   - Maps intents to workflows
   - Returns appropriate workflow instance

4. **Workflows** (`*_workflow.py`)
   - Handle specific conversation types
   - Process user input
   - Generate responses

5. **Suggestion Engine** (`intelligent_suggestions.py`)
   - Recommends activities
   - Personalizes based on history

---

## 📁 40 Files Organized

### CRITICAL (Must Understand) - 5 files
1. `chat_engine_workflow.py` - Main orchestrator
2. `workflow_registry.py` - Routes to workflows
3. `activity_workflow.py` - Logs activities
4. `mood_workflow.py` - Logs moods
5. `llm_intent_detector.py` - Detects intent

### IMPORTANT (Should Understand) - 10 files
6. `unified_state.py` - Manages conversation state
7. `challenges_workflow.py` - Shows progress
8. `activity_query_workflow.py` - Suggests activities
9. `general_workflow.py` - General chat
10. `workflow_base.py` - Base class for workflows
11. `llm_service.py` - OpenAI integration
12. `intelligent_suggestions.py` - Suggestion engine
13. `context_builder_simple.py` - Builds LLM context
14. `mood_extractor.py` - Extracts mood from text
15. `activity_intent_detector.py` - Detects activity type

### SUPPORTING (Nice to Know) - 25 files
16-40. All other files support the above

---

## 🔄 Data Flow (Simple)

```
User Message
    ↓
API Endpoint
    ↓
Chat Service
    ↓
Chat Engine ← (loads state from unified_state.py)
    ↓
LLM Intent Detector ← (calls llm_service.py)
    ↓
Workflow Registry ← (maps intent to workflow)
    ↓
Specific Workflow (mood/activity/challenges/etc.)
    ↓
Suggestion Engine ← (gets recommendations)
    ↓
Response Generated
    ↓
Saved to Database
    ↓
Returned to User
```

---

## 💡 How to Learn the System

### Step 1: Understand the Flow (30 min)
Read: `VISUAL_ARCHITECTURE.md`
- See complete system flow
- Understand how files interact

### Step 2: Learn Core Files (1 hour)
Read these 5 files in order:
1. `chat_engine_workflow.py` - Start here!
2. `llm_intent_detector.py` - How intent is detected
3. `workflow_registry.py` - How routing works
4. `workflow_base.py` - Base class structure
5. `mood_workflow.py` - Example workflow

### Step 3: Explore Workflows (1 hour)
Read these workflow files:
- `activity_workflow.py` - Activity logging
- `challenges_workflow.py` - Progress tracking
- `activity_query_workflow.py` - Suggestions
- `general_workflow.py` - General chat

### Step 4: Understand Support Systems (1 hour)
Read:
- `unified_state.py` - State management
- `intelligent_suggestions.py` - Recommendations
- `llm_service.py` - LLM integration

---

## 🎯 Key Concepts

### 1. Workflows
- Each workflow handles a specific conversation type
- Inherits from `workflow_base.py`
- Has `start()` and `process()` methods
- Returns `WorkflowResponse` object

### 2. Intent Detection
- LLM analyzes user message
- Returns intent name (e.g., "mood_logging")
- Extracts entities (e.g., mood="happy")

### 3. State Management
- `unified_state.py` tracks conversation
- Stores active workflow
- Maintains context across messages

### 4. Suggestions
- Generated based on user context
- Ranked by relevance
- Personalized using history

---

## 📊 File Categories

### Entry Points (2 files)
- `chat_engine_workflow.py`
- `chat_engine_with_suggestions.py`

### Workflows (6 files)
- `workflow_base.py`
- `workflow_registry.py`
- `activity_workflow.py`
- `mood_workflow.py`
- `challenges_workflow.py`
- `activity_query_workflow.py`
- `general_workflow.py`
- `example_workflow.py`

### LLM Integration (6 files)
- `llm_service.py`
- `llm_service_with_tracking.py`
- `llm_intent_detector.py`
- `domain/llm/intent_extractor.py`
- `domain/llm/response_phraser.py`
- `domain/llm/suggestion_ranker.py`

### Suggestions (5 files)
- `intelligent_suggestions.py`
- `smart_suggestions.py`
- `action_suggestions.py`
- `content_suggestions.py`
- `predefined_activities.py`

### State & Context (5 files)
- `unified_state.py`
- `conversation_state.py`
- `context_detector.py`
- `context_builder_simple.py`
- `conversation_depth_tracker.py`

### Mood System (4 files)
- `mood_workflow.py`
- `mood_handler.py`
- `mood_extractor.py`
- `mood_categories.py`

### Activity System (4 files)
- `activity_workflow.py`
- `activity_chat_handler.py`
- `activity_intent_detector.py`
- `health_activity_logger.py`

### Response Generation (4 files)
- `response_templates.py`
- `response_phrasing.py`
- `response_validation.py`
- `response_validator.py`

### Utilities (4 files)
- `guardrails.py`
- `safety_layer.py`
- `user_history.py`
- `session_summary.py`

---

## ❓ Common Questions

**Q: Where does a message enter the system?**
A: `chat_engine_workflow.py` → `process_message()` method

**Q: How is intent detected?**
A: `llm_intent_detector.py` calls OpenAI API

**Q: How are workflows selected?**
A: `workflow_registry.py` maps intent → workflow

**Q: Where is conversation state stored?**
A: `unified_state.py` manages all state

**Q: How are suggestions generated?**
A: `intelligent_suggestions.py` ranks activities

**Q: Where is data saved?**
A: Each workflow calls appropriate repository

---

## 🎓 Next Steps

1. **Read VISUAL_ARCHITECTURE.md** - See the complete flow
2. **Read COMPLETE_FILE_GUIDE.md** - Quick reference
3. **Open chat_engine_workflow.py** - Start reading code
4. **Trace a message flow** - Follow one example through
5. **Ask questions** - About specific files or flows

---

## 💬 Want to Understand Specific Files?

Tell me which files you want detailed explanations for:
- I can explain any file in depth
- Show you how it connects to others
- Provide code examples
- Explain the design decisions

**Ready to dive deeper? Let me know where to start!**
