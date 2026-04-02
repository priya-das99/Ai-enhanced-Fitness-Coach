"""
Intent Analyzer Service
Detects user's true intent: venting, logging, seeking action, or chatting
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Analyzes user intent beyond just mood/activity classification"""
    
    def analyze_user_intent(self, message: str, context: Dict = None) -> Dict:
        """
        Determine user's true intent
        
        Args:
            message: User's message
            context: Additional context (mood, history, etc.)
            
        Returns:
            {
                'intent_type': 'venting' | 'logging' | 'action_seeking' | 'chatting',
                'confidence': float,
                'signals': list of detected signals
            }
        """
        message_lower = message.lower()
        signals = []
        
        # Check for action-seeking signals
        action_words = ['help', 'suggest', 'what should', 'recommend', 'advice', 
                       'want to', 'need to', 'how do i', 'can you']
        has_action_words = any(word in message_lower for word in action_words)
        
        # Check for venting signals
        venting_words = ['again', 'still', 'always', 'every time', 'can\'t', 
                        'so', 'really', 'very', 'extremely']
        has_venting_words = any(word in message_lower for word in venting_words)
        
        # Check for questions (usually action-seeking)
        has_question = '?' in message
        
        # Check for logging signals
        logging_words = ['logged', 'slept', 'drank', 'exercised', 'hours', 'glasses']
        has_logging_words = any(word in message_lower for word in logging_words)
        
        # Check message length (short = logging, long = venting/chatting)
        word_count = len(message.split())
        
        # Determine intent
        if has_logging_words or (word_count <= 5 and not has_venting_words):
            intent_type = 'logging'
            confidence = 0.8
            signals.append('logging_keywords')
        
        elif has_question or has_action_words:
            intent_type = 'action_seeking'
            confidence = 0.9
            signals.append('question_or_action_words')
        
        elif has_venting_words or word_count > 10:
            intent_type = 'venting'
            confidence = 0.7
            signals.append('venting_indicators')
        
        else:
            intent_type = 'chatting'
            confidence = 0.6
            signals.append('default_chat')
        
        # Adjust based on context
        if context:
            # If user has been active recently, likely logging
            if context.get('recent_activity'):
                if intent_type == 'venting':
                    intent_type = 'logging'
                    signals.append('recent_activity_context')
            
            # If recurring pattern, likely venting
            if context.get('recurring_pattern'):
                if intent_type == 'logging':
                    intent_type = 'venting'
                    confidence = 0.8
                    signals.append('recurring_pattern_context')
        
        return {
            'intent_type': intent_type,
            'confidence': confidence,
            'signals': signals,
            'show_buttons': intent_type in ['action_seeking', 'logging'],
            'show_insight': intent_type in ['venting', 'action_seeking'],
            'tone': self._get_tone_for_intent(intent_type)
        }
    
    def _get_tone_for_intent(self, intent_type: str) -> str:
        """Get appropriate tone for intent"""
        tone_map = {
            'venting': 'empathetic',
            'logging': 'encouraging',
            'action_seeking': 'helpful',
            'chatting': 'friendly'
        }
        return tone_map.get(intent_type, 'neutral')
    
    def detect_intensity(self, message: str, history: Dict = None) -> Dict:
        """
        Detect intensity of emotion/feeling
        
        Returns:
            {
                'intensity': 'mild' | 'moderate' | 'severe' | 'recurring',
                'indicators': list of what indicated this level
            }
        """
        message_lower = message.lower()
        indicators = []
        
        # Check for intensity words
        severe_words = ['exhausted', 'terrible', 'horrible', 'awful', 'can\'t take']
        moderate_words = ['stressed', 'worried', 'anxious', 'frustrated']
        mild_words = ['tired', 'okay', 'fine', 'bit']
        
        # Check for recurring indicators
        recurring_words = ['again', 'still', 'always', 'every day', 'constantly']
        has_recurring = any(word in message_lower for word in recurring_words)
        
        # Determine intensity
        if has_recurring:
            intensity = 'recurring'
            indicators.append('recurring_language')
        elif any(word in message_lower for word in severe_words):
            intensity = 'severe'
            indicators.append('severe_language')
        elif any(word in message_lower for word in moderate_words):
            intensity = 'moderate'
            indicators.append('moderate_language')
        else:
            intensity = 'mild'
            indicators.append('mild_language')
        
        # Check history for recurring pattern
        if history and history.get('frequency', 0) >= 3:
            intensity = 'recurring'
            indicators.append('historical_pattern')
        
        return {
            'intensity': intensity,
            'indicators': indicators,
            'requires_immediate_support': intensity in ['severe', 'recurring']
        }


def get_intent_analyzer() -> IntentAnalyzer:
    """Get or create IntentAnalyzer instance"""
    return IntentAnalyzer()
