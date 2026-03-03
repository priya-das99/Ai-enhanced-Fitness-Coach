# LLM Token Usage Tracking Guide

## Overview

The system now tracks all LLM API calls, token usage, and costs in real-time. This helps you:
- Monitor costs and optimize usage
- Debug LLM-related issues
- Analyze which features use the most tokens
- Track per-user LLM usage

## Quick Start

### 1. View Current Usage

```bash
# View last 7 days statistics
python backend/view_llm_usage.py

# View last 30 days
python backend/view_llm_usage.py stats 30

# View recent calls
python backend/view_llm_usage.py recent 20

# View usage for specific user
python backend/view_llm_usage.py user 18
```

### 2. Monitor in Real-Time

```bash
# Watch LLM calls as they happen
python backend/monitor_llm_realtime.py
```

This will show each LLM call as it occurs with:
- Timestamp
- Call type (intent_detection, response_generation, etc.)
- User ID
- Token counts (input → output)
- Cost
- Latency
- Running totals

### 3. Test the Tracking

```bash
# Run test to see tracking in action
python backend/test_llm_tracking.py
```

## Database Schema

All LLM calls are logged to the `llm_usage_log` table:

```sql
CREATE TABLE llm_usage_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,              -- User who triggered the call
    call_type TEXT,                -- 'intent_detection', 'response_generation', etc.
    model TEXT,                    -- 'gpt-3.5-turbo'
    input_tokens INTEGER,          -- Tokens sent to LLM
    output_tokens INTEGER,         -- Tokens received from LLM
    total_tokens INTEGER,          -- input + output
    estimated_cost REAL,           -- Cost in USD
    latency_ms INTEGER,            -- Response time in milliseconds
    success BOOLEAN,               -- Whether call succeeded
    error_message TEXT,            -- Error if failed
    context_data TEXT,             -- JSON with additional context
    timestamp DATETIME             -- When the call happened
)
```

## Call Types

The system tracks different types of LLM calls:

1. **intent_detection** - Detecting user intent from message
2. **response_generation** - Generating conversational responses
3. **insight_generation** - Generating daily insights
4. **structured_intent** - Structured JSON intent detection
5. **general** - Other LLM calls

## Using the Tracked LLM Service

### In Your Code

Replace regular LLM service with tracked version:

```python
# OLD (no tracking)
from chat_assistant.llm_service import get_llm_service
llm = get_llm_service()

# NEW (with tracking)
from chat_assistant.llm_service_with_tracking import get_tracked_llm_service
llm = get_tracked_llm_service()

# Use it the same way, but now it tracks automatically
response = llm.call(
    prompt="User message here",
    user_id=18,  # Add user_id for tracking
    call_type="intent_detection"  # Add call_type for analytics
)
```

### Example: Intent Detection with Tracking

```python
from chat_assistant.llm_service_with_tracking import get_tracked_llm_service

llm = get_tracked_llm_service()

response = llm.call(
    prompt=f"User said: '{user_message}'. What is their intent?",
    system_message="Detect intent: log_mood, activity_query, or unknown",
    max_tokens=20,
    temperature=0.1,
    user_id=user_id,
    call_type="intent_detection"
)

# Automatically tracked:
# - Input tokens counted
# - Output tokens counted
# - Cost calculated
# - Latency measured
# - Logged to database
```

## Viewing Statistics

### Overall Stats

```python
from app.services.llm_token_tracker import LLMTokenTracker

stats = LLMTokenTracker.get_usage_stats(days=7)

print(f"Total calls: {stats['total_calls']}")
print(f"Total tokens: {stats['total_tokens']:,}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Success rate: {stats['success_rate']:.1f}%")

# By call type
for call_type, data in stats['by_call_type'].items():
    print(f"{call_type}: {data['calls']} calls, ${data['cost']:.4f}")
```

### User-Specific Stats

```python
user_stats = LLMTokenTracker.get_user_usage(user_id=18, days=30)

print(f"User 18 used {user_stats['total_tokens']:,} tokens")
print(f"Cost: ${user_stats['total_cost']:.4f}")
```

### Recent Calls

```python
recent = LLMTokenTracker.get_recent_calls(limit=10)

for call in recent:
    print(f"{call['call_type']}: {call['total_tokens']} tokens, ${call['estimated_cost']:.4f}")
```

## Cost Analysis

### Current Pricing (GPT-3.5-turbo)

- Input: $0.50 per 1M tokens
- Output: $1.50 per 1M tokens

### Example Costs

