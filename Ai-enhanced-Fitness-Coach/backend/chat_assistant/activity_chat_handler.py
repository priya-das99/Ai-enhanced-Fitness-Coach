# activity_chat_handler.py
# Handle activity-related chat interactions

from .activity_intent_detector import ActivityIntentDetector
from .health_activity_logger import HealthActivityLogger
from .predefined_activities import PredefinedActivities
from .conversation_state import get_user_data, save_user_data
from .llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

class ActivityChatHandler:
    """Handle activity logging through chat"""
    
    def __init__(self):
        self.intent_detector = ActivityIntentDetector()
        self.activity_logger = HealthActivityLogger()
        self.llm_service = get_llm_service()
    
    def process_activity_message(self, user_id, message, mood_logged=False):
        """
        Process message for activity logging
        Returns: dict with response or None if no activity detected
        """
        # Detect activities from message
        activities = self.intent_detector.detect_all_activities(message)
        
        if activities:
            # Log all detected activities
            logged_activities = []
            for activity in activities:
                try:
                    activity_id = self.activity_logger.log_activity(
                        user_id=user_id,
                        activity_type=activity['activity_type'],
                        value=activity['value'],
                        unit=activity['unit'],
                        notes=activity['notes']
                    )
                    logged_activities.append(activity)
                    logger.info(f"✅ Logged {activity['activity_type']}: {activity['value']} {activity['unit']}")
                except Exception as e:
                    logger.error(f"Failed to log activity: {e}")
            
            if logged_activities:
                # Generate confirmation message
                return self._generate_activity_confirmation(logged_activities, message)
        
        # Check if we should suggest predefined activities
        if self.intent_detector.should_suggest_activities(message, mood_logged):
            mood = get_user_data(user_id, 'mood_emoji') or '😐'
            suggestions = PredefinedActivities.get_suggestions_for_mood(mood)
            
            return {
                'message': 'Would you like to log any of these activities?',
                'ui_elements': ['activity_buttons'],
                'activities': suggestions,
                'state': 'AWAITING_ACTIVITY_SELECTION'
            }
        
        return None
    
    def handle_activity_button_click(self, user_id, activity_id):
        """Handle when user clicks a predefined activity button"""
        activity = PredefinedActivities.get_activity_by_id(activity_id)
        
        if not activity:
            return {
                'message': 'Sorry, I couldn\'t find that activity.',
                'ui_elements': [],
                'state': 'IDLE'
            }
        
        # Save the selected activity for next input
        save_user_data(user_id, 'pending_activity', activity_id)
        
        return {
            'message': activity['prompt'],
            'ui_elements': ['text_input'],
            'state': 'AWAITING_ACTIVITY_VALUE'
        }
    
    def handle_activity_value_input(self, user_id, message):
        """Handle value input for a pending activity"""
        activity_id = get_user_data(user_id, 'pending_activity')
        
        if not activity_id:
            return None
        
        activity = PredefinedActivities.get_activity_by_id(activity_id)
        if not activity:
            return None
        
        # Extract value from message
        value = self.intent_detector.extract_number(message)
        
        if not value:
            return {
                'message': 'I couldn\'t understand that. Please enter a number.',
                'ui_elements': ['text_input'],
                'state': 'AWAITING_ACTIVITY_VALUE'
            }
        
        # Log the activity
        try:
            self.activity_logger.log_activity(
                user_id=user_id,
                activity_type=activity['activity_type'],
                value=value,
                notes=message
            )
            
            # Clear pending activity
            save_user_data(user_id, 'pending_activity', None)
            
            # Generate confirmation
            return self._generate_single_activity_confirmation(
                activity['activity_type'], value, activity.get('unit', '')
            )
        
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return {
                'message': 'Sorry, I couldn\'t log that activity. Please try again.',
                'ui_elements': [],
                'state': 'IDLE'
            }
    
    def _generate_activity_confirmation(self, activities, original_message):
        """Generate confirmation message for logged activities"""
        if not activities:
            return None
        
        # Use LLM for natural confirmation
        if self.llm_service.is_available():
            activities_text = ", ".join([
                f"{a['value']} {a['unit']} of {a['activity_type']}"
                for a in activities
            ])
            
            prompt = f"""You are a supportive wellness assistant. The user said: "{original_message}"

You successfully logged: {activities_text}

Generate a brief, encouraging confirmation (1-2 sentences). Be warm and supportive.

Examples:
- "Great! I've logged 2 glasses of water for you. Stay hydrated! 💧"
- "Perfect! I've recorded 8 hours of sleep. Rest is so important! 😴"
- "Awesome! I've logged your exercise. Keep up the great work! 🏃"

Response:"""
            
            response_text = self.llm_service.call(prompt, max_tokens=50, temperature=0.7)
            if response_text:
                return {
                    'message': response_text,
                    'ui_elements': [],
                    'state': 'IDLE'
                }
        
        # Fallback confirmation
        if len(activities) == 1:
            a = activities[0]
            return {
                'message': f"✅ Logged {a['value']} {a['unit']} of {a['activity_type']}!",
                'ui_elements': [],
                'state': 'IDLE'
            }
        else:
            return {
                'message': f"✅ Logged {len(activities)} activities!",
                'ui_elements': [],
                'state': 'IDLE'
            }
    
    def _generate_single_activity_confirmation(self, activity_type, value, unit):
        """Generate confirmation for single activity"""
        # Use LLM for natural confirmation
        if self.llm_service.is_available():
            prompt = f"""You are a supportive wellness assistant. The user just logged: {value} {unit} of {activity_type}

Generate a brief, encouraging confirmation (1 sentence). Be warm and supportive.

Examples:
- "Great! I've logged 2 glasses of water for you. Stay hydrated! 💧"
- "Perfect! I've recorded 8 hours of sleep. Rest is so important! 😴"

Response:"""
            
            response_text = self.llm_service.call(prompt, max_tokens=40, temperature=0.7)
            if response_text:
                return {
                    'message': response_text,
                    'ui_elements': [],
                    'state': 'IDLE'
                }
        
        # Fallback
        return {
            'message': f"✅ Logged {value} {unit} of {activity_type}!",
            'ui_elements': [],
            'state': 'IDLE'
        }
    
    def get_today_summary(self, user_id):
        """Get summary of today's activities"""
        activities = self.activity_logger.get_today_activities(user_id)
        
        if not activities:
            return {
                'message': 'You haven\'t logged any activities today yet.',
                'ui_elements': [],
                'state': 'IDLE'
            }
        
        # Build summary
        summary_lines = []
        for activity in activities:
            summary_lines.append(
                f"• {activity['activity_type']}: {activity['value']} {activity['unit']}"
            )
        
        summary_text = "\n".join(summary_lines)
        
        return {
            'message': f"Here's what you've logged today:\n\n{summary_text}",
            'ui_elements': [],
            'state': 'IDLE'
        }
