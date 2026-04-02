# Complete Chat Assistant File Guide

## Quick Reference: What Each File Does

### CORE ENGINE (Entry Points)
| File | Purpose | Called By | Calls |
|------|---------|-----------|-------|
| chat_engine_workflow.py | Main orchestrator | chat_service.py | llm_intent_detector, workflow_registry |
| chat_engine_with_suggestions.py | Alternative engine with suggestions | chat_service.py | intelligent_suggestions |

### WORKFLOWS (Conversation Handlers)
| File | Purpose | Triggers | Returns |
|------|---------|----------|---------|
| workflow_base.py | Base class for all workflows | N/A | N/A |
| workflow_registry.py | Routes intents to workflows | chat_engine | Workflow instance |
| activity_workflow.py | Logs water/sleep/exercise | "i drank", "i slept" | Confirmation + challenge update |
| mood_workflow.py | Logs user mood | "i'm happy", "feeling sad" | Empathy + suggestions |
| challenges_workflow.py | Shows progress | "how am i doing" | Progress + insights |
| activity_query_workflow.py | Suggests activities | "what should i do" | Activity suggestions |
| general_workflow.py | General chat | "hello", "thanks" | Friendly response |
| example_workflow.py | Template/example | N/A | N/A |

### LLM INTEGRATION (AI Components)
| File | Purpose | Input | Output |
|------|---------|-------|--------|
| llm_service.py | OpenAI API wrapper | Prompt | LLM response |
| llm_service_with_tracking.py | LLM with token tracking | Prompt | Response + token count |
| llm_intent_detector.py | Detects user intent | Message | Intent + entities |
| domain/llm/intent_extractor.py | Extracts structured intent | LLM response | Intent object |
| domain/llm/response_phraser.py | Phrases responses naturally | Data | Natural language |
| domain/llm/suggestion_ranker.py | Ranks suggestions | Suggestions + context | Ranked list |

### SUGGESTIONS (Recommendation System)
| File | Purpose | Input | Output |
|------|---------|-------|--------|
| intelligent_suggestions.py | Smart suggestion engine | User context | Personalized suggestions |
| smart_suggestions.py | Context-aware suggestions | Mood + history | Relevant activities |
| action_suggestions.py | Actionable suggestions | Current state | Action buttons |
| content_suggestions.py | Content recommendations | User preferences | Articles/videos |
| predefined_activities.py | Activity database | Activity type | Activity details |

### STATE MANAGEMENT (Memory)
| File | Purpose | Stores | Used By |
|------|---------|--------|---------|
| unified_state.py | Main state manager | Active workflow, context | All workflows |
| conversation_state.py | Conversation tracking | Message history | chat_engine |
| session_summary.py | Session summaries | Session data | Analytics |
| user_history.py | User history | Past activities | Suggestions |

### CONTEXT & DETECTION (Understanding)
| File | Purpose | Analyzes | Returns |
|------|---------|----------|---------|
| context_detector.py | Detects conversation context | Message + history | Context type |
| context_builder_simple.py | Builds LLM context | Conversation | Context string |
| conversation_depth_tracker.py | Tracks conversation depth | Message count | Depth level |

### MOOD SYSTEM (Emotion Handling)
| File | Purpose | Input | Output |
|------|---------|-------|--------|
| mood_workflow.py | Mood logging workflow | Mood message | Logged mood + response |
| mood_handler.py | Mood processing logic | Mood data | Processed mood |
| mood_extractor.py | Extracts mood from text | Message | Mood emoji |
| mood_categories.py | Mood classification | Mood text | Mood category |

### ACTIVITY SYSTEM (Activity Tracking)
| File | Purpose | Input | Output |
|------|---------|-------|--------|
| activity_workflow.py | Activity logging workflow | Activity message | Logged activity |
| activity_chat_handler.py | Activity conversation | Activity text | Extracted data |
| activity_intent_detector.py | Detects activity intent | Message | Activity type |
| health_activity_logger.py | Logs health activities | Activity data | Database entry |

### RESPONSE GENERATION (Output Formatting)
| File | Purpose | Input | Output |
|------|---------|-------|--------|
| response_templates.py | Response templates | Template name | Template string |
| response_phrasing.py | Natural phrasing | Data | Natural text |
| response_validation.py | Validates responses | Response | Valid/Invalid |
| response_validator.py | Response validation logic | Response object | Validation result |

### SAFETY & UTILITIES (Support)
| File | Purpose | Checks | Returns |
|------|---------|--------|---------|
| guardrails.py | Content safety | Message content | Safe/Unsafe |
| safety_layer.py | Additional safety | Response | Filtered response |

---

## Data Flow Examples

### Example 1: Mood Logging
```
User: "I'm feeling stressed"
  ↓
chat_engine_workflow.py
  ↓
llm_intent_detector.py → Intent: "mood_logging"
  ↓
workflow_registry.py → Returns: MoodWorkflow
  ↓
mood_workflow.py
  ├→ mood_extractor.py → Extracts: 😰
  ├→ Asks: "What's causing the stress?"
  └→ Returns response
```

### Example 2: Activity Logging
```
User: "I drank 8 glasses of water"
  ↓
chat_engine_workflow.py
  ↓
llm_intent_detector.py → Intent: "activity_logging"
  ↓
workflow_registry.py → Returns: ActivityWorkflow
  ↓
activity_workflow.py
  ├→ activity_intent_detector.py → Type: "water", Value: 8
  ├→ health_activity_logger.py → Logs to DB
  ├→ challenge_service.py → Updates challenge
  └→ Returns: "Great! 8 glasses logged!"
```

### Example 3: Challenge Progress
```
User: "How am I doing?"
  ↓
chat_engine_workflow.py
  ↓
llm_intent_detector.py → Intent: "challenges"
  ↓
workflow_registry.py → Returns: ChallengesWorkflow
  ↓
challenges_workflow.py
  ├→ challenge_service.py → Gets challenges
  ├→ insight_generator.py → Gets insights
  ├→ pattern_detector.py → Detects patterns
  └→ Returns: Progress + insights
```

---

## File Dependencies Map

```
chat_engine_workflow.py
├── llm_intent_detector.py
│   ├── llm_service.py
│   └── context_builder_simple.py
├── workflow_registry.py
│   ├── activity_workflow.py
│   ├── mood_workflow.py
│   ├── challenges_workflow.py
│   ├── activity_query_workflow.py
│   └── general_workflow.py
└── unified_state.py

activity_workflow.py
├── activity_intent_detector.py
├── activity_chat_handler.py
├── health_activity_logger.py
└── intelligent_suggestions.py

mood_workflow.py
├── mood_extractor.py
├── mood_handler.py
├── mood_categories.py
└── smart_suggestions.py

challenges_workflow.py
├── challenge_service.py
├── insight_generator.py
└── pattern_detector.py
```

---

## Which Files Are Most Important?

### CRITICAL (Must understand):
1. **chat_engine_workflow.py** - Main orchestrator
2. **workflow_registry.py** - Routes to workflows
3. **activity_workflow.py** - Core feature
4. **mood_workflow.py** - Core feature
5. **llm_intent_detector.py** - Intent detection

### IMPORTANT (Should understand):
6. **unified_state.py** - State management
7. **challenges_workflow.py** - Progress tracking
8. **intelligent_suggestions.py** - Recommendations
9. **workflow_base.py** - Base class
10. **llm_service.py** - LLM integration

### SUPPORTING (Nice to understand):
11-40. All other files support the above

---

**Want detailed analysis of specific files? Let me know which ones!**
