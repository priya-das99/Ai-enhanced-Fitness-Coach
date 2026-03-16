# fallback_responses.py
# Fallback responses when LLM service is unavailable

import random
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class FallbackResponseGenerator:
    """Generate fallback responses when LLM is unavailable"""
    
    def __init__(self):
        self.greeting_responses = [
            "Hello! I'm here to help you with wellness tracking and activities.",
            "Hi there! How can I assist you with your wellness journey today?",
            "Welcome! I can help you log activities, track your mood, and suggest wellness activities.",
            "Hello! I'm your wellness companion. What would you like to do today?"
        ]
        
        self.mood_responses = [
            "Thank you for sharing how you're feeling. Your mood has been logged.",
            "I've recorded your mood. Taking time to check in with yourself is important.",
            "Your mood entry has been saved. How you feel matters.",
            "Thanks for logging your mood. Self-awareness is a great first step."
        ]
        
        self.activity_responses = [
            "Great job! I've logged that activity for you.",
            "Awesome! Your activity has been recorded.",
            "Well done! I've saved that activity to your log.",
            "Nice work! Your activity is now tracked."
        ]
        
        self.general_responses = [
            "I can help you log activities like exercise, water intake, sleep, and mood.",
            "You can track various wellness activities with me - just tell me what you did!",
            "I'm here to help with wellness tracking. What would you like to log or learn about?",
            "I can assist with logging activities, tracking mood, and suggesting wellness tips."
        ]
        
        self.error_responses = [
            "I'm having trouble processing that right now. Could you try rephrasing your message?",
            "Something went wrong on my end. Please try again with a simpler message.",
            "I'm experiencing some technical difficulties. Can you try that again?",
            "I'm not able to process that request right now. Please try again in a moment."
        ]
        
        self.activity_keywords = {
            'water': ['water', 'drink', 'hydrat', 'glass', 'bottle'],
            'exercise': ['exercise', 'workout', 'run', 'walk', 'gym', 'cardio', 'strength'],
            'sleep': ['sleep', 'slept', 'bed', 'rest', 'nap'],
            'mood': ['feel', 'mood', 'emotion', 'happy', 'sad', 'stress', 'anxious', 'good', 'bad']
        }
    
    def get_greeting_response(self) -> str:
        """Get a random greeting response"""
        return random.choice(self.greeting_responses)
    
    def get_activity_response(self, message: str) -> str:
        """Get activity-specific response based on message content"""
        message_lower = message.lower()
        
        # Check for specific activity types
        for activity_type, keywords in self.activity_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if activity_type == 'mood':
                    return random.choice(self.mood_responses)
                else:
                    return random.choice(self.activity_responses)
        
        # Default activity response
        return random.choice(self.activity_responses)
    
    def get_general_response(self) -> str:
        """Get a general helpful response"""
        return random.choice(self.general_responses)
    
    def get_error_response(self) -> str:
        """Get an error/fallback response"""
        return random.choice(self.error_responses)
    
    def generate_response(self, message: str, context: str = "general") -> Dict:
        """
        Generate a fallback response based on message and context
        
        Args:
            message: User's message
            context: Context hint ('greeting', 'activity', 'mood', 'error', 'general')
            
        Returns:
            Dict with response structure
        """
        try:
            if context == "greeting":
                response_text = self.get_greeting_response()
            elif context == "activity":
                response_text = self.get_activity_response(message)
            elif context == "mood":
                response_text = random.choice(self.mood_responses)
            elif context == "error":
                response_text = self.get_error_response()
            else:
                # Try to detect activity type from message
                message_lower = message.lower()
                
                # Check for greeting patterns
                if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
                    response_text = self.get_greeting_response()
                
                # Check for activity patterns
                elif any(keyword in message_lower for keywords in self.activity_keywords.values() for keyword in keywords):
                    response_text = self.get_activity_response(message)
                
                # Default to general response
                else:
                    response_text = self.get_general_response()
            
            return {
                'message': response_text,
                'ui_elements': ['activity_buttons'],  # Always show activity buttons
                'state': 'idle',
                'completed': True,
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            return {
                'message': "I'm here to help with your wellness journey. What would you like to do?",
                'ui_elements': ['activity_buttons'],
                'state': 'idle',
                'completed': True,
                'fallback_used': True
            }

# Global instance
_fallback_generator = FallbackResponseGenerator()

def get_fallback_response(message: str, context: str = "general") -> Dict:
    """Get a fallback response when LLM is unavailable"""
    return _fallback_generator.generate_response(message, context)

def get_error_fallback() -> Dict:
    """Get a fallback response for errors"""
    return _fallback_generator.generate_response("", "error")