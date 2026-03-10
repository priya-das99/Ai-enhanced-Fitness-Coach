# Activity Summary Query Analysis

## User Request
Can the bot answer questions about:
1. **Daily activity summary**: "What did I do today?" or "Show me my activities today"
2. **Specific activity queries**: "How much water did I drink?" or "Did I exercise today?"

## Current System Capabilities

### ✅ What EXISTS:

1. **Data Storage**
   - All activities are stored in `health_activities` table with:
     - `user_id`, `activity_type`, `value`, `unit`, `notes`, `timestamp`
   - Activity types: water, sleep, exercise, weight, meal
   - All user activities are being logged and persisted

2. **Basic Retrieval Functions**
   - `get_today_activities(user_id)` - Gets all today's activities
   - `get_activity_summary(user_id, activity_type, days)` - Gets summary for specific activity
   - Located in: `backend/chat_assistant/health_activity_logger.py`

3. **Challenge-Specific Queries** (Just Fixed!)
   - "Did I meet my water goal?" ✅
   - "How many glasses do I need to drink more?" ✅
   - These work because they're handled by `ChallengesWorkflow`

### ❌ What's MISSING:

1. **No Intent for Activity Summary**
   - Current intents:
     - `mood_logging` - Log mood
     - `activity_logging` - Log new activity
     - `activity_query` - Get activity suggestions (e.g., "what activity for stress")
     - `challenges` - Challenge progress
     - `general_chat` - General conversation
   - **Missing**: `activity_summary` or `activity_history` intent

2. **No Workflow for Activity Summary**
   - No workflow handles queries like:
     - "What did I do today?"
     - "Show me my activities"
     - "How much water did I drink today?"
     - "Did I exercise today?"

3. **General Workflow Doesn't Handle This**
   - `GeneralWorkflow` is a catch-all but doesn't have logic to:
     - Detect activity summary requests
     - Query the database for user activities
     - Format activity data into readable responses

## What Would Happen Now?

### Test Case 1: "What did I do today?"
**Current Behavior:**
1. Intent detection → Likely classified as `general_chat`
2. Routes to `GeneralWorkflow`
3. GeneralWorkflow calls LLM with the question
4. LLM responds with generic text (no database access)
5. **Result**: Generic response like "I can help you track your activities! What would you like to log?"

**Expected Behavior:**
- Query database for today's activities
- Format response: "Today you logged: 💧 2 glasses of water, 😴 7 hours of sleep, 🏃 30 minutes of exercise, 😊 Mood: Happy"

### Test Case 2: "How much water did I drink today?"
**Current Behavior:**
1. Intent detection → Could be `activity_logging` (wrong!) or `general_chat`
2. If `activity_logging` → Asks "How much water did you drink?"
3. If `general_chat` → Generic LLM response without database query
4. **Result**: Doesn't answer the question with actual data

**Expected Behavior:**
- Query database: `SELECT SUM(value) FROM health_activities WHERE user_id=X AND activity_type='water' AND DATE(timestamp)=today`
- Response: "You drank 2 glasses of water today! 💧"

### Test Case 3: "Did I exercise today?"
**Current Behavior:**
1. Intent detection → `general_chat` or `activity_logging`
2. No database query
3. **Result**: Generic response or asks to log exercise

**Expected Behavior:**
- Query database for exercise entries today
- Response: "Yes! You logged 30 minutes of exercise today. Great job! 🏃" OR "Not yet! Want to log some exercise?"

## Why It Doesn't Work

### 1. Intent Gap
The LLM intent extractor doesn't have an intent for "retrieve my activity data". The prompt in `intent_extractor.py` defines:
- `activity_logging` - For LOGGING new activities
- `activity_query` - For GETTING SUGGESTIONS (e.g., "what activity for stress")
- But NO intent for "show me what I already logged"

### 2. Workflow Gap
Even if we added the intent, there's no workflow to:
- Parse the query (which activity? which timeframe?)
- Query the database
- Format the response

### 3. LLM Limitation
The `GeneralWorkflow` uses LLM for responses, but the LLM:
- Has NO access to the database
- Can't see user's actual logged activities
- Can only generate generic text

