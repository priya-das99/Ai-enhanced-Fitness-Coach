# Complete End-to-End Workflow - From Server Start to Chat

## 🚀 Phase 1: Server Startup

### Step 1: You Run the Server
```bash
python backend/app/main.py
# or
uvicorn app.main:app --reload
```

### Step 2: FastAPI Initializes
**File**: `backend/app/main.py`

```python
# What happens:
1. FastAPI app is created
2. CORS middleware is configured (allows frontend to connect)
3. API routers are registered:
   - /api/v1/auth (login, register)
   - /api/v1/chat (chat messages)
   - /api/v1/activity (activity logging)
   - /api/v1/analytics (insights)
4. Database connection is initialized
5. LLM service is initialized (OpenAI client)
6. Server starts listening on http://localhost:8000
```

**Console Output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ OpenAI client initialized (model: gpt-4o-mini)
```

---

## 🌐 Phase 2: Frontend Opens

### Step 3: You Open Browser
```
http://localhost:5500/frontend/index.html
```

### Step 4: Landing Page Loads
**File**: `frontend/index.html`

```html
<!-- What loads: -->
1. HTML structure
2. CSS styles (landing.css)
3. JavaScript (login.js)
4. Shows: "Welcome to MoodCapture" with Login/Register buttons
```

**What You See**:
```
┌─────────────────────────────────┐
│     🌟 MoodCapture              │
│                                 │
│   Track your wellness journey  │
│                                 │
│   [Login]  [Register]          │
└─────────────────────────────────┘
```

---

## 🔐 Phase 3: Login Process

### Step 5: You Click "Login"
**File**: `frontend/login.js`

```javascript
// What happens:
1. Login modal appears
2. You enter username: "ankur"
3. You enter password: "password123"
4. You click "Login" button
```

### Step 6: Login Request Sent
**Frontend** → **Backend**

```javascript
// frontend/login.js
fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'ankur',
        password: 'password123'
    })
})
```

### Step 7: Backend Authenticates
**File**: `backend/app/api/v1/endpoints/auth.py`

```python
@router.post("/login")
async def login(credentials: LoginRequest):
    # Step 7a: Find user in database
    user = db.query(User).filter(User.username == 'ankur').first()
    
    # Step 7b: Verify password
    if not verify_password('password123', user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    # Step 7c: Create JWT token
    token = create_access_token(data={"sub": user.username})
    
    # Step 7d: Update last_login timestamp
    user.last_login = datetime.now()
    db.commit()
    
    # Step 7e: Return token and user info
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": 18,
            "username": "ankur",
            "email": "ankur@example.com"
        }
    }
```

### Step 8: Frontend Stores Token
**File**: `frontend/login.js`

```javascript
// What happens:
1. Receives token from backend
2. Stores in localStorage:
   localStorage.setItem('token', 'eyJ0eXAiOiJKV1QiLCJhbGc...')
   localStorage.setItem('user', '{"id":18,"username":"ankur"}')
