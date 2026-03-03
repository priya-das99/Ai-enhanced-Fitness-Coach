# MoodCapture System Documentation - Part 5: Insight System

## 6. Insight System Architecture

### Overview
The insight system analyzes user data to generate personalized wellness insights and recommendations.

### System Flow

```
Daily Cron Job → Pattern Detector → LLM Insight Generator → Store Insights → Show in Chat
```

### Core Components

#### 6.1 Pattern Detector
**File**: `backend/app/services/pattern_detector.py`

```python
class PatternDetector:
    def detect_patterns(user_id: int, days: int = 7):
        """
        Analyzes user data to find patterns
        
        Detects:
        1. Mood patterns (trending up/down)
        2. Activity correlations (exercise → better mood)
        3. Time-based patterns (stressed on Mondays)
        4. Behavioral trends (sleep declining)
        
        Returns: List of detected patterns
        """
```

**Pattern Types**:

**1. Mood Trends**
```python
{
    "type": "mood_trend",
    "pattern": "improving",
    "data": {
        "avg_mood_last_7_days": 4.2,
        "avg_mood_prev_7_days": 3.5,
        "change": "+20%"
    }
}
```

**2. Activity Correlations**
```python
{
    "type": "activity_correlation",
    "pattern": "exercise_improves_mood",
    "data": {
        "activity": "exercise",
        "mood_before": 3.0,
        "mood_after": 4.5,
        "correlation": 0.85
    }
}
```

**3. Time Patterns**
```python
{
    "type": "time_pattern",
    "pattern": "monday_stress",
    "data": {
        "day": "Monday",
        "avg_stress": 4.2,
        "other_days_avg": 2.8
    }
}
```

#### 6.2 LLM Insight Generator
**File**: `backend/app/services/llm_insight_generator.py`

```python
class LLMInsightGenerator:
    def generate_insights(user_id: int, patterns: list):
        """
        Uses LLM to create human-readable insights
        
        Input: Raw patterns from detector
        Output: Friendly, actionable insights
        
        LLM Prompt:
        "Based on this user's data, generate 3 personalized insights:
        - Mood has improved 20% this week
        - Exercise correlates with better mood
        - Stress peaks on Mondays
        
        Make insights:
        1. Positive and encouraging
        2. Actionable
        3. Specific to user's data"
        """
```

**Example LLM Output**:
```json
[
    {
        "insight": "Great progress! Your mood has improved 20% this week. Keep up the good work!",
        "type": "positive_trend",
        "action": "Continue your current wellness routine"
    },
    {
        "insight": "Exercise seems to boost your mood significantly. You feel 50% better after workouts.",
        "type": "correlation",
        "action": "Try exercising when you're feeling down"
    },
    {
        "insight": "Mondays tend to be stressful for you. Consider starting the week with a calming activity.",
        "type": "time_pattern",
        "action": "Schedule meditation on Monday mornings"
    }
]
```

#### 6.3 Insight System Service
**File**: `backend/app/services/insight_system.py`

```python
class InsightSystem:
    def generate_daily_insights(user_id: int):
        """
        Main insight generation pipeline
        
        Steps:
        1. Check if user has enough data (min 7 days)
        2. Detect patterns using PatternDetector
        3. Generate insights using LLM
        4. Store insights in database
        5. Mark for display in next chat session
        
        Runs: Daily at midnight via cron job
        """
    
    def get_insights_for_display(user_id: int):
        """
        Retrieves insights to show user
        
        Rules:
        - Show max 3 insights per day
        - Prioritize new insights
        - Don't repeat same insight within 7 days
        - Show positive insights first
        """
```

### Data Analysis

#### Mood Analysis
```python
def analyze_mood_trends(user_id: int):
    """
    Analyzes mood logs over time
    
    Queries:
    - Average mood by day of week
    - Mood trend (7-day moving average)
    - Most common mood reasons
    - Mood volatility (standard deviation)
    """
    
    # SQL Query
    SELECT 
        DATE(timestamp) as date,
        AVG(mood_value) as avg_mood,
        COUNT(*) as log_count
    FROM mood_logs
    WHERE user_id = ? AND timestamp >= date('now', '-30 days')
    GROUP BY DATE(timestamp)
```

