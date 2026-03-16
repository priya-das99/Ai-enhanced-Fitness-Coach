"""
Conversation Memory Service - SQLite3 Compatible
Long-term memory for conversations

Remembers:
- Important life events mentioned
- Previous emotional states
- Follow-up opportunities
- User preferences and communication style
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class ConversationMemoryServiceSQLite:
    """Manages long-term conversation memory (SQLite3 compatible)"""
    
    def __init__(self):
        pass
    
    def should_follow_up(self, user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
        """Check if we should follow up on previous conversation"""
        try:
            cursor = db.cursor()
            
            # Get recent mood logs (last 7 days)
            one_week_ago = datetime.now() - timedelta(days=7)
            
            cursor.execute("""
                SELECT mood_emoji, reason, mood_intensity, timestamp
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (user_id, one_week_ago.isoformat()))
            
            recent_moods = cursor.fetchall()
            
            if not recent_moods:
                return None
            
            # Check for improvement opportunity
            improvement = self._check_mood_improvement(recent_moods)
            if improvement:
                return improvement
            
            # Check for persistent negative mood
            persistent = self._check_persistent_negative_mood(recent_moods)
            if persistent:
                return persistent
            
            # Check for mentioned events
            event_followup = self._check_event_followup(user_id, db)
            if event_followup:
                return event_followup
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to check follow-up for user {user_id}: {e}", exc_info=True)
            return None
    
    def _check_mood_improvement(self, mood_logs: List) -> Optional[Dict]:
        """Check if mood has improved and celebrate"""
        if len(mood_logs) < 2:
            return None
        
        # Compare recent mood to earlier mood
        recent = mood_logs[0]
        earlier = mood_logs[-1]
        
        recent_emoji, recent_reason, recent_intensity, recent_timestamp = recent
        earlier_emoji, earlier_reason, earlier_intensity, earlier_timestamp = earlier
        
        # Check if improved from negative to positive
        negative_moods = ['😟', '😢', '😠', '😰', '😞', '😭', '😤', '😔']
        positive_moods = ['😊', '😄', '🎉', '😌', '🥰', '😁']
        
        if earlier_emoji in negative_moods and recent_emoji in positive_moods:
            earlier_dt = datetime.fromisoformat(earlier_timestamp)
            days_ago = (datetime.now() - earlier_dt).days
            
            return {
                'type': 'mood_improvement',
                'message': (
                    f"I noticed your mood has improved since {days_ago} days ago! 🎉\n\n"
                    f"You were feeling {earlier_emoji} and now you're {recent_emoji}. "
                    f"That's wonderful progress!\n\n"
                    f"What helped you feel better?"
                ),
                'context': {
                    'previous_mood': earlier_emoji,
                    'current_mood': recent_emoji,
                    'days_between': days_ago
                }
            }
        
        return None
    
    def _check_persistent_negative_mood(self, mood_logs: List) -> Optional[Dict]:
        """Check if user has been consistently negative"""
        if len(mood_logs) < 3:
            return None
        
        negative_moods = ['😟', '😢', '😠', '😰', '😞', '😭', '😤', '😔']
        
        # Check last 3 moods
        recent_three = mood_logs[:3]
        negative_count = sum(1 for m in recent_three if m[0] in negative_moods)
        
        if negative_count >= 3:
            # All 3 recent moods are negative
            most_common_reason = self._get_most_common_reason(recent_three)
            
            return {
                'type': 'persistent_negative',
                'message': (
                    f"I've noticed you've been feeling down lately. 💙\n\n"
                    f"You've logged negative moods {negative_count} times recently"
                    + (f", mostly about {most_common_reason}" if most_common_reason else "")
                    + ".\n\n"
                    f"I'm here to help. Would you like to talk about what's going on, "
                    f"or try some activities that might help?"
                ),
                'context': {
                    'negative_count': negative_count,
                    'reason': most_common_reason
                }
            }
        
        return None
    
    def _check_event_followup(self, user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
        """Check for events mentioned in past conversations to follow up on"""
        try:
            cursor = db.cursor()
            
            # Get messages from 3-7 days ago (not too recent, not too old)
            seven_days_ago = datetime.now() - timedelta(days=7)
            three_days_ago = datetime.now() - timedelta(days=3)
            
            cursor.execute("""
                SELECT message, timestamp
                FROM chat_messages
                WHERE user_id = ?
                AND sender = 'user'
                AND timestamp >= ?
                AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 20
            """, (user_id, seven_days_ago.isoformat(), three_days_ago.isoformat()))
            
            messages = cursor.fetchall()
            
            # Look for event keywords
            event_keywords = {
                'deadline': 'work deadline',
                'exam': 'exam',
                'interview': 'interview',
                'presentation': 'presentation',
                'meeting': 'important meeting',
                'appointment': 'appointment',
                'event': 'event'
            }
            
            for message_row in messages:
                message_content, message_timestamp = message_row
                content_lower = message_content.lower()
                
                for keyword, event_name in event_keywords.items():
                    if keyword in content_lower:
                        message_dt = datetime.fromisoformat(message_timestamp)
                        days_ago = (datetime.now() - message_dt).days
                        
                        return {
                            'type': 'event_followup',
                            'message': (
                                f"Hey! I remember you mentioned a {event_name} about {days_ago} days ago. 📅\n\n"
                                f"How did it go?"
                            ),
                            'context': {
                                'event': event_name,
                                'days_ago': days_ago,
                                'original_message': message_content[:100]
                            }
                        }
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to check event follow-up: {e}")
            return None
    
    def _get_most_common_reason(self, mood_logs: List) -> Optional[str]:
        """Get most common reason from mood logs"""
        reasons = [m[1] for m in mood_logs if m[1]]  # m[1] is reason
        if not reasons:
            return None
        
        return max(set(reasons), key=reasons.count)
    
    def get_conversation_context(self, user_id: int, db: sqlite3.Connection) -> Dict:
        """Get context about user's recent conversations"""
        try:
            cursor = db.cursor()
            
            # Get last 5 messages
            cursor.execute("""
                SELECT sender, message, timestamp
                FROM chat_messages
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            """, (user_id,))
            
            recent_messages = cursor.fetchall()
            
            # Get last mood log
            cursor.execute("""
                SELECT mood_emoji, reason, timestamp
                FROM mood_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            
            last_mood = cursor.fetchone()
            
            return {
                'recent_messages': [
                    {
                        'role': m[0],
                        'content': m[1][:100],
                        'created_at': m[2]
                    }
                    for m in recent_messages
                ],
                'last_mood': {
                    'emoji': last_mood[0],
                    'reason': last_mood[1],
                    'created_at': last_mood[2]
                } if last_mood else None
            }
        
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {'recent_messages': [], 'last_mood': None}
    
    def get_communication_style(self, user_id: int, db: sqlite3.Connection) -> Dict:
        """Analyze user's communication style"""
        try:
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT message
                FROM chat_messages
                WHERE user_id = ?
                AND sender = 'user'
                ORDER BY timestamp DESC
                LIMIT 20
            """, (user_id,))
            
            messages = cursor.fetchall()
            
            if not messages:
                return {'style': 'unknown', 'avg_length': 0}
            
            # Calculate average message length
            avg_length = sum(len(m[0]) for m in messages) / len(messages)
            
            # Determine style
            if avg_length < 20:
                style = 'brief'
            elif avg_length < 50:
                style = 'moderate'
            else:
                style = 'detailed'
            
            return {
                'style': style,
                'avg_length': int(avg_length),
                'message_count': len(messages)
            }
        
        except Exception as e:
            logger.error(f"Failed to get communication style: {e}")
            return {'style': 'unknown', 'avg_length': 0}
