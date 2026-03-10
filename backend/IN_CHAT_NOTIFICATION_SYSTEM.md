# In-Chat Notification System
## How Notifications Appear During Active Chat Sessions

## The Challenge

**Scenario**: User is actively chatting with the bot at 2 PM when the water reminder is scheduled to trigger.

**Question**: How does the notification appear in the chat without interrupting the conversation?

## Solution Overview

There are **3 delivery mechanisms** depending on the situation:

### 1. **User is NOT in chat** → Push Notification
### 2. **User is in chat but IDLE** → In-Chat System Message
### 3. **User is in chat and ACTIVE** → Queued for next response

---

## Detailed Implementation

### Architecture: WebSocket + Polling Hybrid

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vue)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Chat Component                                         │ │
│  │  - Displays messages                                    │ │
│  │  - Listens for new messages (WebSocket/Polling)        │ │
│  │  - Shows system notifications                           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ WebSocket / Long Polling
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  WebSocket Manager                                      │ │
│  │  - Tracks active connections                           │ │
│  │  - Sends real-time messages                            │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Notification Service                                   │ │
│  │  - Checks user status (online/offline)                 │ │
│  │  - Routes to appropriate channel                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Chat Repository                                        │ │
│  │  - Stores all messages (user + bot + system)           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. WebSocket Connection Manager

```python
# backend/app/websocket/connection_manager.py

from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat.
    Tracks which users are currently online and in chat.
    """
    
    def __init__(self):
        # user_id -> Set of WebSocket connections (multiple tabs/devices)
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # Track last activity time for each user
        self.last_activity: Dict[int, datetime] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.last_activity[user_id] = datetime.now()
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Remove user if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.last_activity[user_id]
        
        logger.info(f"User {user_id} disconnected")
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def is_user_active(self, user_id: int, threshold_seconds: int = 60) -> bool:
        """
        Check if user is actively chatting (sent message recently).
        Active = sent message in last 60 seconds
        """
        if user_id not in self.last_activity:
            return False
        
        time_since_activity = (datetime.now() - self.last_activity[user_id]).seconds
        return time_since_activity < threshold_seconds
    
    def update_activity(self, user_id: int):
        """Update last activity timestamp when user sends message"""
        self.last_activity[user_id] = datetime.now()
    
    async def send_personal_message(self, message: dict, user_id: int):
        """
        Send message to specific user (all their connections).
        Used for: System notifications, reminders
        """
        if user_id in self.active_connections:
            # Send to all user's connections (multiple tabs/devices)
            disconnected = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


# Global instance
connection_manager = ConnectionManager()
```

### 2. WebSocket Endpoint

```python
# backend/app/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.connection_manager import connection_manager
from app.auth import get_current_user_ws  # WebSocket auth
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time chat.
    Handles bidirectional communication.
    """
    # Authenticate user (verify token)
    # user = await get_current_user_ws(websocket)
    
    await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Update activity timestamp
            connection_manager.update_activity(user_id)
            
            # Handle different message types
            if data['type'] == 'chat_message':
                # Process chat message
                from app.services.chat_service import process_chat_message
                response = await process_chat_message(user_id, data['message'])
                
                # Send response back
                await connection_manager.send_personal_message(
                    {
                        'type': 'chat_response',
                        'message': response['message'],
                        'ui_elements': response.get('ui_elements', []),
                        'timestamp': datetime.now().isoformat()
                    },
                    user_id
                )
            
            elif data['type'] == 'typing':
                # User is typing (update activity)
                connection_manager.update_activity(user_id)
            
            elif data['type'] == 'ping':
                # Heartbeat to keep connection alive
                await websocket.send_json({'type': 'pong'})
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(websocket, user_id)
```

### 3. Enhanced Notification Service

