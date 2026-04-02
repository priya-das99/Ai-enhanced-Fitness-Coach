"""
Engagement Context Analyzer
Analyzes conversation context to determine appropriate post-workflow engagement
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EngagementContextAnalyzer:
    """Analyzes conversation context and suggests engagement strategies"""
    
    def analyze_context(self, user_id: int, workflow_data: dict) -> dict:
        """
        Analyze conversation context and return engagement strategy
        
        Args:
            user_id: User ID
            workflow_data: Data from completed workflow including:
                - mood_emoji
                - reason
                - declined_activity
                - completed_activity
                - activity_rating
        
        Returns:
            {
                'message': str,
                'buttons': list,
                'priority': str,
                'reason': str
            }
        """
        
        # Extract context
        mood_emoji = workflow_data.get('mood_emoji')
        reason = workflow_data.get('reason')
        declined_activity = workflow_data.get('declined_activity', False)
        completed_activity = workflow_data.get('completed_activity')
        activity_rating = workflow_data.get('activity_rating')
        
        # Get user patterns
        patterns = self._get_user_patterns(user_id)
        
        # Scenario 1: Declined activity + negative mood (HIGH PRIORITY)
        if declined_activity and self._is_negative_mood(mood_emoji):
            return self._create_declined_negative_engagement(reason, patterns)
        
        # Scenario 2: Completed activity + good rating (HIGH PRIORITY)
        if completed_activity and activity_rating and activity_rating >= 4:
            return self._create_positive_outcome_engagement(completed_activity, patterns)
        
        # Scenario 3: On a streak (HIGH PRIORITY - celebrate!)
        if patterns.get('streak', 0) >= 3:
            return self._create_streak_engagement(patterns['streak'])
        
        # Scenario 4: Positive mood (LOW PRIORITY)
        if self._is_positive_mood(mood_emoji):
            return self._create_positive_mood_engagement()
        
        # Scenario 5: Completed activity + low rating (MEDIUM PRIORITY)
        if completed_activity and activity_rating and activity_rating < 3:
            return self._create_low_rating_engagement(completed_activity)
        
        # Default: Minimal engagement
        return self._create_default_engagement()
    
    def _create_declined_negative_engagement(self, reason: str, patterns: dict) -> dict:
        """User declined activity while in negative mood"""
        
        # Check if prolonged stress
        if patterns.get('has_prolonged_stress'):
            message = "I understand you're not ready right now. I'm here if you need me. Would you like to:"
        else:
            message = "No problem. I'm here if you need anything. Would you like to:"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'Get suggestions later', 'action': 'remind_later', 'description': 'Set a reminder to check in later'},
                {'label': 'Talk about it', 'action': 'open_chat', 'description': 'Chat with me about how you\'re feeling'},
                {'label': "I'm good for now", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'high',
            'reason': 'declined_while_stressed'
        }
    
    def _create_positive_outcome_engagement(self, activity: str, patterns: dict) -> dict:
        """User completed activity with good rating"""
        
        message = "Glad that helped! Want to:"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'Try another activity', 'action': 'suggest_more', 'description': 'Get more personalized suggestions'},
                {'label': 'Set daily reminder', 'action': 'create_reminder', 'description': 'Never forget to check in'},
                {'label': "Done for now", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'high',
            'reason': 'positive_outcome'
        }
    
    def _create_streak_engagement(self, streak: int) -> dict:
        """User is on an activity streak"""
        
        message = f"🔥 {streak}-day streak! You're doing great! Want to:"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'See my progress', 'action': 'show_stats', 'description': 'View your activity history'},
                {'label': 'Join a challenge', 'action': 'browse_challenges', 'description': 'Take on a new challenge'},
                {'label': "Done for now", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'high',
            'reason': 'celebrate_streak'
        }
    
    def _create_positive_mood_engagement(self) -> dict:
        """User logged positive mood"""
        
        message = "That's great! Want to:"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'Start a challenge', 'action': 'browse_challenges', 'description': 'Take on a new challenge'},
                {'label': 'Log an activity', 'action': 'log_activity', 'description': 'Track what you did today'},
                {'label': "Done for now", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'low',
            'reason': 'positive_mood'
        }
    
    def _create_low_rating_engagement(self, activity: str) -> dict:
        """User completed activity but gave low rating"""
        
        message = "Thanks for trying that. Want to try something different?"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'Get other suggestions', 'action': 'suggest_more', 'description': 'Try different activities'},
                {'label': 'Tell me what would help', 'action': 'open_chat', 'description': 'Chat about what you need'},
                {'label': "I'm good", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'medium',
            'reason': 'low_rating'
        }
    
    def _create_default_engagement(self) -> dict:
        """Default minimal engagement"""
        
        message = "Your mood has been logged. I'm here if you need anything!"
        
        return {
            'message': message,
            'buttons': [
                {'label': 'Get suggestions', 'action': 'suggest_activities', 'description': 'Get personalized activity suggestions'},
                {'label': "I'm good", 'action': 'dismiss', 'description': 'Close this conversation'}
            ],
            'priority': 'low',
            'reason': 'default'
        }
    
    def _get_user_patterns(self, user_id: int) -> dict:
        """Get user patterns for context"""
        try:
            from app.services.pattern_detector import PatternDetector
            detector = PatternDetector()
            patterns = detector.detect_all_patterns(user_id)
            return {
                'streak': patterns['activity_patterns']['streak'],
                'has_prolonged_stress': patterns['mood_patterns']['has_prolonged_stress']
            }
        except Exception as e:
            logger.warning(f"Failed to get user patterns: {e}")
            return {'streak': 0, 'has_prolonged_stress': False}
    
    def _is_negative_mood(self, mood_emoji: str) -> bool:
        """Check if mood is negative"""
        if not mood_emoji:
            return False
        negative_moods = ['😟', '😰', '😢', '😭', '😡', '😤', '😕']
        return mood_emoji in negative_moods
    
    def _is_positive_mood(self, mood_emoji: str) -> bool:
        """Check if mood is positive"""
        if not mood_emoji:
            return False
        positive_moods = ['😊', '🙂', '😄', '😁']
        return mood_emoji in positive_moods
