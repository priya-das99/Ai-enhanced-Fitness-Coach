# MoodCapture System Documentation - Part 1: APIs & Architecture

## 1. Chat Assistant APIs

### Main Chat Endpoint
**File**: `backend/app/api/v1/endpoints/chat.py`

```python
POST /api/v1/chat/message
```

**Flow**:
```
User Message → API Endpoint → Chat Service → Workflow Registry → Specific Workflow → LLM (if needed) → Response
```

### Key API Functions

#### 1.1 `/api/v1/chat/message` - Main Chat Handler
**Location**: `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/message")
async def send_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    Main chat endpoint that processes all user messages
    
    Flow:
    1. Receives user message
    2. Saves to chat_messages table
    3. Calls ChatService.process_message()
    4. Returns bot response with UI elements
    """
```

**Request Body**:
```json
{
  "message": "I'm feeling stressed",
  "metadata": {
    "button_click": false,
    "emoji_selected": null
  }
}
```

**Response**:
```json
{
  "message": "I'm sorry you're feeling stressed...",
  "ui_elements": ["emoji_selector", "activity_buttons"],
  "suggestions": [...],
  "state": "awaiting_mood_reason"
}
```

#### 1.2 `/api/v1/chat/init` - Initialize Conversation
**Location**: `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/init")
async def init_conversation(current_user: dict = Depends(get_current_user)):
    """
    Called when user opens chat
    
    Returns:
    - Greeting message
    - Initial UI elements
    - Context-aware welcome (checks if mood logged today)
    """
```

### Core Service Layer

#### ChatService
**File**: `backend/app/services/chat_service.py`

```python
class ChatService:
    def process_message(user_id: int, message: str, metadata: dict):
        """
        Main orchestrator for chat processing
        
        Steps:
        1. Load conversation history (last 10 messages)
        2. Detect intent using workflow registry
        3. Route to appropriate workflow
        4. Get response from workflow
        5. Save response to database
        6. Return formatted response
        """
```

**Key Methods**:
- `process_message()` - Main entry point
- `_get_conversation_history()` - Loads recent messages
- `_save_message()` - Persists messages
- `_format_response()` - Structures API response

