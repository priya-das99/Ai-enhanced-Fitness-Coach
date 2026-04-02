# app/services/chat_service.py
# Chat business logic

from app.repositories.chat_repository import ChatRepository
from typing import Dict, List

class ChatService:
    """Service for chat operations"""
    
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.active_sessions = {}  # user_id -> session_id
        self.personalized_greeting_shown = {}  # user_id -> date (in-memory cache)
    
    def get_or_create_session(self, user_id: int) -> int:
        """
        Get active session or create new one
        
        Args:
            user_id: User ID
        
        Returns:
            Session ID
        """
        if user_id not in self.active_sessions:
            session_id = self.chat_repo.create_session(user_id)
            self.active_sessions[user_id] = session_id
        return self.active_sessions[user_id]
    
    def init_conversation(self, user_id: int) -> Dict:
        """Initialize conversation - show greeting for new users, load history for existing users"""
        # Get or create session
        session_id = self.get_or_create_session(user_id)
        
        # Load recent chat history to check if user needs greeting
        chat_history = self.chat_repo.get_recent_messages(user_id, limit=50)
        
        # Activity buttons for all users (including Log Mood)
        activity_buttons = [
            {"id": "log_water",    "label": "💧 Log Water"},
            {"id": "log_sleep",    "label": "😴 Log Sleep"},
            {"id": "log_exercise", "label": "🏃 Log Exercise"},
            {"id": "log_weight",   "label": "⚖️ Log Weight"},
            {"id": "log_steps",    "label": "👟 Log Steps"},
            {"id": "log_calories", "label": "🔥 Log Calories"},
            {"id": "log_meal",     "label": "🍽️ Log Meal"},
            {"id": "log_mood",     "label": "😊 Log Mood"},
        ]
        
        # Check if user needs a greeting today
        from datetime import date
        today = date.today().isoformat()
        
        needs_greeting = True
        has_messages_today = False
        
        if chat_history:
            # Check if there are ANY messages from today (not just greetings)
            for msg in chat_history:
                msg_date = msg.get('timestamp', '')[:10]  # Get date part
                if msg_date == today:
                    has_messages_today = True
                    break
            
            # If user has ANY messages today, no greeting needed
            if has_messages_today:
                needs_greeting = False
        
        # Debug logging
        import logging
        logging.info(f"User {user_id} greeting check: needs_greeting={needs_greeting}, has_messages_today={has_messages_today}, today={today}")
        if chat_history:
            recent_messages = [(msg.get('timestamp', '')[:10], msg.get('sender'), msg.get('message', '')[:30]) 
                             for msg in chat_history[-5:]]
            logging.info(f"Recent messages: {recent_messages}")
        
        if needs_greeting:
            # Try to get personalized greeting with insights first
            personalized_greeting = self._get_personalized_greeting(user_id)
            
            if personalized_greeting:
                # Use personalized greeting with insights
                greeting_message = personalized_greeting['message']
                ui_elements = personalized_greeting.get('ui_elements', ['emoji_selector', 'activity_buttons'])
                
                # Save the personalized greeting to chat history
                self.chat_repo.save_message_with_session(
                    user_id=user_id,
                    session_id=session_id,
                    message=greeting_message,
                    sender='bot',
                    metadata={
                        'ui_elements': ui_elements,
                        'activity_options': activity_buttons,
                        'state': 'idle',
                        'insight_type': 'proactive_greeting',
                        'has_insight': True
                    }
                )
                
                # Return response with personalized greeting and insights
                response = {
                    'message': greeting_message,
                    'state': 'idle',
                    'ui_elements': ui_elements,
                    'activity_options': activity_buttons,
                    'is_new_greeting': True,
                    'has_insight': True,
                    'insight': personalized_greeting.get('insight')
                }
            else:
                # Fallback to default greeting
                greeting_message = "Hey! How are you feeling today?"
                
                # Save the greeting to chat history
                self.chat_repo.save_message_with_session(
                    user_id=user_id,
                    session_id=session_id,
                    message=greeting_message,
                    sender='bot',
                    metadata={
                        'ui_elements': ['emoji_selector', 'activity_buttons'],
                        'activity_options': activity_buttons,
                        'state': 'idle'
                    }
                )
                
                # Return response with greeting and UI elements
                response = {
                    'message': greeting_message,
                    'state': 'idle',
                    'ui_elements': ['emoji_selector', 'activity_buttons'],
                    'activity_options': activity_buttons,
                    'is_new_greeting': True
                }
        else:
            # User already has conversation today, just return UI elements
            response = {
                'message': '',  # No new message, frontend will load history
                'state': 'idle',
                'ui_elements': ['emoji_selector', 'activity_buttons'],
                'activity_options': activity_buttons,
                'is_new_greeting': False
            }
        
        return response
    
    def _get_personalized_greeting(self, user_id: int) -> Dict:
        """Generate personalized greeting based on user patterns"""
        try:
            from datetime import date
            
            # Check if we already showed personalized greeting today
            today = date.today().isoformat()
            if user_id in self.personalized_greeting_shown:
                if self.personalized_greeting_shown[user_id] == today:
                    # Already shown today, return None to use default greeting
                    import logging
                    logging.info(f"Personalized greeting already shown today for user {user_id}")
                    return None
            
            # Use the unified insight system
            from app.services.unified_insight_system import get_unified_insight_system
            
            insight_system = get_unified_insight_system()
            insight = insight_system.get_greeting_insight(user_id)
            
            if insight:
                # Mark that we've shown personalized greeting today
                self.personalized_greeting_shown[user_id] = today
                
                # Build greeting with insight
                message = insight['message']
                
                # Show activity buttons with the insight
                ui_elements = ['emoji_selector', 'activity_buttons']
                extra_data = {
                    'activity_options': [
                        {'id': 'log_water', 'label': '💧 Log Water'},
                        {'id': 'log_sleep', 'label': '😴 Log Sleep'},
                        {'id': 'log_exercise', 'label': '🏃 Log Exercise'},
                        {'id': 'log_mood', 'label': '😊 Log Mood'},
                        {'id': 'log_weight', 'label': '⚖️ Log Weight'},
                        {'id': 'log_steps', 'label': '👟 Log Steps'},
                        {'id': 'log_calories', 'label': '🔥 Log Calories'},
                        {'id': 'log_meal', 'label': '🍽️ Log Meal'}
                    ]
                }
                
                result = {
                    'message': message,
                    'ui_elements': ui_elements,
                    'insight': insight
                }
                
                # Add extra data
                result.update(extra_data)
                
                import logging
                logging.info(f"Generated proactive greeting insight for user {user_id}: {insight.get('pattern', {}).get('type', 'unknown')}")
                
                return result
            
            return None
            
        except Exception as e:
            import logging
            logging.error(f"Failed to generate personalized greeting: {e}", exc_info=True)
            return None
    
    def process_message(self, user_id: int, message: str) -> Dict:
        """Process user message with comprehensive error handling"""
        # Get or create session
        session_id = self.get_or_create_session(user_id)
        
        # Save user message with session
        self.chat_repo.save_message_with_session(
            user_id=user_id,
            session_id=session_id,
            message=message,
            sender='user'
        )
        
        try:
            # Import here to avoid circular imports
            from chat_assistant.chat_engine_workflow import process_message
            response = process_message(user_id, message)
            
        except Exception as e:
            # If chat engine fails, use fallback response
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Chat engine failed for user {user_id}: {e}", exc_info=True)
            
            # Generate fallback response
            from chat_assistant.fallback_responses import get_fallback_response
            
            # Determine context from message
            message_lower = message.lower()
            if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
                context = "greeting"
            elif any(word in message_lower for word in ['feel', 'mood', 'emotion', 'happy', 'sad', 'stress']):
                context = "mood"
            elif any(word in message_lower for word in ['water', 'exercise', 'sleep', 'walk', 'run']):
                context = "activity"
            else:
                context = "general"
            
            response = get_fallback_response(message, context)
        
        # Save bot response with session
        self.chat_repo.save_message_with_session(
            user_id=user_id,
            session_id=session_id,
            message=response.get('message', ''),
            sender='bot',
            metadata={
                'ui_elements': response.get('ui_elements', []),
                'state': response.get('state', 'idle'),
                'completed': response.get('completed', False),
                'fallback_used': response.get('fallback_used', False)
            }
        )
        
        return response
    
    def get_history(self, user_id: int) -> List[Dict]:
        """Get chat history for user"""
        from chat_assistant.mood_handler import get_user_mood_logs
        return get_user_mood_logs(user_id)
    
    def get_chat_messages(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get recent chat messages"""
        return self.chat_repo.get_recent_messages(user_id, limit)

    def get_current_session_messages(self, user_id: int) -> List[Dict]:
        """Get messages from the current (latest) session only"""
        return self.chat_repo.get_current_session_messages(user_id)