```
Intent Detection (typical):
- Input: 150 tokens ($0.000075)
- Output: 10 tokens ($0.000015)
- Total: $0.00009 per call

Response Generation (typical):
- Input: 300 tokens ($0.00015)
- Output: 100 tokens ($0.00015)
- Total: $0.0003 per call

Insight Generation (daily):
- Input: 1000 tokens ($0.0005)
- Output: 200 tokens ($0.0003)
- Total: $0.0008 per user per day
```

### Monthly Projections

For 1000 active users:
- Average 15 messages/day per user
- 30% use LLM (5 calls/day)
- Average 500 tokens per call

```
Daily: 1000 users × 5 calls × 500 tokens = 2,500,000 tokens
Monthly: 2.5M × 30 = 75,000,000 tokens

Cost: ~$75-100/month
```

## Monitoring Best Practices

### 1. Set Up Daily Monitoring

```bash
# Add to cron (run daily at 9am)
0 9 * * * cd /path/to/project && python backend/view_llm_usage.py stats 1 > /tmp/llm_usage.txt && mail -s "Daily LLM Usage" you@email.com < /tmp/llm_usage.txt
```

### 2. Set Cost Alerts

```python
# Check if daily cost exceeds threshold
stats = LLMTokenTracker.get_usage_stats(days=1)
if stats['total_cost'] > 5.0:  # $5/day threshold
    send_alert(f"LLM cost exceeded: ${stats['total_cost']:.2f}")
```

### 3. Monitor Latency

```python
# Check if latency is too high
stats = LLMTokenTracker.get_usage_stats(days=1)
if stats['avg_latency_ms'] > 2000:  # 2 second threshold
    send_alert(f"LLM latency high: {stats['avg_latency_ms']}ms")
```

### 4. Track Success Rate

```python
# Check if too many failures
stats = LLMTokenTracker.get_usage_stats(days=1)
if stats['success_rate'] < 95:  # 95% threshold
    send_alert(f"LLM success rate low: {stats['success_rate']:.1f}%")
```

## Optimization Tips

### 1. Reduce Token Usage

```python
# BAD: Sending full conversation history
history = get_all_messages(user_id)  # Could be 100+ messages
llm.call(messages=history)

# GOOD: Limit to recent messages
history = get_recent_messages(user_id, limit=10)
llm.call(messages=history)
```

### 2. Use Rule-Based When Possible

```python
# Check if rule-based can handle it first
if can_handle_with_rules(message):
    return rule_based_response(message)
else:
    return llm.call(prompt=message, call_type="fallback")
```

### 3. Cache Common Queries

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_intent_cached(message):
    return llm.call(prompt=message, call_type="intent_detection")
```

### 4. Batch Processing

```python
# Process multiple users at once (for insights)
users = get_active_users()
for user_batch in chunks(users, 10):
    process_insights_batch(user_batch)
```

## Troubleshooting

### No Data Showing

```bash
# Check if table exists
python -c "from app.services.llm_token_tracker import LLMTokenTracker; LLMTokenTracker.create_table()"

# Check if tracking is enabled
python -c "from chat_assistant.llm_service import get_llm_service; print(get_llm_service().is_available())"
```

### High Costs

```bash
# Find which call types cost the most
python backend/view_llm_usage.py stats 7

# Check recent expensive calls
python -c "from app.services.llm_token_tracker import LLMTokenTracker; calls = LLMTokenTracker.get_recent_calls(50); expensive = [c for c in calls if c['estimated_cost'] > 0.001]; print(f'Found {len(expensive)} expensive calls')"
```

### Slow Responses

```bash
# Check latency by call type
python backend/view_llm_usage.py stats 1
# Look at "Avg Latency" for each call type
```

## API Endpoints (Optional)

You can add API endpoints to expose this data:

```python
# backend/app/api/v1/endpoints/admin.py

@router.get("/llm-usage")
async def get_llm_usage(days: int = 7):
    """Get LLM usage statistics"""
    return LLMTokenTracker.get_usage_stats(days=days)

@router.get("/llm-usage/user/{user_id}")
async def get_user_llm_usage(user_id: int, days: int = 30):
    """Get LLM usage for specific user"""
    return LLMTokenTracker.get_user_usage(user_id, days=days)
```

## Summary

The LLM tracking system provides:
- ✅ Real-time monitoring of all LLM calls
- ✅ Detailed token and cost tracking
- ✅ Per-user usage analytics
- ✅ Performance metrics (latency, success rate)
- ✅ Historical data for optimization

Use the provided scripts to monitor your LLM usage and optimize costs!
