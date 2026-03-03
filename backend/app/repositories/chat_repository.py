# app/repositories/chat_repository.py
# Chat/conversation data access layer

from app.core.database import get_db
from typing import List, Dict
import json
from datetime import datetime, timedelta

class ChatRepository:
    """Repository for chat/mood log database operations"""
    
    def get_user_mood_logs(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get mood logs for a user"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM mood_logs 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def save_mood_log(self, user_id: int, mood: str, user_input: str, 
                      bot_response: str, suggestions: str = None) -> int:
        """Save a mood log entry"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO mood_logs 
                   (user_id, mood, user_input, bot_response, suggestions) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, mood, user_input, bot_response, suggestions)
            )
            return cursor.lastrowid
    
    # Chat History Methods
    
    def save_message(self, user_id: int, message: str, sender: str, metadata: Dict = None) -> int:
        """
        Save a chat message to database
        
        Args:
            user_id: User ID
            message: Message text
            sender: 'user' or 'bot'
            metadata: Optional metadata (ui_elements, etc.)
        
        Returns:
            Message ID
        """
        with get_db() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute('''
                INSERT INTO chat_messages (user_id, message, sender, metadata)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message, sender, metadata_json))
            
            return cursor.lastrowid
    
    def get_recent_messages(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Get recent chat messages for a user
        
        Args:
            user_id: User ID
            limit: Number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, message, sender, timestamp, metadata
                FROM chat_messages
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            
            # Reverse to get chronological order
            messages = []
            for row in reversed(rows):
                metadata = json.loads(row[4]) if row[4] else {}
                messages.append({
                    'id': row[0],
                    'message': row[1],
                    'sender': row[2],
                    'timestamp': row[3],
                    'metadata': metadata
                })
            
            return messages
    
    def get_conversation_context(self, user_id: int, max_messages: int = 10) -> str:
        """
        Get recent conversation as formatted context for LLM
        
        Args:
            user_id: User ID
            max_messages: Maximum messages to include
        
        Returns:
            Formatted conversation string
        """
        messages = self.get_recent_messages(user_id, max_messages)
        
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            sender_label = "User" if msg['sender'] == 'user' else "Assistant"
            context_lines.append(f"{sender_label}: {msg['message']}")
        
        return "\n".join(context_lines)
    
    # Session Management Methods
    
    def create_session(self, user_id: int) -> int:
        """
        Create new chat session
        
        Args:
            user_id: User ID
        
        Returns:
            Session ID
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_sessions (user_id, session_start)
                VALUES (?, CURRENT_TIMESTAMP)
            """, (user_id,))
            return cursor.lastrowid
    
    def save_message_with_session(self, user_id: int, session_id: int, 
                                   message: str, sender: str, metadata: Dict = None) -> int:
        """
        Save message linked to session
        
        Args:
            user_id: User ID
            session_id: Session ID
            message: Message text
            sender: 'user' or 'bot'
            metadata: Optional metadata
        
        Returns:
            Message ID
        """
        with get_db() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO chat_messages 
                (user_id, session_id, message, sender, timestamp, metadata)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (user_id, session_id, message, sender, metadata_json))
            
            return cursor.lastrowid
