# app/services/event_publisher.py
# Event publisher for analytics and personalization

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import get_db

logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Publishes events to analytics_events table for event-driven architecture.
    
    Events are used for:
    - Analytics and monitoring
    - Behavior metrics calculation
    - Personalization feedback loop
    """
    
    # Event type constants
    EVENT_MOOD_LOGGED = "mood_logged"
    EVENT_ACTIVITY_LOGGED = "activity_logged"
    EVENT_SUGGESTION_SHOWN = "suggestion_shown"
    EVENT_SUGGESTION_ACCEPTED = "suggestion_accepted"
    EVENT_WORKFLOW_STARTED = "workflow_started"
    EVENT_WORKFLOW_COMPLETED = "workflow_completed"
    
    def publish(self, user_id: str, event_type: str, event_data: Dict[str, Any] = None) -> Optional[int]:
        """
        Publish an event to analytics_events table.
        
        Args:
            user_id: User identifier
            event_type: Type of event (use EVENT_* constants)
            event_data: Additional event data (will be JSON serialized)
            
        Returns:
            Event ID if successful, None otherwise
        """
        try:
            # Serialize event data to JSON
            event_data_json = json.dumps(event_data) if event_data else None
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analytics_events (user_id, event_type, event_data, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, event_type, event_data_json, datetime.now().isoformat()))
                
                event_id = cursor.lastrowid
                
            logger.info(f"📊 Event published: {event_type} for user {user_id} (id={event_id})")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} for user {user_id}: {e}")
            return None
    
    def publish_mood_logged(self, user_id: str, mood_emoji: str, reason: Optional[str] = None, mood_value: Optional[int] = None):
        """Publish mood_logged event"""
        return self.publish(user_id, self.EVENT_MOOD_LOGGED, {
            'mood_emoji': mood_emoji,
            'reason': reason,
            'mood_value': mood_value
        })
    
    def publish_activity_logged(self, user_id: str, activity_type: str, value: float, unit: str):
        """Publish activity_logged event"""
        return self.publish(user_id, self.EVENT_ACTIVITY_LOGGED, {
            'activity_type': activity_type,
            'value': value,
            'unit': unit
        })
    
    def publish_suggestion_shown(self, user_id: str, suggestion_key: str, mood_emoji: Optional[str] = None, reason: Optional[str] = None):
        """Publish suggestion_shown event and record in suggestion_history"""
        # Publish event
        event_id = self.publish(user_id, self.EVENT_SUGGESTION_SHOWN, {
            'suggestion_key': suggestion_key,
            'mood_emoji': mood_emoji,
            'reason': reason
        })
        
        # Also record in suggestion_history
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO suggestion_history (user_id, suggestion_key, mood_emoji, reason, shown_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, suggestion_key, mood_emoji, reason, datetime.now().isoformat()))
                
        except Exception as e:
            logger.error(f"Failed to record suggestion_history: {e}")
        
        return event_id
    
    def publish_suggestion_accepted(self, user_id: str, suggestion_key: str):
        """Publish suggestion_accepted event and update suggestion_history"""
        # Publish event
        event_id = self.publish(user_id, self.EVENT_SUGGESTION_ACCEPTED, {
            'suggestion_key': suggestion_key
        })
        
        # Update suggestion_history
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE suggestion_history
                    SET accepted = 1, accepted_at = ?
                    WHERE user_id = ? AND suggestion_key = ?
                    AND id = (
                        SELECT id FROM suggestion_history
                        WHERE user_id = ? AND suggestion_key = ?
                        ORDER BY shown_at DESC
                        LIMIT 1
                    )
                """, (datetime.now().isoformat(), user_id, suggestion_key, user_id, suggestion_key))
                
        except Exception as e:
            logger.error(f"Failed to update suggestion_history: {e}")
        
        return event_id
    
    def publish_suggestion_ignored(self, user_id: str, suggestion_key: str):
        """
        Publish suggestion_ignored event (Phase 3)
        
        Used for fatigue tracking - when user sees but doesn't accept suggestion
        """
        return self.publish(user_id, "suggestion_ignored", {
            'suggestion_key': suggestion_key
        })
    
    def publish_workflow_started(self, user_id: str, workflow_name: str):
        """Publish workflow_started event"""
        return self.publish(user_id, self.EVENT_WORKFLOW_STARTED, {
            'workflow_name': workflow_name
        })
    
    def publish_workflow_completed(self, user_id: str, workflow_name: str, success: bool = True):
        """Publish workflow_completed event"""
        return self.publish(user_id, self.EVENT_WORKFLOW_COMPLETED, {
            'workflow_name': workflow_name,
            'success': success
        })


# Global instance
_event_publisher = None

def get_event_publisher() -> EventPublisher:
    """Get or create global EventPublisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher
