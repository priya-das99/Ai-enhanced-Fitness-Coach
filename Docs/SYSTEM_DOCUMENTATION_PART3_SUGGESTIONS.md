# MoodCapture System Documentation - Part 3: Suggestion System

## 4. Suggestion System Architecture

### Overview
The suggestion system recommends wellness activities based on user mood, behavior, and preferences.

### System Flow

```
User logs mood → Suggestion Ranker → Score activities → Return top 3-5 → User accepts/rejects → Track interaction
```

### Core Components

#### 3.1 Suggestion Master Table
**Database**: `suggestion_master`
**Purpose**: Stores all available activities

```sql
CREATE TABLE suggestion_master (
    id INTEGER PRIMARY KEY,
    suggestion_key TEXT UNIQUE,  -- "breathing", "meditation"
    title TEXT,                   -- "Breathing Exercise"
    description TEXT,
    category TEXT,                -- "mindfulness", "physical"
    effort_level TEXT,            -- "low", "medium", "high"
    duration_minutes INTEGER,
    best_for TEXT                 -- JSON: ["stress", "anxiety"]
)
```

**Example Data**:
```json
{
  "suggestion_key": "breathing",
  "title": "Breathing Exercise",
  "best_for": ["stress", "anxiety", "work", "quick relief"]
}
```

#### 3.2 Intelligent Suggestions Service
**File**: `backend/chat_assistant/intelligent_suggestions.py`

```python
class IntelligentSuggestions:
    def get_suggestions(user_id: int, mood_emoji: str, reason: str):
        """
        Main suggestion engine
        
        Steps:
        1. Get all active suggestions from suggestion_master
        2. Score each suggestion using weighted algorithm
        3. Apply diversity penalty (avoid repetition)
        4. Return top 3-5 ranked suggestions
        5. Log ranking context for analytics
        """
```

### Scoring Algorithm

**File**: `backend/chat_assistant/domain/llm/suggestion_ranker.py`

```python
def calculate_score(suggestion, user_context):
    """
    Weighted scoring system
    
    Factors:
    1. Mood Match (40%): Does suggestion fit current mood?
    2. User History (30%): Has user accepted this before?
    3. Time Context (15%): Is it appropriate time of day?
    4. Recency (10%): When was it last shown?
    5. Diversity (5%): Avoid showing same suggestions
    
    Formula:
    score = (mood_match * 0.4) + 
            (acceptance_rate * 0.3) + 
            (time_match * 0.15) + 
            (recency_bonus * 0.1) + 
            (diversity_bonus * 0.05)
    """
```

**Example Calculation**:
```python
User: Feeling stressed at 3pm on workday

Suggestion: "Breathing Exercise"
- Mood match: 1.0 (perfect for stress)
- Acceptance rate: 0.8 (user accepted 4/5 times)
- Time match: 1.0 (good for afternoon)
- Recency: 0.5 (shown 2 days ago)
- Diversity: 0.8 (not shown recently)

Score = (1.0 * 0.4) + (0.8 * 0.3) + (1.0 * 0.15) + (0.5 * 0.1) + (0.8 * 0.05)
      = 0.4 + 0.24 + 0.15 + 0.05 + 0.04
      = 0.88 (88% match)
```

### Tracking System

#### Suggestion History
**Table**: `suggestion_history`
**Purpose**: Track every suggestion shown and user interaction

```sql
CREATE TABLE suggestion_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    suggestion_key TEXT,
    mood_emoji TEXT,
    reason TEXT,
    shown_at DATETIME,
    interaction_type TEXT,  -- 'shown', 'accepted', 'rejected'
    interacted_at DATETIME
)
```

#### Ranking Context
**Table**: `suggestion_ranking_context`
**Purpose**: Store why suggestions were ranked in specific order

```sql
CREATE TABLE suggestion_ranking_context (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    mood_emoji TEXT,
    reason TEXT,
    ranking_timestamp DATETIME,
    ranking_algorithm TEXT,
    total_candidates INTEGER,
    selected_suggestion_key TEXT,
    context_snapshot TEXT  -- JSON with scores
)
```

### Integration Points

#### When Suggestions Are Generated

**1. After Mood Logging**
**File**: `backend/chat_assistant/mood_workflow.py`

```python
def handle_mood_logged(user_id, mood_emoji, reason):
    # Get personalized suggestions
    suggestions = IntelligentSuggestions.get_suggestions(
        user_id, mood_emoji, reason
    )
    
    # Return with response
    return WorkflowResponse(
        message="Here are some activities that might help...",
        suggestions=suggestions,
        ui_elements=['suggestion_buttons']
    )
```

**2. On User Request**
**File**: `backend/chat_assistant/activity_query_workflow.py`

```python
def handle_activity_query(user_id, message):
    # User asks: "What can I do to feel better?"
    suggestions = IntelligentSuggestions.get_suggestions(
        user_id, 
        mood_emoji=get_last_mood(user_id),
        reason="user_requested"
    )
```

### Files Involved

**Core Logic**:
- `backend/chat_assistant/intelligent_suggestions.py` - Main engine
- `backend/chat_assistant/domain/llm/suggestion_ranker.py` - Scoring
- `backend/app/services/ranking_context_logger.py` - Analytics

**Data Access**:
- `backend/app/repositories/activity_repository.py` - Database queries
- `backend/chat_assistant/user_history.py` - User behavior data

**Tracking**:
- `backend/app/services/suggestion_interaction_tracker.py` - Track clicks
- `backend/app/services/behavior_scorer.py` - Update user metrics
