# LLM Token Tracking - Quick Start

## ✅ System is Now Tracking All LLM Calls!

Every time your system calls the LLM (OpenAI), it automatically tracks:
- Token usage (input + output)
- Cost in USD
- Response latency
- Success/failure
- User ID and call type

## 📊 View Usage Statistics

```bash
# View last 7 days
python backend/view_llm_usage.py

# View last 30 days
python backend/view_llm_usage.py stats 30

# View recent calls
python backend/view_llm_usage.py recent 20

# View usage for specific user
python backend/view_llm_usage.py user 18
```

## 🔍 Monitor in Real-Time

```bash
# Watch LLM calls as they happen (live)
python backend/monitor_llm_realtime.py
```

This shows each call instantly with tokens, cost, and latency.

## 📈 What Gets Tracked

The system tracks these call types:
1. **intent_detection** - When detecting what user wants
2. **response_generation** - When generating chat responses
3. **insight_generation** - When creating daily insights
4. **structured_intent** - When using structured JSON output

## 💰 Cost Information

Current pricing (GPT-3.5-turbo / GPT-4o-mini):
- Input tokens: ~$0.0005 per 1K tokens
- Output tokens: ~$0.0015 per 1K tokens

Typical costs per call:
- Intent detection: $0.0001
- Response generation: $0.0003
- Insight generation: $0.0008

## 📊 Example Output

```
LLM USAGE STATISTICS - Last 7 Days
====================================

📊 OVERALL STATS
   Total Calls: 150
   Total Tokens: 75,000
   Total Cost: $0.05
   Success Rate: 98.5%
   Avg Latency: 850ms

📈 BY CALL TYPE
   intent_detection: 100 calls, $0.02
   response_generation: 40 calls, $0.02
   insight_generation: 10 calls, $0.01

💰 COST PROJECTIONS
   Daily Average: $0.007
   Monthly Projection: $0.21
   Yearly Projection: $2.56
```

## 🔧 How It Works

1. **Automatic Tracking**: Every LLM call is automatically logged
2. **Database Storage**: All data stored in `llm_usage_log` table
3. **Token Counting**: Estimates tokens (install `tiktoken` for exact counts)
4. **Cost Calculation**: Automatically calculates cost based on model pricing

## 📁 Files Created

- `backend/app/services/llm_token_tracker.py` - Core tracking service
- `backend/chat_assistant/llm_service_with_tracking.py` - Tracked LLM wrapper
- `backend/view_llm_usage.py` - View statistics
- `backend/monitor_llm_realtime.py` - Real-time monitoring
- `backend/test_llm_tracking.py` - Test the system
- `backend/LLM_TRACKING_GUIDE.md` - Complete documentation

## 🚀 Next Steps

1. **Monitor regularly**: Run `python backend/view_llm_usage.py` daily
2. **Set alerts**: Alert if daily cost exceeds threshold
3. **Optimize**: Identify expensive call types and optimize them
4. **Install tiktoken**: For exact token counts: `pip install tiktoken`

## 💡 Tips

- Check usage before month-end to avoid surprises
- Monitor latency to ensure good user experience
- Track per-user usage to identify power users
- Use real-time monitor during development/testing

## ✅ Verification

Run the test to verify everything works:
```bash
python backend/test_llm_tracking.py
```

You should see 3 test calls tracked successfully!