3. Redirects to chat page
```

---

## 💬 Phase 4: Chat Page Opens

### Step 9: Chat Page Loads
**File**: `frontend/chat.html`

```html
<!-- What loads: -->
1. Chat interface HTML
2. CSS styles (chat.css)
3. JavaScript (chat.js)
4. Checks for token in localStorage
5. If no token → redirect to login
6. If token exists → initialize chat
```

**What You See**:
```
┌─────────────────────────────────┐
│  MoodCapture Chat    [ankur] ⚙️ │
├─────────────────────────────────┤
│                                 │
│  [Chat messages appear here]   │
│                                 │
│                                 │
├─────────────────────────────────┤
│  Type a message...        [Send]│
└─────────────────────────────────┘
```

### Step 10: Initialize Chat Request
**Frontend** → **Backend**

```javascript
// frontend/chat.js - on page load
fetch('http://localhost:8000/api/v1/chat/init', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...',
        'Content-Type': 'application/json'
    }
})
```

### Step 11: Backend Initializes Chat
**File**: `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/init")
async def init_conversation(current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']  # 18
    
    # Step 11a: Check if mood logged today
    mood_logged_today = has_mood_log_for_today(user_id)
    
    # Step 11b: Get user's name
    user = get_user(user_id)
    
    # Step 11c: Determine greeting
    if mood_logged_today:
        message = f"Welcome back, {user.username}! Ready to track your wellness? 🌟"
        ui_elements = ['activity_buttons']
    else:
        message = f"Hi {user.username}! How are you feeling today? 😊"
        ui_elements = ['emoji_selector', 'activity_buttons']
    
    # Step 11d: Save greeting to chat_messages
    save_message(user_id, message, sender='bot')
    
    # Step 11e: Return response
    return {
        "message": message,
        "ui_elements": ui_elements,
        "suggestions": []
    }
```

### Step 12: Frontend Displays Greeting
**File**: `frontend/chat.js`

```javascript
// What happens:
1. Receives greeting from backend
2. Creates bot message bubble
3. Displays: "Hi ankur! How are you feeling today? 😊"
4. Shows emoji selector (😊 😐 😟 😢 😡)
5. Shows activity buttons (Log Mood, Log Water, etc.)
```

**What You See**:
```
┌─────────────────────────────────┐
│  Bot: Hi ankur! How are you     │
│       feeling today? 😊         │
│                                 │
│  😊 😐 😟 😢 😡                  │
│                                 │
│  [Log Mood] [Log Water]        │
│  [Log Sleep] [Log Exercise]    │
└─────────────────────────────────┘
```

---

## 💬 Phase 5: User Sends First Message

### Step 13: You Type and Send Message
```
You type: "I'm feeling stressed"
You click: Send button
```

### Step 14: Frontend Sends Message
**Frontend** → **Backend**

```javascript
// frontend/chat.js
fetch('http://localhost:8000/api/v1/chat/message', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: "I'm feeling stressed",
        metadata: {
            button_click: false,
            emoji_selected: null
        }
    })
})
```

### Step 15: Backend Receives Message
**File**: `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/message")
async def send_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user['id']  # 18
    user_message = message.message  # "I'm feeling stressed"
    
    # Step 15a: Save user message to database
    save_message(user_id, user_message, sender='user')
    
    # Step 15b: Process message
    response = ChatService.process_message(
        user_id=user_id,
        message=user_message,
        metadata=message.metadata
    )
    
    # Step 15c: Save bot response to database
    save_message(user_id, response['message'], sender='bot')
    
    # Step 15d: Return response
    return response
```

---

## 🧠 Phase 6: Message Processing (The Brain)

### Step 16: ChatService Processes Message
**File**: `backend/app/services/chat_service.py`

```python
class ChatService:
    @staticmethod
    def process_message(user_id, message, metadata):
        # Step 16a: Load conversation history (last 10 messages)
        history = get_conversation_history(user_id, limit=10)
        
        # Step 16b: Route to appropriate workflow
        response = WorkflowRegistry.route_message(
            user_id=user_id,
            message=message,
            history=history,
            metadata=metadata
        )
        
        return response
```

### Step 17: Workflow Registry Routes Message
**File**: `backend/chat_assistant/workflow_registry.py`

```python
class WorkflowRegistry:
    @staticmethod
    def route_message(user_id, message, history, metadata):
        # Step 17a: Try rule-based detection first
        intent = detect_intent_with_rules(message)
        
        if intent == 'log_mood':
            # Detected keywords: "feeling", "stressed"
            return MoodWorkflow.handle(user_id, message, history)
        
        elif intent == 'unknown':
            # Step 17b: Fall back to LLM for complex messages
            intent = detect_intent_with_llm(message, history)
            
            if intent == 'log_mood':
                return MoodWorkflow.handle(user_id, message, history)
            elif intent == 'activity_query':
                return ActivityQueryWorkflow.handle(user_id, message)
            else:
                return GeneralWorkflow.handle(user_id, message)