#### Activity Analysis
```python
def analyze_activity_impact(user_id: int):
    """
    Correlates activities with mood changes
    
    Logic:
    1. Get all activities with timestamps
    2. Get mood logs before and after activities
    3. Calculate mood delta
    4. Identify activities with positive impact
    """
    
    # Example result
    {
        "meditation": {"avg_mood_improvement": +1.5},
        "exercise": {"avg_mood_improvement": +1.2},
        "sleep": {"avg_mood_improvement": +0.8}
    }
```

#### Behavioral Analysis
```python
def analyze_behavioral_patterns(user_id: int):
    """
    Analyzes health metrics trends
    
    Metrics:
    - Sleep: Average hours, trend
    - Water: Daily intake, consistency
    - Exercise: Frequency, duration
    - Mood: Correlation with behaviors
    """
```

### Insight Display

#### When Insights Are Shown

**1. Proactive Display (Morning Greeting)**
```python
# File: backend/chat_assistant/general_workflow.py

def handle_greeting(user_id):
    insights = InsightSystem.get_insights_for_display(user_id)
    
    if insights:
        return f"Good morning! Here's your wellness insight: {insights[0]}"
```

**2. On User Request**
```python
User: "How am I doing?"
Bot: Shows insights + recent trends
```

**3. After Milestone**
```python
# User completes 7-day streak
Bot: "Amazing! You've logged your mood for 7 days straight. 
      Your average mood has improved by 15%!"
```

### Database Schema

#### Insights Storage (Conceptual - not implemented yet)
```sql
CREATE TABLE user_insights (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    insight_text TEXT,
    insight_type TEXT,  -- 'trend', 'correlation', 'milestone'
    data_snapshot TEXT,  -- JSON with supporting data
    generated_at DATETIME,
    shown_at DATETIME,
    user_reaction TEXT  -- 'helpful', 'not_helpful', null
)
```

### Integration with Chat

**File**: `backend/chat_assistant/general_workflow.py`

```python
def should_show_insight(user_id: int) -> bool:
    """
    Determines if insight should be shown
    
    Conditions:
    - User has new insights
    - Haven't shown insight today
    - User is in receptive state (not mid-workflow)
    """
    
def format_insight_message(insights: list) -> str:
    """
    Formats insights for chat display
    
    Returns:
    "📊 Your Wellness Insight:
    
    Great progress! Your mood has improved 20% this week.
    
    💡 Tip: Exercise seems to boost your mood. Try a quick
    workout when you're feeling down.
    
    [View More Insights] [Dismiss]"
    """
```

### Performance Considerations

**Optimization 1: Batch Processing**
```python
# Process all users at once (midnight)
def generate_insights_batch():
    users = get_active_users()
    for user_id in users:
        try:
            generate_daily_insights(user_id)
        except Exception as e:
            log_error(user_id, e)
```

**Optimization 2: Caching**
```python
# Cache patterns for 24 hours
@cache(ttl=86400)
def get_user_patterns(user_id):
    return PatternDetector.detect_patterns(user_id)
```

**Optimization 3: Incremental Analysis**
```python
# Only analyze new data since last run
def analyze_incremental(user_id, last_analysis_date):
    new_data = get_data_since(user_id, last_analysis_date)
    update_patterns(user_id, new_data)
```

### Files Involved

**Core Insight Logic**:
- `backend/app/services/insight_system.py` - Main orchestrator
- `backend/app/services/pattern_detector.py` - Pattern detection
- `backend/app/services/llm_insight_generator.py` - LLM generation

**Data Analysis**:
- `backend/app/services/user_data_analyzer.py` - Data aggregation
- `backend/app/services/behavior_scorer.py` - Metric calculation

**Display**:
- `backend/chat_assistant/general_workflow.py` - Chat integration
