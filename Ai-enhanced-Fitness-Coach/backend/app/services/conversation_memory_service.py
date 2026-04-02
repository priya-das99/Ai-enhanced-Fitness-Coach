"""
Conversation Memory Service - Long-term memory for conversations

Remembers:
- Important life events mentioned
- Previous emotional states
- Follow-up opportunities
- User preferences and communication style
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.chat import ChatMessage
from app.models.user import MoodLog


class ConversationMemoryService:
    """Manages long-term conversation memory"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def should_follow_up(self, user_id: int) -> Optional[Dict]:
        """Check if we should follow up on previous conversation"""
        # Get recent mood logs (last 7 days)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_moods = self.db.query(MoodLog).filter(
            and_(
                MoodLog.user_id == user_id,
                MoodLog.created_at >= one_week_ago
            )
        ).order_by(desc(MoodLog.created_at)).all()
        
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
        event_followup = self._check_event_followup(user_id)
        if event_followup:
            return event_followup
        
        return None
    
    def _check_mood_improvement(self, mood_logs: List) -> Optional[Dict]:
        """Check if mood has improved and celebrate"""
        if len(mood_logs) < 2:
            return None
        
        # Compare recent mood to earlier mood
        recent = mood_logs[0]
        earlier = mood_logs[-1]
        
        # Check if improved from negative to positive
        negative_moods = ['😟', '😢', '😠', '😰', '😞']
        positive_moods = ['😊', '😄', '🎉', '😌']
        
        if earlier.mood_emoji in negative_moods and recent.mood_emoji in positive_moods:
            days_ago = (datetime.utcnow() - earlier.created_at).days
            
            return {
                'type': 'mood_improvement',
                'message': (
                    f"I noticed your mood has improved since {days_ago} days ago! 🎉\n\n"
                    f"You were feeling {earlier.mood_emoji} and now you're {recent.mood_emoji}. "
                    f"That's wonderful progress!\n\n"
                    f"What helped you feel better?"
                ),
                'context': {
                    'previous_mood': earlier.mood_emoji,
                    'current_mood': recent.mood_emoji,
                    'days_between': days_ago
                }
            }
        
        return None
    
    def _check_persistent_negative_mood(self, mood_logs: List) -> Optional[Dict]:
        """Check if user has been consistently negative"""
        if len(mood_logs) < 3:
            return None
        
        negative_moods = ['😟', '😢', '😠', '😰', '😞']
        
        # Check last 3 moods
        recent_three = mood_logs[:3]
        negative_count = sum(1 for m in recent_three if m.mood_emoji in negative_moods)
        
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
    
    def _check_event_followup(self, user_id: int) -> Optional[Dict]:
        """Check for events mentioned in past conversations to follow up on"""
        # Get messages from 3-7 days ago (not too recent, not too old)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.user_id == user_id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= seven_days_ago,
                ChatMessage.created_at <= three_days_ago
            )
        ).order_by(desc(ChatMessage.created_at)).limit(20).all()
        
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
        
        for message in messages:
            content_lower = message.content.lower()
            for keyword, event_name in event_keywords.items():
                if keyword in content_lower:
                    days_ago = (datetime.utcnow() - message.created_at).days
                    
                    return {
                        'type': 'event_followup',
                        'message': (
                            f"Hey! I remember you mentioned a {event_name} about {days_ago} days ago. 📅\n\n"
                            f"How did it go?"
                        ),
                        'context': {
                            'event': event_name,
                            'days_ago': days_ago,
                            'original_message': message.content[:100]
                        }
                    }
        
        return None
    
    def _get_most_common_reason(self, mood_logs: List) -> Optional[str]:
        """Get most common reason from mood logs"""
        reasons = [m.reason for m in mood_logs if m.reason]
        if not reasons:
            return None
        
        return max(set(reasons), key=reasons.count)
    
    def get_conversation_context(self, user_id: int) -> Dict:
        """Get context about user's recent conversations"""
        # Get last 5 messages
        recent_messages = self.db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(desc(ChatMessage.created_at)).limit(5).all()
        
        # Get last mood log
        last_mood = self.db.query(MoodLog).filter(
            MoodLog.user_id == user_id
        ).order_by(desc(MoodLog.created_at)).first()
        
        return {
            'recent_messages': [
                {
                    'role': m.role,
                    'content': m.content[:100],
                    'created_at': m.created_at
                }
                for m in recent_messages
            ],
            'last_mood': {
                'emoji': last_mood.mood_emoji,
                'reason': last_mood.reason,
                'created_at': last_mood.created_at
            } if last_mood else None
        }
    
    def store_important_event(self, user_id: int, event_type: str, event_data: Dict):
        """Store an important event for future follow-up"""
        # This could be expanded to use a dedicated events table
        # For now, we rely on chat messages and mood logs
        pass
    
    def get_communication_style(self, user_id: int) -> Dict:
        """Analyze user's communication style"""
        messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.user_id == user_id,
                ChatMessage.role == 'user'
            )
        ).order_by(desc(ChatMessage.created_at)).limit(20).all()
        
        if not messages:
            return {'style': 'unknown', 'avg_length': 0}
        
        # Calculate average message length
        avg_length = sum(len(m.content) for m in messages) / len(messages)
        
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