```

### Step 18: Mood Workflow Handles Message
**File**: `backend/chat_assistant/mood_workflow.py`

```python
class MoodWorkflow:
    @staticmethod
    def handle(user_id, message, history):
        # Step 18a: Extract mood from message
        mood_emoji = extract_mood("I'm feeling stressed")
        # Returns: "😟" (stressed emoji)
        
        # Step 18b: Check if we need to ask for reason
        if not has_reason_in_message(message):
            # Step 18c: Ask follow-up question
            return WorkflowResponse(
                message="I'm sorry you're feeling stressed. What's contributing to this feeling?",
                ui_elements=['text_input'],
                next_state='awaiting_mood_reason',
                temp_data={'mood_emoji': '😟'}
            )
```

---

## 📤 Phase 7: Response Sent Back

### Step 19: Backend Returns Response
**Backend** → **Frontend**

```json
{
    "message": "I'm sorry you're feeling stressed. What's contributing to this feeling?",
    "ui_elements": ["text_input"],
    "suggestions": [],
    "state": "awaiting_mood_reason"
}
```

### Step 20: Frontend Displays Response
**File**: `frontend/chat.js`

```javascript
// What happens:
1. Receives response from backend
2. Creates bot message bubble
3. Displays message
4. Shows text input (already visible)
5. Waits for next user input
```

**What You See**:
```
┌─────────────────────────────────┐
│  You: I'm feeling stressed      │
│                                 │
│  Bot: I'm sorry you're feeling  │
│       stressed. What's          │
│       contributing to this      │
│       feeling?                  │
│                                 │
│  Type a message...        [Send]│
└─────────────────────────────────┘
```

---

## 🔄 Phase 8: Conversation Continues

### Step 21: You Reply with Reason
```
You type: "Work deadlines"
You click: Send
```

### Step 22: Same Process Repeats
```
Frontend → Backend → ChatService → WorkflowRegistry → MoodWorkflow
```

### Step 23: Mood Workflow Completes
**File**: `backend/chat_assistant/mood_workflow.py`

```python
# Step 23a: Save mood log to database
save_mood_log(
    user_id=18,
    mood_emoji='😟',
    reason='work deadlines',
    timestamp=now()
)

# Step 23b: Get personalized suggestions
suggestions = IntelligentSuggestions.get_suggestions(
    user_id=18,
    mood_emoji='😟',
    reason='work deadlines'
)
# Returns: ["breathing", "take_break", "short_walk"]

# Step 23c: Return response with suggestions
return WorkflowResponse(
    message="I understand work deadlines can be stressful. Here are some activities that might help:",
    suggestions=[
        {"id": "breathing", "title": "Breathing Exercise", "duration": "5 min"},
        {"id": "take_break", "title": "Take a Break", "duration": "5 min"},
        {"id": "short_walk", "title": "Short Walk", "duration": "15 min"}
    ],
    ui_elements=['suggestion_buttons'],
    completed=True
)
```

### Step 24: Frontend Shows Suggestions
**What You See**:
```
┌─────────────────────────────────┐
│  You: Work deadlines            │
│                                 │
│  Bot: I understand work         │
│       deadlines can be          │
│       stressful. Here are some  │
│       activities that might     │
│       help:                     │
│                                 │
│  [🧘 Breathing Exercise - 5min] │
│  [☕ Take a Break - 5min]       │
│  [🚶 Short Walk - 15min]        │
└─────────────────────────────────┘
```

---

## 📊 Behind the Scenes (Continuous)

### Database Updates
**File**: `backend/mood_capture.db`

```sql
-- chat_messages table
INSERT INTO chat_messages (user_id, message, sender, timestamp)
VALUES (18, 'I''m feeling stressed', 'user', '2026-02-27 10:15:00');