```python
# backend/app/services/notification_service.py

from app.websocket.connection_manager import connection_manager
from app.repositories.chat_repository import ChatRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Smart notification delivery based on user status.
    Routes to appropriate channel (WebSocket, Push, or Queue).
    """
    
    def __init__(self):
        self.chat_repo = ChatRepository()
    
    async def send_notification(self, user_id: int, notification: dict):
        """
        Smart notification routing based on user status.
        
        Args:
            user_id: Target user
            notification: {
                'title': str,
                'message': str,
                'type': 'reminder' | 'celebration' | 'insight',
                'action_buttons': List[dict],
                'priority': 'high' | 'normal' | 'low'
            }
        """
        # Check user status
        is_online = connection_manager.is_user_online(user_id)
        is_active = connection_manager.is_user_active(user_id)
        
        logger.info(f"Sending notification to user {user_id}: online={is_online}, active={is_active}")
        
        # CASE 1: User is online and in chat
        if is_online:
            if is_active:
                # User is actively chatting - queue for next response
                await self._queue_for_next_response(user_id, notification)
            else:
                # User is in chat but idle - send as system message
                await self._send_in_chat_notification(user_id, notification)
        
        # CASE 2: User is offline - send push notification
        else:
            await self._send_push_notification(user_id, notification)
        
        # Always store in database for history
        self._store_notification(user_id, notification)
    
    async def _send_in_chat_notification(self, user_id: int, notification: dict):
        """
        Send notification as system message in chat.
        Appears as a special message bubble.
        """
        # Save to chat history as system message
        message_id = self.chat_repo.save_message(
            user_id=user_id,
            sender='system',
            message=notification['message'],
            message_type=notification['type'],
            metadata={
                'title': notification.get('title'),
                'action_buttons': notification.get('action_buttons', [])
            }
        )
        
        # Send via WebSocket for real-time display
        await connection_manager.send_personal_message(
            {
                'type': 'system_notification',
                'id': message_id,
                'title': notification.get('title', ''),
                'message': notification['message'],
                'notification_type': notification['type'],
                'action_buttons': notification.get('action_buttons', []),
                'timestamp': datetime.now().isoformat(),
                'priority': notification.get('priority', 'normal')
            },
            user_id
        )
        
        logger.info(f"Sent in-chat notification to user {user_id}")
    
    async def _queue_for_next_response(self, user_id: int, notification: dict):
        """
        Queue notification to be included in next bot response.
        Used when user is actively chatting to avoid interruption.
        """
        # Store in pending notifications table
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO pending_notifications 
                (user_id, notification_data, created_at)
                VALUES (?, ?, ?)
            ''', (user_id, json.dumps(notification), datetime.now()))
        
        logger.info(f"Queued notification for user {user_id} (active chat)")
    
    async def _send_push_notification(self, user_id: int, notification: dict):
        """
        Send push notification to user's device.
        Used when user is not in chat.
        """
        # Integrate with push service (Firebase, OneSignal, etc.)
        # This is platform-specific
        
        logger.info(f"Sent push notification to user {user_id}")
    
    def _store_notification(self, user_id: int, notification: dict):
        """Store notification in database for history"""
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO notifications 
                (user_id, title, message, notification_type, action_buttons, created_at, read)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                notification.get('title', ''),
                notification['message'],
                notification['type'],
                json.dumps(notification.get('action_buttons', [])),
                datetime.now(),
                False
            ))
    
    def get_pending_notifications(self, user_id: int) -> List[dict]:
        """
        Get pending notifications for user.
        Called when generating next bot response.
        """
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                SELECT id, notification_data 
                FROM pending_notifications
                WHERE user_id = ?
                ORDER BY created_at ASC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            
            # Delete retrieved notifications
            if rows:
                cursor.execute('''
                    DELETE FROM pending_notifications
                    WHERE user_id = ?
                ''', (user_id,))
            
            return [json.loads(row['notification_data']) for row in rows]
```

### 4. Enhanced Chat Engine (Include Pending Notifications)

```python
# backend/chat_assistant/chat_engine_workflow.py

def process_message(self, user_id: str, message: str) -> dict:
    """
    Process user message and include pending notifications.
    """
    # ... existing message processing ...
    
    # Get pending notifications
    from app.services.notification_service import NotificationService
    notification_service = NotificationService()
    pending = notification_service.get_pending_notifications(user_id)
    
    # If there are pending notifications, prepend to response
    if pending:
        notification_text = self._format_pending_notifications(pending)
        result['message'] = f"{notification_text}\n\n{result['message']}"
        
        # Add action buttons from notifications
        for notif in pending:
            if notif.get('action_buttons'):
                result['ui_elements'].extend(notif['action_buttons'])
    
    return result

def _format_pending_notifications(self, notifications: List[dict]) -> str:
    """Format pending notifications as text"""
    if len(notifications) == 1:
        return f"💡 {notifications[0]['message']}"
    else:
        text = "💡 While you were chatting:\n"
        for notif in notifications:
            text += f"  • {notif['message']}\n"
        return text
```

---

## Frontend Implementation

### React Component Example

