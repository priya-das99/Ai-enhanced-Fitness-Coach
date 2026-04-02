# Architecture Deep Dive - Part 2: Detailed File Analysis

## Core Files Analysis (1-10)

### 1. action_suggestions.py
**Purpose:** Generates actionable suggestions for users
**Key Functions:**
- `get_action_suggestions()` - Returns list of suggested actions
- `filter_by_context()` - Filters suggestions based on user context
**Used By:** Workflows when generating responses
**Uses:** predefined_activities.py, user_history.py

### 2. activity_chat_handler.py  
**Purpose:** Handles conversational activity logging
**Key Functions:**
- `handle_activity_message()` - Processes activity-related messages
- `extract_activity_data()` - Extracts activity values from text
**Used By:** activity_workflow.py
**Uses:** activity_intent_detector.py

### 3. activity_intent_detector.py
**Purpose:** Detects if message is about logging an activity
**Key Functions:**
- `detect_activity_intent()` - Returns activity type (water/sleep/exercise)
- `extract_value()` - Extracts numeric values from text
**Used By:** activity_chat_handler.py, activity_workflow.py
**Pattern Matching:** Uses regex for "8 glasses", "7 hours", etc.

### 4. activity_query_workflow.py
**Purpose:** Handles "What should I do?" type questions
**Workflow Type:** Query/Suggestion workflow
**Key Methods:**
- `start()` - Entry point for activity queries
- `process()` - Generates activity suggestions
**Triggers:** "what should i do", "suggest activity", "i'm bored"
**Returns:** List of personalized activity suggestions

### 5. activity_workflow.py
**Purpose:** Main workflow for logging activities (water, sleep, exercise)
**Workflow Type:** Multi-step conversation workflow
**Key Methods:**
- `start()` - Initiates activity logging
- `process()` - Handles follow-up questions
- `log_activity()` - Saves to database
**States:** 
- asking_activity_type
- asking_value
- confirming
- completed
**Triggers:** "i drank", "i slept", "log water", "track exercise"

### 6. challenges_workflow.py
**Purpose:** Shows user's challenge progress and motivates them
**Workflow Type:** Display/Information workflow
**Key Methods:**
- `start()` - Shows challenges overview
- `get_challenges_summary()` - Fetches from database
- `create_progress_response()` - Formats progress message
**Triggers:** "how am i doing", "my challenges", "show progress"
**Returns:** Challenge list with progress bars, points, insights

### 7. chat_engine_with_suggestions.py
**Purpose:** Enhanced chat engine that adds smart suggestions
**Key Functions:**
- `process_message()` - Main entry point
- `add_suggestions()` - Appends relevant suggestions
**Used By:** chat_service.py (alternative to chat_engine_workflow)
**Uses:** intelligent_suggestions.py, smart_suggestions.py

### 8. chat_engine_workflow.py
**Purpose:** MAIN ORCHESTRATOR - Routes messages to appropriate workflows
**Key Functions:**
- `process_message()` - Entry point for all messages
- `route_to_workflow()` - Determines which workflow to use
- `handle_workflow_response()` - Processes workflow output
**Flow:**
1. Load conversation state
2. Call LLM intent detector
3. Get workflow from registry
4. Execute workflow
5. Save response
**This is the HEART of the system!**

### 9. content_suggestions.py
**Purpose:** Suggests wellness content (articles, videos, exercises)
**Key Functions:**
- `get_content_suggestions()` - Returns content recommendations
- `rank_by_relevance()` - Ranks content by user preferences
**Used By:** Workflows when user needs resources
**Data Source:** wellness_content table in database

### 10. context_builder_simple.py
**Purpose:** Builds context string for LLM prompts
**Key Functions:**
- `build_context()` - Creates context from conversation history
- `summarize_history()` - Condenses long conversations
**Used By:** llm_intent_detector.py, llm_service.py
**Output:** Formatted string with recent messages and user info

---

## Continue to next section for files 11-20...