INSERT INTO chat_messages (user_id, message, sender, timestamp)
VALUES (18, 'I''m sorry you''re feeling stressed...', 'bot', '2026-02-27 10:15:01');

-- mood_logs table
INSERT INTO mood_logs (user_id, mood_emoji, reason, timestamp)
VALUES (18, '😟', 'work deadlines', '2026-02-27 10:15:30');

-- suggestion_history table
INSERT INTO suggestion_history (user_id, suggestion_key, mood_emoji, shown_at)
VALUES (18, 'breathing', '😟', '2026-02-27 10:15:30');
```

### LLM Tracking (If LLM Was Called)
**File**: `backend/mood_capture.db`

```sql
-- llm_usage_log table (only if LLM was used)
INSERT INTO llm_usage_log (
    user_id, call_type, model, input_tokens, output_tokens,
    total_tokens, estimated_cost, latency_ms, timestamp
)
VALUES (
    18, 'intent_detection', 'gpt-4o-mini', 150, 10,
    160, 0.0001, 850, '2026-02-27 10:15:01'
);
```

---

## 🔄 Complete Flow Diagram

```
┌─────────────┐
│ 1. START    │ python main.py
│   SERVER    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 2. FASTAPI  │ Initialize routes, DB, LLM
│   INIT      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 3. OPEN     │ http://localhost:5500/frontend/
│   BROWSER   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 4. LANDING  │ Shows Login/Register
│   PAGE      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 5. LOGIN    │ POST /api/v1/auth/login
│   REQUEST   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 6. AUTH     │ Verify password, create JWT
│   BACKEND   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 7. STORE    │ localStorage.setItem('token', ...)
│   TOKEN     │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 8. CHAT     │ Load chat.html
│   PAGE      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ 9. INIT     │ POST /api/v1/chat/init
│   CHAT      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│10. GREETING │ "Hi ankur! How are you feeling?"
│   RESPONSE  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│11. USER     │ "I'm feeling stressed"
│   MESSAGE   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│12. PROCESS  │ ChatService → WorkflowRegistry
│   MESSAGE   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│13. DETECT   │ Rule-based or LLM
│   INTENT    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│14. ROUTE TO │ MoodWorkflow.handle()
│   WORKFLOW  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│15. GENERATE │ Ask follow-up or provide suggestions
│   RESPONSE  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│16. SAVE TO  │ chat_messages, mood_logs, etc.
│   DATABASE  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│17. RETURN   │ JSON response to frontend
│   RESPONSE  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│18. DISPLAY  │ Show message and UI elements
│   IN CHAT   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│19. WAIT FOR │ User types next message...
│   NEXT MSG  │
└─────────────┘
```

---

## 📁 Key Files in Order of Execution

1. **`backend/app/main.py`** - Server startup
2. **`frontend/index.html`** - Landing page
3. **`frontend/login.js`** - Login logic
4. **`backend/app/api/v1/endpoints/auth.py`** - Authentication
5. **`frontend/chat.html`** - Chat interface
6. **`frontend/chat.js`** - Chat logic
7. **`backend/app/api/v1/endpoints/chat.py`** - Chat API
8. **`backend/app/services/chat_service.py`** - Message processing
9. **`backend/chat_assistant/workflow_registry.py`** - Intent routing
10. **`backend/chat_assistant/mood_workflow.py`** - Mood handling
11. **`backend/chat_assistant/intelligent_suggestions.py`** - Suggestions
12. **`backend/mood_capture.db`** - Data storage

---

## 🎯 Summary

**Total Steps**: 24 steps from server start to first complete interaction
**API Calls**: 3 (login, init, message)
**Database Writes**: 4-5 (user login, chat messages, mood log, suggestions)
**LLM Calls**: 0-1 (only if needed for intent detection)
**Time**: ~2-3 seconds total

The system is designed to be fast, efficient, and context-aware, providing a seamless chat experience!
