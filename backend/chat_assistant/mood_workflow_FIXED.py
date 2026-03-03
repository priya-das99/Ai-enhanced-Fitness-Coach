# mood_workflow.py
# Minimal working mood logging workflow with engagement buttons

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .mood_handler import (
    validate_mood_emoji, save_mood_log, is_positive_mood, get_mood_value
)
import logging

logger = logging.getLogger(__name__)

class MoodWorkflow(BaseWorkflow):
    """
    Simplified mood logging workflow with engagement buttons
    
    Flow:
    1. Detect mood from message
    2. Log mood
    3. Show confirmation + engagement buttons
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="mood_logging",
            handled_intents=['mood_logging', 'mood_check', 'feeling', 'emotion']
        )
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start mood logging workflow"""
        logger.info(f"Starting mood workflow for user {user_id}")
        
        # Check if message is a direct emoji selection
        if validate_mood_emoji(message.strip()):
            mood_emoji = message.strip()
            return self._log_and_respond(user_id, mood_emoji, state)
        
        # Try to extract mood from message
        from .mood_extractor import extract_mood_from_message
        mood_emoji, confidence = extract_mood_from_message(message)
        
        if mood_emoji:
            logger.info(f"Extracted mood: {mood_emoji} (confidence: {confidence})")
            return self._log_and_respond(user_id, mood_emoji, state)
        
        # Couldn't extract mood - ask explicitly
        state.start_workflow(self.workflow_name, {'step': 'asking_mood'})
        return self._ask_clarification(
            message="How are you feeling?",
            ui_elements=['emoji_selector']
        )
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Process message in active mood workflow"""
        step = state.get_workflow_data('step')
        
        if step == 'asking_mood':
            if validate_mood_emoji(message):
                return self._log_and_respond(user_id, message, state)
            else:
                return self._ask_clarification(
                    message="Please select a mood emoji.",
                    ui_elements=['emoji_selector']
                )
        
        # Unknown step
        return self._complete_workflow(message="Mood logging completed.")
    
    def _log_and_respond(self, user_id: int, mood_emoji: str, state: WorkflowState) -> WorkflowResponse:
        """Log mood and return response with engagement buttons"""
        # Save mood
        save_mood_log(user_id, mood_emoji, reason=None)
        
        # Publish event
        try:
            from app.services.event_publisher import get_event_publisher
            publisher = get_event_publisher()
            publisher.publish_mood_logged(
                user_id=str(user_id),
                mood_emoji=mood_emoji,
                reason=None,
                mood_value=get_mood_value(mood_emoji)
            )
            logger.info(f"📊 Published mood_logged event for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to publish mood_logged event: {e}")
        
        # Complete workflow
        state.complete_workflow()
        
        # Get mood name
        mood_name = self._get_mood_name(mood_emoji)
        
        # Return response with engagement buttons
        return WorkflowResponse(
            message=f"✓ Logged: {mood_name} mood {mood_emoji}\n\nThat's wonderful! Keep it up! 😊\n\nWhat would you like to do next?",
            completed=True,
            next_state=ConversationState.IDLE,
            ui_elements=['action_buttons_multiple'],
            actions=[
                {'id': 'log_exercise', 'name': '🏃 Log Exercise'},
                {'id': 'log_water', 'name': '💧 Log Water'},
                {'id': 'log_sleep', 'name': '😴 Log Sleep'},
                {'id': 'view_progress', 'name': '📊 View Progress'}
            ],
            events=[{'type': 'mood_logged', 'mood': mood_emoji, 'reason': None}]
        )
    
    def _get_mood_name(self, mood_emoji: str) -> str:
        """Get friendly name for mood emoji"""
        mood_names = {
            '😊': 'Happy',
            '😄': 'Very Happy',
            '😐': 'Neutral',
            '😔': 'Sad',
            '😢': 'Very Sad',
            '😡': 'Angry',
            '😰': 'Anxious',
            '😴': 'Tired',
            '🤗': 'Grateful',
            '😌': 'Calm'
        }
        return mood_names.get(mood_emoji, 'Good')
