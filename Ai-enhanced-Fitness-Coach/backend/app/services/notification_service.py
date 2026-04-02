# app/services/notification_service.py
# Service for sending notifications (in-app messages for now)

from typing import Dict, List
from datetime import datetime
from app.core.database import get_db
import json
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Handles notification delivery.
    For now: Stores in database as system messages in chat.
    Future: WebSocket, Push notifications
    """
    
    def send_notification(self, user_id: int, notification: Dict):
        """
        Send notification to user.
        
        Args:
            notification: {
                'title': str,
                'message': str,
                'type': 'reminder' | 'celebration' | 'insight',
                'action_buttons': List[dict],  # Optional
                'priority': 'high' | 'normal' | 'low'  # Optional
            }
        """
        try:
            # Store in database
            self._store_notification(user_id, notification)
            
            # Store as chat message (so it appears in chat history)
            self._store_as_chat_message(user_id, notification)
            
            logger.info(f"Notification sent to user {user_id}: {notification['type']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
    
    def _store_notification(self, user_id: int, notification: Dict):
        """Store notification in notifications table"""
        with get_db() as db:
            cursor = db.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    message TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    action_buttons TEXT,
                    priority TEXT DEFAULT 'normal',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read BOOLEAN DEFAULT 0,
                    read_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO notifications 
                (user_id, title, message, notification_type, action_buttons, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                notification.get('title', ''),
                notification['message'],
                notification['type'],
                json.dumps(notification.get('action_buttons', [])),
                notification.get('priority', 'normal')
            ))
    
    def _store_as_chat_message(self, user_id: int, notification: Dict):
        """Store notification as system message in chat"""
        with get_db() as db:
            cursor = db.cursor()
            
            # Format message with title if present
            full_message = notification['message']
            if notification.get('title'):
                full_message = f"💡 {notification['title']}\n\n{notification['message']}"
            
            # Store action_buttons in metadata so frontend can use them directly
            metadata = json.dumps({
                'action_buttons': notification.get('action_buttons', []),
                'notification_type': notification.get('type', 'reminder'),
                'title': notification.get('title', '')
            })
            
            cursor.execute('''
                INSERT INTO chat_messages 
                (user_id, sender, message, timestamp, metadata)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (
                user_id,
                'system',
                full_message,
                metadata
            ))
    
    def get_unread_notifications(self, user_id: int) -> List[Dict]:
        """Get unread notifications for user"""
        with get_db() as db:
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT id, title, message, notification_type, action_buttons, created_at
                FROM notifications
                WHERE user_id = ? AND read = 0
                ORDER BY created_at DESC
            ''', (user_id,))
            
            return [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'message': row['message'],
                    'type': row['notification_type'],
                    'action_buttons': json.loads(row['action_buttons']) if row['action_buttons'] else [],
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]
    
    def mark_as_read(self, notification_id: int):
        """Mark notification as read"""
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                UPDATE notifications
                SET read = 1, read_at = ?
                WHERE id = ?
            ''', (datetime.now(), notification_id))


# Global instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get or create global NotificationService instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
