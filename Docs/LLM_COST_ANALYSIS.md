# OpenAI API Cost Analysis for Wellness Chatbot

## Current Configuration

**Model**: GPT-4o-mini  
**Temperature**: 0.1 (deterministic responses)  
**Provider**: OpenAI

## GPT-4o-mini Pricing (as of 2024)

- **Input tokens**: $0.150 per 1M tokens ($0.00000015 per token)
- **Output tokens**: $0.600 per 1M tokens ($0.00000060 per token)

**Note**: GPT-4o-mini is OpenAI's most cost-effective model, ~60x cheaper than GPT-4.

## LLM Call Patterns in Your Chatbot

### 1. Intent Detection (Every Message)

**File**: `intent_extractor.py`  
**Frequency**: 1 call per user message  
**Token Usage**:
- Input: ~400 tokens (prompt + conversation history)
- Output: ~50 tokens (JSON response)

**Cost per call**: $0.00009

### 2. Response Generation (Most Messages)

**File**: `response_phraser.py`  
**Frequency**: ~70% of messages (when not using templates)  
**Token Usage**:
- Input: ~500 tokens (prompt + conversation context)
- Output: ~60 tokens (1-3 sentences)

**Cost per call**: $0.000111

### 3. Mood Extraction (Mood Messages Only)

**File**: `mood_extractor.py`  
**Frequency**: ~15% of messages  
**Token Usage**:
- Input: ~200 tokens
- Output: ~20 tokens

**Cost per call**: $0.000042

### 4. Activity Acknowledgment (Activity Logging)

**File**: `activity_workflow.py`  
**Frequency**: ~20% of messages  
**Token Usage**:
- Input: ~300 tokens
- Output: ~40 tokens

**Cost per call**: $0.000069

### 5. Suggestion Ranking (When Showing Suggestions)

**File**: `suggestion_ranker.py`  
**Frequency**: ~10% of messages  
**Token Usage**:
- Input: ~600 tokens (includes activity list)
- Output: ~100 tokens (ranked JSON)

**Cost per call**: $0.00015

## Cost Per User Interaction

### Typical Message Flow

**Example**: User says "I'm stressed"

1. **Intent Detection**: $0.00009
2. **Response Generation**: $0.000111
3. **Mood Extraction**: $0.000042

**Total**: ~$0.000243 per message

### Average Cost Per Message

Based on typical usage patterns:

| Scenario | LLM Calls | Cost |
|----------|-----------|------|
| Simple greeting | 1 (intent only) | $0.00009 |
| Activity logging | 2 (intent + response) | $0.00020 |
| Mood logging | 3 (intent + mood + response) | $0.00024 |
| Challenge query | 2 (intent + response) | $0.00020 |
| General chat | 2 (intent + response) | $0.00020 |

**Average**: ~$0.00020 per message

## Monthly Cost Projections

### Scenario 1: Small User Base (100 active users)

**Assumptions**:
- 100 active users/month
- 10 messages per user per day
- 30 days per month

**Calculation**:
```
100 users × 10 messages/day × 30 days × $0.00020 = $6.00/month
```

**Monthly Cost**: $6.00

### Scenario 2: Medium User Base (1,000 active users)

**Assumptions**:
- 1,000 active users/month
- 10 messages per user per day
- 30 days per month

**Calculation**:
```
1,000 users × 10 messages/day × 30 days × $0.00020 = $60.00/month
```

**Monthly Cost**: $60.00

### Scenario 3: Large User Base (10,000 active users)

**Assumptions**:
- 10,000 active users/month
- 10 messages per user per day
- 30 days per month

**Calculation**:
```
10,000 users × 10 messages/day × 30 days × $0.00020 = $600.00/month
```

**Monthly Cost**: $600.00

### Scenario 4: Enterprise Scale (100,000 active users)

**Assumptions**:
- 100,000 active users/month
- 10 messages per user per day
- 30 days per month

**Calculation**:
```
100,000 users × 10 messages/day × 30 days × $0.00020 = $6,000.00/month
```

**Monthly Cost**: $6,000.00

## Cost Optimization Strategies

### 1. Template Responses (Already Implemented) ✅

**Current Implementation**: `response_templates.py`

**Savings**: ~30% reduction in LLM calls

Common questions answered with 0 LLM calls:
- "What can you do?"
- "How do I log water?"
- "What are challenges?"

**Impact**: Saves ~$1.80/month per 100 users

### 2. Caching Conversation Context

**Potential Implementation**: Cache recent conversation history in Redis

**Savings**: ~10% reduction in input tokens

**Impact**: Saves ~$0.60/month per 100 users

