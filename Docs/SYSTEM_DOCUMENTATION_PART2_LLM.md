# MoodCapture System Documentation - Part 2: LLM Usage

## 2. LLM Integration & Token Usage

### LLM Service Architecture
**File**: `backend/chat_assistant/llm_service.py`

### When LLMs Are Called

The system uses LLMs in **3 specific scenarios**:

#### Scenario 1: Intent Detection (Most Common)
**File**: `backend/chat_assistant/llm_intent_detector.py`
**Frequency**: Every ambiguous user message

```python
def detect_intent_with_llm(message: str, conversation_history: list) -> dict:
    """
    Called when rule-based detection fails
    
    Example triggers:
    - "I want to track something" (ambiguous)
    - "How am I doing?" (needs context)
    - "Tell me about my progress" (complex query)
    
    Token Usage: ~200-500 tokens per call
    """
```

**LLM Call Count**: 30-40% of messages (others use rule-based)

#### Scenario 2: Response Generation (Rare)
**File**: `backend/chat_assistant/general_workflow.py`
**Frequency**: Only for open-ended conversations

```python
def generate_conversational_response(message: str, context: dict) -> str:
    """
    Called for general chat that doesn't fit workflows
    
    Example triggers:
    - "Tell me a joke"
    - "What do you think about meditation?"
    - Complex questions
    
    Token Usage: ~300-800 tokens per call
    """
```

**LLM Call Count**: 5-10% of messages

#### Scenario 3: Insight Generation (Scheduled)
**File**: `backend/app/services/llm_insight_generator.py`
**Frequency**: Once per day per user (background job)

```python
def generate_insights(user_id: int, data: dict) -> list:
    """
    Analyzes user data to generate insights
    
    Runs: Daily at midnight or on-demand
    
    Token Usage: ~1000-2000 tokens per user
    """
```

**LLM Call Count**: 1 per user per day

### Total LLM Usage Per User Session

**Typical 10-message conversation**:
```
Message 1: "Hi" → No LLM (rule-based greeting)
Message 2: "Log mood" → No LLM (keyword match)
Message 3: "😊" → No LLM (emoji detection)
Message 4: "I exercised" → No LLM (keyword match)
Message 5: "How am I doing?" → LLM CALL #1 (intent detection)
Message 6: "Show my progress" → LLM CALL #2 (intent detection)
Message 7: "Thanks" → No LLM (keyword match)
Message 8: "Log water" → No LLM (keyword match)
Message 9: "Tell me about meditation" → LLM CALL #3 (response gen)
Message 10: "Bye" → No LLM (keyword match)

Total LLM Calls: 3 out of 10 messages (30%)
```

### Token Usage Breakdown

**Per LLM Call**:
```
Input Tokens:
- System prompt: ~150 tokens
- Conversation history (10 msgs): ~200 tokens
- Current message: ~20 tokens
- Context data: ~50 tokens
Total Input: ~420 tokens

Output Tokens:
- Intent detection: ~50 tokens
- Response generation: ~150 tokens
Total Output: ~50-150 tokens

Total per call: ~470-570 tokens
```

**Monthly Usage (1000 active users)**:
```
Average messages per user per day: 15
LLM calls per user per day: 5 (33%)
Tokens per LLM call: 500

Daily: 1000 users × 5 calls × 500 tokens = 2,500,000 tokens
Monthly: 2.5M × 30 = 75,000,000 tokens (75M)

Cost (GPT-3.5-turbo):
- Input: $0.50 per 1M tokens
- Output: $1.50 per 1M tokens
- Monthly: ~$75-100
```

### LLM Configuration

**File**: `backend/.env`
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=150
OPENAI_TEMPERATURE=0.7
```

### LLM Call Optimization

**Current Optimizations**:
1. Rule-based intent detection first (70% of messages)
2. Conversation history limited to 10 messages
3. Caching for repeated queries
4. Batch processing for insights

**Files Involved**:
- `backend/chat_assistant/llm_service.py` - Core LLM wrapper
- `backend/chat_assistant/llm_intent_detector.py` - Intent detection
- `backend/chat_assistant/domain/llm/intent_extractor.py` - Intent parsing
- `backend/chat_assistant/domain/llm/response_phraser.py` - Response formatting
