# MoodCapture Complete System Documentation

## 📚 Documentation Index

This comprehensive documentation covers all aspects of the MoodCapture wellness chatbot system.

### Part 1: APIs & Architecture
**File**: `SYSTEM_DOCUMENTATION_PART1_APIS.md`

**Topics Covered**:
- Main chat endpoint (`/api/v1/chat/message`)
- Initialization endpoint (`/api/v1/chat/init`)
- ChatService architecture
- Request/response flow
- API integration points

**Key Files Referenced**:
- `backend/app/api/v1/endpoints/chat.py`
- `backend/app/services/chat_service.py`
- `backend/app/repositories/chat_repository.py`

---

### Part 2: LLM Usage & Token Management
**File**: `SYSTEM_DOCUMENTATION_PART2_LLM.md`

**Topics Covered**:
- When LLMs are called (3 scenarios)
- Token usage breakdown
- Cost analysis ($75-100/month for 1000 users)
- LLM optimization strategies
- Rule-based vs LLM decision making

**Key Metrics**:
- LLM usage: 30% of messages
- Average tokens per call: 470-570
- Monthly token usage: 75M tokens

**Key Files Referenced**:
- `backend/chat_assistant/llm_service.py`
- `backend/chat_assistant/llm_intent_detector.py`
- `backend/chat_assistant/domain/llm/intent_extractor.py`

---

### Part 3: Suggestion System
**File**: `SYSTEM_DOCUMENTATION_PART3_SUGGESTIONS.md`

**Topics Covered**:
- Intelligent suggestion engine
- Weighted scoring algorithm (mood 40%, history 30%, time 15%, etc.)
- Suggestion tracking and analytics
- Integration with mood logging
- Personalization based on user behavior

**Key Tables**:
- `suggestion_master` - Available activities
- `suggestion_history` - Tracking shown/accepted/rejected
- `suggestion_ranking_context` - Analytics data

**Key Files Referenced**:
- `backend/chat_assistant/intelligent_suggestions.py`
- `backend/chat_assistant/domain/llm/suggestion_ranker.py`
- `backend/app/services/ranking_context_logger.py`

---

### Part 4: Context-Aware Chat & Memory
**File**: `SYSTEM_DOCUMENTATION_PART4_CONTEXT.md`

**Topics Covered**:
- 3-layer memory system (session, recent, long-term)
- Context detection and resolution
- Pronoun resolution ("it", "that")
- Conversation continuity
- Memory optimization strategies

**Memory Layers**:
1. **Session Memory**: In-memory state (current conversation)
2. **Recent History**: Last 10 messages from database
3. **Long-term Memory**: User profile and behavioral patterns

**Key Files Referenced**:
- `backend/app/services/context_aware_response_engine.py`
- `backend/chat_assistant/context_detector.py`
- `backend/app/services/session_tracker.py`
- `backend/app/services/user_data_analyzer.py`

---

### Part 5: Insight System
**File**: `SYSTEM_DOCUMENTATION_PART5_INSIGHTS.md`

**Topics Covered**:
- Pattern detection (mood trends, correlations, time patterns)
- LLM-powered insight generation
- Daily insight pipeline
- Data analysis methods
- Insight display strategies

**Insight Types**:
- Mood trends (improving/declining)
- Activity correlations (exercise → better mood)
- Time patterns (stressed on Mondays)
- Behavioral trends (sleep declining)

**Key Files Referenced**:
- `backend/app/services/insight_system.py`
- `backend/app/services/pattern_detector.py`
- `backend/app/services/llm_insight_generator.py`

---

### Part 6: Challenge System
**File**: `SYSTEM_DOCUMENTATION_PART6_CHALLENGES.md`

**Topics Covered**:
- Challenge enrollment and tracking
- Progress calculation
- Points and rewards system
- Challenge types (mood, activity, meditation)
- Automatic progress updates
- Completion detection

**Database Tables**:
- `challenges` - Available challenges
- `user_challenges` - User enrollments
- `challenge_progress` - Daily progress tracking
- `user_points` - Points and streaks

**Key Files Referenced**:
- `backend/app/services/challenge_service.py`
- `backend/app/repositories/challenge_repository.py`
- `backend/chat_assistant/challenges_workflow.py`

---

### Part 7: System Analysis (Pros & Cons)
**File**: `SYSTEM_DOCUMENTATION_PART7_PROS_CONS.md`

**Topics Covered**:
- Architecture strengths and weaknesses
- Scalability concerns
- Security and privacy issues
- Performance optimization opportunities
- Priority improvements roadmap

**Overall Score**: 6.6/10 (Solid MVP, needs production hardening)

**Top 5 Priority Improvements**:
1. Add Redis caching
2. Implement rate limiting
3. Add error tracking (Sentry)
4. Encrypt sensitive data
5. Add LLM fallbacks

---

## 🗂️ Quick Reference

### Database Tables (26 total)

**Core Tables**:
- `users` - User accounts
- `chat_messages` - Conversation history
- `mood_logs` - Mood tracking
- `health_activities` - Activity logging

**Suggestion System**:
- `suggestion_master` - Available activities
- `suggestion_history` - Interaction tracking
- `suggestion_ranking_context` - Analytics
- `user_behavior_metrics` - User patterns

**Challenge System**:
- `challenges` - Available challenges
- `user_challenges` - Enrollments
- `challenge_progress` - Daily tracking
- `user_points` - Points and rewards

**Content System**:
- `content_categories` - Content types
- `content_items` - Wellness content
- `user_content_interactions` - View tracking

**Preferences**:
- `user_wellness_preferences` - User settings

### Key Workflows

1. **Mood Logging**: `backend/chat_assistant/mood_workflow.py`
2. **Activity Tracking**: `backend/chat_assistant/activity_workflow.py`
3. **Challenges**: `backend/chat_assistant/challenges_workflow.py`
4. **General Chat**: `backend/chat_assistant/general_workflow.py`
5. **Activity Queries**: `backend/chat_assistant/activity_query_workflow.py`

### API Endpoints

```
POST /api/v1/auth/register - User registration
POST /api/v1/auth/login - User login
POST /api/v1/chat/init - Initialize conversation
POST /api/v1/chat/message - Send message
GET  /api/v1/activity/history - Get activity history
POST /api/v1/activity/log - Log activity
GET  /api/v1/analytics/insights - Get insights
```

### Environment Variables

```
DATABASE_URL=backend/mood_capture.db
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=150
OPENAI_TEMPERATURE=0.7
JWT_SECRET_KEY=your_secret_key
```

---

## 📊 System Metrics

### Performance
- Average response time: <500ms
- LLM response time: 1-2s
- Database query time: <50ms

### Usage
- LLM calls: 30% of messages
- Rule-based: 70% of messages
- Average session: 10-15 messages

### Cost
- Monthly LLM cost: $75-100 (1000 users)
- Cost per user: $0.075-0.10/month
- Cost per message: $0.005-0.007

### Scale
- Current: Supports 1000 concurrent users
- Database: SQLite (single file)
- Bottleneck: Concurrent writes to SQLite

---

## 🚀 Getting Started

1. **Read Part 1** to understand the API architecture
2. **Read Part 2** to understand LLM usage and costs
3. **Read Part 4** to understand how context works
4. **Read Part 7** to understand limitations and improvements

---

## 📞 Support

For questions about specific components:
- APIs: See Part 1
- LLM costs: See Part 2
- Suggestions: See Part 3
- Context/Memory: See Part 4
- Insights: See Part 5
- Challenges: See Part 6
- System issues: See Part 7

---

**Last Updated**: February 27, 2026
**Version**: 1.0
**Status**: Production MVP
