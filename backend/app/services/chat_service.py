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
        """Initialize or resume conversation for user with personalized insights"""
        # Get or create session
        session_id = self.get_or_create_session(user_id)
        
        # Check for personalized insights
        greeting_message = self._get_personalized_greeting(user_id)
        
        if greeting_message:
            # Use insight-based greeting - include ALL fields from greeting
            response = greeting_message.copy()  # Copy all fields including activity_options
            # Ensure required fields are present
            if 'state' not in response:
                response['state'] = 'idle'
        else:
            # Default greeting
            from chat_assistant.chat_engine_workflow import init_conversation
            response = init_conversation(user_id)
        
        # Save bot's init message with session
        self.chat_repo.save_message_with_session(
            user_id=user_id,
            session_id=session_id,
            message=response.get('message', ''),
            sender='bot',
            metadata={
                'ui_elements': response.get('ui_elements', []),
                'state': response.get('state', 'idle'),
                'insight': response.get('insight')
            }
        )
        
        # Load recent chat history
        response['chat_history'] = self.chat_repo.get_recent_messages(user_id, limit=20)
        
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
            
            from app.services.insight_system import InsightSystem
            
            insight_system = InsightSystem()
            insight = insight_system.get_greeting_insight(user_id)
            
            if insight:
                # Mark that we've shown personalized greeting today
                self.personalized_greeting_shown[user_id] = today
                
                # Build greeting with insight
                message = insight['message']
                
                # Show activity buttons ONLY on initial greeting
                # Frontend will keep them fixed at top, so no need to repeat
                ui_elements = ['activity_buttons']
                extra_data = {
                    'activity_options': [
                        {'id': 'log_water', 'label': '💧 Log Water'},
                        {'id': 'log_sleep', 'label': '😴 Log Sleep'},
                        {'id': 'log_exercise', 'label': '🏃 Log Exercise'},
                        {'id': 'log_mood', 'label': '😊 Log Mood'}
                    ],
                    'persistent_buttons': False  # Don't repeat in chat
                }
                
                result = {
                    'message': message,
                    'ui_elements': ui_elements,
                    'insight': insight
                }
                
                # Add extra data
                result.update(extra_data)
                
                return result
            
            return None
            
        except Exception as e:
            import logging
            logging.error(f"Failed to generate personalized greeting: {e}")
            return None
    
    def process_message(self, user_id: int, message: str) -> Dict:
        """Process user message"""
        # Get or create session
        session_id = self.get_or_create_session(user_id)
        
        # Save user message with session
        self.chat_repo.save_message_with_session(
            user_id=user_id,
            session_id=session_id,
            message=message,
            sender='user'
        )
        
        # Import here to avoid circular imports
        from chat_assistant.chat_engine_workflow import process_message
        response = process_message(user_id, message)
        
        # Save bot response with session
        self.chat_repo.save_message_with_session(
            user_id=user_id,
            session_id=session_id,
            message=response.get('message', ''),
            sender='bot',
            metadata={
                'ui_elements': response.get('ui_elements', []),
                'state': response.get('state', 'idle'),
                'completed': response.get('completed', False)
            }
        )
        
        return response
    
    def get_history(self, user_id: int) -> List[Dict]:
        """Get chat history for user"""
        from chat_assistant.mood_handler import get_user_mood_logs
        return get_user_mood_logs(user_id)
    
    def get_chat_messages(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get recent chat messages"""
        return self.chat_repo.get_recent_messages(user_id, limit)