```typescript
// frontend/src/components/Chat.tsx

import { useEffect, useState } from 'react';
import useWebSocket from 'react-use-websocket';

interface Message {
  type: 'user' | 'bot' | 'system';
  message: string;
  timestamp: string;
  notification_type?: string;
  action_buttons?: Array<{id: string, label: string}>;
}

export function Chat({ userId }: { userId: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const socketUrl = `ws://localhost:8000/ws/chat/${userId}`;
  
  const { sendJsonMessage, lastJsonMessage } = useWebSocket(socketUrl, {
    onOpen: () => console.log('WebSocket connected'),
    onClose: () => console.log('WebSocket disconnected'),
    shouldReconnect: () => true,
  });
  
  // Handle incoming messages
  useEffect(() => {
    if (lastJsonMessage) {
      const data = lastJsonMessage as any;
      
      if (data.type === 'chat_response') {
        // Regular bot response
        setMessages(prev => [...prev, {
          type: 'bot',
          message: data.message,
          timestamp: data.timestamp
        }]);
      }
      
      else if (data.type === 'system_notification') {
        // System notification (reminder, celebration, etc.)
        setMessages(prev => [...prev, {
          type: 'system',
          message: data.message,
          timestamp: data.timestamp,
          notification_type: data.notification_type,
          action_buttons: data.action_buttons
        }]);
        
        // Show toast/banner for high priority
        if (data.priority === 'high') {
          showNotificationBanner(data);
        }
      }
    }
  }, [lastJsonMessage]);
  
  const sendMessage = (text: string) => {
    // Add to UI immediately
    setMessages(prev => [...prev, {
      type: 'user',
      message: text,
      timestamp: new Date().toISOString()
    }]);
    
    // Send via WebSocket
    sendJsonMessage({
      type: 'chat_message',
      message: text
    });
  };
  
  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
      </div>
      <ChatInput onSend={sendMessage} />
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.type === 'system') {
    // Special styling for system notifications
    return (
      <div className="system-notification">
        <div className="notification-icon">💡</div>
        <div className="notification-content">
          <p>{message.message}</p>
          {message.action_buttons && (
            <div className="action-buttons">
              {message.action_buttons.map(btn => (
                <button key={btn.id} onClick={() => handleAction(btn.id)}>
                  {btn.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Regular user/bot message
  return (
    <div className={`message ${message.type}`}>
      <p>{message.message}</p>
      <span className="timestamp">{formatTime(message.timestamp)}</span>
    </div>
  );
}
```

### CSS Styling

```css
/* System notification styling */
.system-notification {
  display: flex;
  gap: 12px;
  padding: 16px;
  margin: 12px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  animation: slideIn 0.3s ease-out;
}

.notification-icon {
  font-size: 24px;
}

.notification-content {
  flex: 1;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.action-buttons button {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.action-buttons button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## Visual Examples

### Scenario 1: User is Idle in Chat
```
┌─────────────────────────────────────────┐
│  Chat with MoodBot                      │
├─────────────────────────────────────────┤
│                                         │
│  You: I drank 1 glass of water         │
│                                         │
│  Bot: Great! Logged 1 glass 💧         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 💡 Hydration Reminder             │ │ ← System notification
│  │                                   │ │
│  │ You've only had 1/8 glasses      │ │
│  │ today. Don't forget to drink     │ │
│  │ water! 💧                        │ │
│  │                                   │ │
│  │ [Log Water]                      │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Scenario 2: User is Actively Chatting
```
User at 2:00 PM: "I'm feeling stressed"
Bot: "I understand. Would you like to try..."

[Notification scheduled at 2:00 PM but user is active]
[Notification queued]

User at 2:01 PM: "Yes, show me activities"
Bot: "💡 Quick reminder: You've only had 1/8 glasses 
      of water today!
      
      Here are some activities for stress..."
```

---

## Database Schema

### New Tables

```sql
-- Store all notifications
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- 'reminder', 'celebration', 'insight'
    action_buttons TEXT, -- JSON
    priority TEXT DEFAULT 'normal', -- 'high', 'normal', 'low'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    read_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Queue for notifications during active chat
CREATE TABLE pending_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_data TEXT NOT NULL, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Track user online status
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    disconnected_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Summary

### How Notifications Appear in Chat:

1. **User Offline** → Push notification to device
2. **User in Chat (Idle)** → System message bubble via WebSocket
3. **User in Chat (Active)** → Queued and prepended to next response

### Key Features:
- ✅ Real-time delivery via WebSocket
- ✅ Non-intrusive (respects user activity)
- ✅ Persistent (stored in database)
- ✅ Actionable (includes buttons)
- ✅ Styled differently (visual distinction)
- ✅ Fallback to push notifications

### Benefits:
- No interruption during active conversation
- Seamless integration with chat flow
- User can act on notifications immediately
- All notifications are preserved in history