### 3. Batch Intent Detection

**Potential Implementation**: Detect multiple intents in one call

**Savings**: ~5% reduction in LLM calls for multi-intent messages

**Impact**: Saves ~$0.30/month per 100 users

### 4. Use Smaller Context Window

**Current**: Passing last 10 messages (~500 tokens)  
**Optimized**: Pass last 6 messages (~300 tokens)

**Savings**: ~20% reduction in input tokens

**Impact**: Saves ~$1.20/month per 100 users

### 5. Prompt Optimization

**Current**: Verbose prompts with examples  
**Optimized**: Concise prompts with fewer examples

**Savings**: ~15% reduction in input tokens

**Impact**: Saves ~$0.90/month per 100 users

## Cost Comparison: GPT-4o-mini vs Other Models

### GPT-4o-mini (Current)
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- **Cost per message**: $0.00020

### GPT-4o
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- **Cost per message**: $0.00325
- **16x more expensive**

### GPT-4 Turbo
- Input: $10.00 per 1M tokens
- Output: $30.00 per 1M tokens
- **Cost per message**: $0.01050
- **52x more expensive**

### Claude 3 Haiku (Alternative)
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens
- **Cost per message**: $0.00033
- **1.65x more expensive**

**Conclusion**: GPT-4o-mini is the most cost-effective choice.

## Real-World Cost Examples

### Example 1: Startup (500 users)

**Usage**:
- 500 active users
- 8 messages/user/day
- 30 days/month

**Monthly Cost**: $24.00

**Annual Cost**: $288.00

### Example 2: Growing App (5,000 users)

**Usage**:
- 5,000 active users
- 12 messages/user/day
- 30 days/month

**Monthly Cost**: $360.00

**Annual Cost**: $4,320.00

### Example 3: Established Platform (50,000 users)

**Usage**:
- 50,000 active users
- 15 messages/user/day
- 30 days/month

**Monthly Cost**: $4,500.00

**Annual Cost**: $54,000.00

## Cost Per User Metrics

| User Base | Monthly Cost | Cost Per User |
|-----------|--------------|---------------|
| 100 | $6.00 | $0.06 |
| 1,000 | $60.00 | $0.06 |
| 10,000 | $600.00 | $0.06 |
| 100,000 | $6,000.00 | $0.06 |

**Average**: $0.06 per user per month

## Revenue Implications

### Freemium Model

**Free Tier**:
- 50 messages/month per user
- Cost: $0.01/user/month
- Sustainable with ads or premium upsell

**Premium Tier** ($4.99/month):
- Unlimited messages
- Cost: ~$0.06/user/month
- Profit margin: 98.8%

### Subscription Model

**Basic** ($2.99/month):
- 200 messages/month
- Cost: $0.04/user/month
- Profit margin: 98.7%

**Pro** ($9.99/month):
- Unlimited messages
- Cost: $0.06/user/month
- Profit margin: 99.4%

## Cost Monitoring Recommendations

### 1. Track Token Usage

```python
# Add to llm_service.py
def log_token_usage(prompt_tokens, completion_tokens, cost):
    logger.info(f"Tokens: {prompt_tokens} in, {completion_tokens} out | Cost: ${cost:.6f}")
```

### 2. Set Budget Alerts

Configure OpenAI dashboard:
- Alert at $50/month
- Hard limit at $100/month (for testing)
- Adjust based on user growth

### 3. Monitor Per-User Costs

Track users with abnormally high usage:
- Flag users with >100 messages/day
- Implement rate limiting if needed

### 4. A/B Test Optimizations

Test cost optimizations:
- Shorter context windows
- Fewer examples in prompts
- Template response coverage

## Summary

### Current State

✅ **Very cost-effective**: $0.00020 per message  
✅ **Scalable**: Linear cost growth with users  
✅ **Optimized**: Using cheapest suitable model (GPT-4o-mini)  
✅ **Template responses**: Already reducing 30% of LLM calls

### Cost Breakdown

- **Per message**: $0.00020
- **Per user/month**: $0.06 (at 10 messages/day)
- **Per 1,000 users/month**: $60.00

### Recommendations

1. **Keep GPT-4o-mini** - Best price/performance ratio
2. **Expand template responses** - Target 50% coverage
3. **Implement caching** - Reduce input tokens by 10%
4. **Monitor usage** - Set alerts and track anomalies
5. **Consider rate limiting** - Prevent abuse (>100 messages/day)

### Bottom Line

Your chatbot is **extremely cost-efficient**. Even with 10,000 active users sending 10 messages/day, you'd only spend **$600/month** on OpenAI API calls. This is sustainable for any freemium or subscription model.
