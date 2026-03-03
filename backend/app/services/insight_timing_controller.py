# app/services/insight_timing_controller.py
"""
Insight Timing Controller
Determines WHEN to show insights based on conversation context and triggers.

Core Principle: Insights must follow emotional openings, never interrupt.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class InsightTrigger(Enum):
    """Valid triggers for showing insights"""
    AFTER_MOOD_LOG = "after_mood_log"
    AFTER_ACTIVITY_LOG = "after_activity_log"
    AFTER_EXTERNAL_ACTIVITY = "after_external_activity"
    USER_ASKS_PROGRESS = "user_asks_progress"
    CONVERSATION_PAUSE = "conversation_pause"
    ENGAGEMENT_DROP = "engagement_drop"
    NONE = "none"


class InsightTimingController:
    """
    Controls WHEN insights should be shown.
    
    Rules:
    1. Max 1 insight per session
    2. Max 1 insight per 24 hours
    3. Max 1 insight per 3 mood logs
    4. Only show at valid trigger points
    5. Never interrupt emotional expression
    """
    
    def __init__(self):
        # In-memory tracking (per user)
        self._last_insight_shown = {}  # user_id -> timestamp
        self._insights_this_session = {}  # user_id -> count
        self._mood_logs_since_insight = {}  # user_id -> count
    
    def should_show_insight(
        self,
        user_id: int,
        trigger: InsightTrigger,
        conversation_context: Dict,
        insight_priority: int = 3
    ) -> bool:
        """
        Determine if insight should be shown based on timing rules.
        
        Args:
            user_id: User ID
            trigger: What triggered the insight check
            conversation_context: Current conversation state
            insight_priority: Priority of the insight (1=highest, 5=lowest)
            
        Returns:
            True if insight should be shown, False otherwise
        """
        logger.info(f"Checking insight timing for user {user_id}, trigger: {trigger.value}")
        
        # Rule 0: Never show during invalid triggers
        if trigger == InsightTrigger.NONE:
            logger.info("❌ No valid trigger")
            return False
        
        # Rule 1: Check if user is in emotional state (venting)
        if self._is_venting(conversation_context):
            logger.info("❌ User is venting - no insight")
            return False
        
        # Rule 2: Check if in clarification flow
        if self._is_clarifying(conversation_context):
            logger.info("❌ User is clarifying - no insight")
            return False
        
        # Rule 3: Check session limit (max 1 per session)
        if self._exceeded_session_limit(user_id):
            logger.info("❌ Session limit exceeded")
            return False
        
        # Rule 4: Check 24-hour limit
        if self._shown_recently(user_id):
            logger.info("❌ Shown within 24 hours")
            return False
        
        # Rule 5: Check mood log frequency (max 1 per 3 mood logs)
        if not self._enough_mood_logs_passed(user_id):
            logger.info("❌ Not enough mood logs since last insight")
            return False
        
        # Rule 6: High-priority insights can override some rules
        if insight_priority == 1:
            # Critical insights (stress-inactivity cycle) can show more frequently
            if self._shown_recently(user_id, hours=12):  # Still respect 12h minimum
                logger.info("❌ High-priority insight shown within 12 hours")
                return False
        
        # Rule 7: Check trigger-specific rules
        if not self._validate_trigger_context(trigger, conversation_context):
            logger.info(f"❌ Trigger {trigger.value} context not valid")
            return False
        
        logger.info(f"✅ Insight timing approved for trigger: {trigger.value}")
        return True
    
    def mark_insight_shown(self, user_id: int):
        """Mark that an insight was shown"""
        self._last_insight_shown[user_id] = datetime.now()
        self._insights_this_session[user_id] = self._insights_this_session.get(user_id, 0) + 1
        self._mood_logs_since_insight[user_id] = 0
        logger.info(f"Marked insight shown for user {user_id}")
    
    def mark_mood_logged(self, user_id: int):
        """Track mood log for frequency limiting"""
        self._mood_logs_since_insight[user_id] = self._mood_logs_since_insight.get(user_id, 0) + 1
    
    def reset_session(self, user_id: int):
        """Reset session counters (call on logout or new session)"""
        if user_id in self._insights_this_session:
            del self._insights_this_session[user_id]
        logger.info(f"Reset session for user {user_id}")
    
    def detect_trigger(
        self,
        workflow_name: str,
        workflow_step: str,
        message: str,
        just_completed_activity: bool = False
    ) -> InsightTrigger:
        """
        Detect what triggered the insight check.
        
        Args:
            workflow_name: Current workflow
            workflow_step: Current step in workflow
            message: User's message
            just_completed_activity: Whether user just completed external activity
            
        Returns:
            InsightTrigger enum
        """
        message_lower = message.lower().strip()
        
        # Trigger 1: After mood logging
        if workflow_name == 'mood_logging' and workflow_step in ['mood_selected', 'suggesting_action']:
            return InsightTrigger.AFTER_MOOD_LOG
        
        # Trigger 2: After activity logging
        if workflow_name == 'activity_logging' and 'logged' in workflow_step:
            return InsightTrigger.AFTER_ACTIVITY_LOG
        
        # Trigger 3: After external activity completion
        if just_completed_activity:
            return InsightTrigger.AFTER_EXTERNAL_ACTIVITY
        
        # Trigger 4: User asks about progress
        progress_keywords = [
            'how am i doing', 'my progress', 'how have i been',
            'show my stats', 'my trends', 'my patterns',
            'am i improving', 'getting better'
        ]
        if any(keyword in message_lower for keyword in progress_keywords):
            return InsightTrigger.USER_ASKS_PROGRESS
        
        # Trigger 5: Engagement drop (detected by context)
        # This would be set by ContextAwareResponseEngine
        
        return InsightTrigger.NONE
    
    # ===== PRIVATE VALIDATION METHODS =====
    
    def _is_venting(self, context: Dict) -> bool:
        """Check if user is in emotional venting state"""
        intent = context.get('intent', '')
        intensity = context.get('intensity', '')
        
        # Venting indicators
        if intent == 'venting':
            return True
        
        if intensity in ['severe', 'high']:
            return True
        
        return False
    
    def _is_clarifying(self, context: Dict) -> bool:
        """Check if user is in clarification flow"""
        state = context.get('state', '')
        
        # Don't show insights during clarification
        if state in ['clarification_pending', 'asking_mood', 'asking_reason']:
            return True
        
        return False
    
    def _exceeded_session_limit(self, user_id: int) -> bool:
        """Check if session limit exceeded (max 1 per session)"""
        count = self._insights_this_session.get(user_id, 0)
        return count >= 1
    
    def _shown_recently(self, user_id: int, hours: int = 24) -> bool:
        """Check if insight shown within X hours"""
        last_shown = self._last_insight_shown.get(user_id)
        
        if not last_shown:
            return False
        
        time_since = datetime.now() - last_shown
        return time_since < timedelta(hours=hours)
    
    def _enough_mood_logs_passed(self, user_id: int, min_logs: int = 3) -> bool:
        """Check if enough mood logs passed since last insight"""
        logs_count = self._mood_logs_since_insight.get(user_id, 999)  # Default to high number
        return logs_count >= min_logs
    
    def _validate_trigger_context(self, trigger: InsightTrigger, context: Dict) -> bool:
        """Validate trigger-specific context requirements"""
        
        if trigger == InsightTrigger.AFTER_MOOD_LOG:
            # Only show after negative mood with reason
            mood = context.get('mood_emoji', '')
            reason = context.get('reason')
            negative_moods = ['😟', '😰', '😢', '😭', '😡', '😤', '😔']
            
            return mood in negative_moods and reason is not None
        
        elif trigger == InsightTrigger.AFTER_ACTIVITY_LOG:
            # Only show after significant activity (not just water)
            activity_type = context.get('activity_type', '')
            significant_activities = ['sleep', 'exercise']
            
            return activity_type in significant_activities
        
        elif trigger == InsightTrigger.AFTER_EXTERNAL_ACTIVITY:
            # Always valid if user completed activity
            return True
        
        elif trigger == InsightTrigger.USER_ASKS_PROGRESS:
            # Always valid - user explicitly asked
            return True
        
        elif trigger == InsightTrigger.ENGAGEMENT_DROP:
            # Check if engagement is actually low
            acceptance_rate = context.get('acceptance_rate', 100)
            return acceptance_rate < 30
        
        return False


# Global instance
_timing_controller = None

def get_timing_controller() -> InsightTimingController:
    """Get or create global InsightTimingController instance"""
    global _timing_controller
    if _timing_controller is None:
        _timing_controller = InsightTimingController()
    return _timing_controller