## Solution Architecture

### Option 1: Add Activity Summary Workflow (Recommended)

**New Intent**: `activity_summary`
- Triggers: "what did I do", "show my activities", "how much X did I", "did I log X"

**New Workflow**: `ActivitySummaryWorkflow`
```python
class ActivitySummaryWorkflow(BaseWorkflow):
    def start(self, message, state, user_id):
        # 1. Parse query
        query_type = self._detect_query_type(message)
        # - "all_activities" → "what did I do today"
        # - "specific_activity" → "how much water"
        # - "yes_no_check" → "did I exercise"
        
        # 2. Query database
        if query_type == "all_activities":
            activities = health_logger.get_today_activities(user_id)
            response = self._format_daily_summary(activities)
        
        elif query_type == "specific_activity":
            activity_type = self._extract_activity_type(message)
            data = health_logger.get_activity_summary(user_id, activity_type, days=1)
            response = self._format_specific_activity(activity_type, data)
        
        elif query_type == "yes_no_check":
            activity_type = self._extract_activity_type(message)
            exists = self._check_activity_logged_today(user_id, activity_type)
            response = self._format_yes_no_response(activity_type, exists)
        
        return WorkflowResponse(message=response, completed=True)
```

**Update Intent Extractor Prompt**:
```
4) activity_summary
User asks to VIEW/RETRIEVE their logged activities or health data.
This is DIFFERENT from activity_logging (which is for LOGGING new data).

Examples:
"What did I do today?"
"Show me my activities"
"How much water did I drink?"
"Did I exercise today?"
"What's my water intake today?"
"Show me my sleep log"

IMPORTANT:
- "I drank 2 glasses" = activity_logging (LOGGING new data)
- "How much did I drink" = activity_summary (RETRIEVING logged data)
```

### Option 2: Enhance General Workflow (Quick Fix)

Add activity summary detection to `GeneralWorkflow`:
```python
def start(self, message, state, user_id):
    # Check if this is an activity summary request
    if self._is_activity_summary_request(message):
        return self._handle_activity_summary(message, user_id)
    
    # ... existing general chat logic
```

**Pros**: Quick to implement
**Cons**: Makes GeneralWorkflow bloated, harder to maintain

## Recommendation

**Implement Option 1** - Create dedicated `ActivitySummaryWorkflow`

### Why:
1. **Separation of Concerns**: Each workflow has a clear purpose
2. **Maintainability**: Easy to add features (weekly summaries, comparisons, etc.)
3. **Testability**: Can test activity summary logic independently
4. **Scalability**: Can add more query types without bloating other workflows

### Implementation Steps:
1. Add `activity_summary` intent to `IntentExtractor`
2. Create `ActivitySummaryWorkflow` class
3. Register workflow in `WorkflowRegistry`
4. Add query parsing logic (detect activity type, timeframe)
5. Add response formatting (daily summary, specific activity, yes/no)
6. Add tests

### Estimated Complexity: **Medium**
- New intent: 30 minutes
- New workflow: 2-3 hours
- Testing: 1 hour
- **Total**: ~4 hours

## Example Responses After Implementation

**Query**: "What did I do today?"
```
Here's your activity summary for today:

💧 Water: 2 glasses
😴 Sleep: 7 hours
🏃 Exercise: 30 minutes
😊 Mood: Happy (logged at 9:00 AM)

Great job staying active! 🌟
```

**Query**: "How much water did I drink?"
```
You drank 2 glasses of water today! 💧

Your daily goal is 8 glasses. You need 6 more glasses to reach your goal.

Want to log more water?
[Log Water] button
```

**Query**: "Did I exercise today?"
```
Yes! You logged 30 minutes of exercise today. 🏃

Keep up the great work! 💪
```

**Query**: "Show me my sleep"
```
Sleep Summary (Last 7 Days):

📅 Today: 7 hours
📅 Yesterday: 6.5 hours
📅 Mar 4: 8 hours
📅 Mar 3: 7 hours
📅 Mar 2: 6 hours
📅 Mar 1: 7.5 hours
📅 Feb 29: 8 hours

Average: 7.1 hours/night 😴
```
