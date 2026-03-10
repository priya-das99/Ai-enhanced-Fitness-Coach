# chat_engine_workflow.py
# Phase 1 Refactoring: LLM-based intent routing
# Workflows are now pure handlers, intent detection is centralized

from .workflow_registry import WorkflowRegistry
from .llm_service import get_llm_service
from .response_validator import validate_response
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ChatEngineWorkflow:
    """
    Main chat engine with LLM-based intent routing (Phase 1)
    Event-driven architecture (Phase 2)
    
    Flow:
    1. Check if there's an active workflow
    2. If active, continue that workflow
    3. If idle, use LLM to detect intent
    4. Map intent → workflow
    5. Execute workflow
    6. Publish events (Phase 2)
    """
    
    def __init__(self):
        self.registry = WorkflowRegistry()
        self.llm_service = get_llm_service()
        self.enable_multi_intent = True  # Phase 3: Multi-intent support
        self.enable_validation = True  # Phase 3: Response validation
        self.enable_events = True  # Phase 2: Event publishing
    
    def process_message(self, user_id: str, message: str) -> dict:
        """
        Main entry point for processing user messages.
        
        Phase 1: Uses LLM intent detection instead of can_handle()
        Guardrails: Applied before any processing to ensure safety and scope
        
        Returns:
            dict with keys: message, ui_elements, completed, state
        """
        logger.info(f"[Phase 1] Processing message for user {user_id}: '{message}'")
        
        # ===== GUARDRAILS CHECK (FIRST PRIORITY) =====
        from .guardrails import apply_guardrails
        
        is_allowed, response_override, metadata = apply_guardrails(message)
        
        if not is_allowed:
            # Guardrail triggered - return response immediately without LLM call
            logger.warning(
                f"Guardrail triggered for user {user_id} | "
                f"Type: {metadata.get('violation_type')} | "
                f"Message: {message[:50]}..."
            )
            
            return {
                'message': response_override,
                'ui_elements': [],
                'state': 'idle',
                'completed': True,
                'guardrail_triggered': True,
                'violation_type': metadata.get('violation_type')
            }
        
        # Message passed guardrails - continue with normal processing
        logger.info(f"[Guardrails] Message passed all checks")
        
        # Use WorkflowState directly (it's already a singleton per user)
        from .unified_state import get_workflow_state
        workflow_state = get_workflow_state(user_id)
        
        logger.info(f"Current state: {workflow_state.state.value}, Active workflow: {workflow_state.active_workflow}")
        
        # ===== UNIVERSAL CONTEXT CHECK (NEW) =====
        # Check if this is a follow-up to recent activity using session summary
        if workflow_state.is_idle():  # Only check if no active workflow
            from .universal_context_handler import get_universal_context_handler
            context_handler = get_universal_context_handler()
            
            if context_handler.can_handle_followup(message, workflow_state):
                logger.info(f"[Universal Context] Handling follow-up request: '{message}'")
                followup_response = context_handler.handle_followup(message, workflow_state, user_id)
                
                if followup_response:
                    # Store messages in conversation history
                    workflow_state.add_message('user', message)
                    workflow_state.add_message('assistant', followup_response.message)
                    
                    # Convert to dict format
                    result = self._convert_response(followup_response, workflow_state, 'universal_context', user_id)
                    return result
        
        # Load conversation history from database if in-memory is empty (after restart/login)
        if len(workflow_state.conversation_history) == 0:
            try:
                from app.repositories.chat_repository import ChatRepository
                chat_repo = ChatRepository()
                
                # Load last 10 messages from database for context continuity
                db_messages = chat_repo.get_recent_messages(user_id, limit=10)
                
                if db_messages:
                    # Populate in-memory conversation_history
                    for msg in db_messages:
                        role = 'user' if msg['sender'] == 'user' else 'assistant'
                        workflow_state.conversation_history.append({
                            'role': role,
                            'content': msg['message']
                        })
                    
                    logger.info(f"✓ Loaded {len(db_messages)} messages from database for context continuity")
            except Exception as e:
                logger.warning(f"Failed to load conversation history from database: {e}")
        
        # Store user message in conversation history
        workflow_state.add_message('user', message)
        
        # Map common activity button names to log_ format
        ACTIVITY_BUTTON_MAP = {
            'water': 'log_water',
            'mood':'log_mood',
            'water_intake': 'log_water',
            'drink_water': 'log_water',
            'sleep': 'log_sleep',
            'rest': 'log_sleep',
            'sleep_log': 'log_sleep',
            'exercise': 'log_exercise',
            'workout': 'log_exercise',
            'weight': 'log_weight',
        }
        
        # Check for "log MOOD again" requests - these should go to mood workflow
        # Be specific to avoid catching "I want to log water" etc.
        message_lower_original = message.lower().strip()
        is_log_again_request = any(phrase in message_lower_original for phrase in [
            'log again', 'log my mood again', 'log mood again',
            'log it again', 'track again', 'log another mood',
            'want to log again', 'want to log my mood'
        ]) and not any(activity in message_lower_original for activity in [
            'water', 'exercise', 'sleep', 'weight', 'meal', 'workout'
        ])
        
        # If user wants to log again, route to mood workflow
        if is_log_again_request:
            logger.info(f"[Priority] Detected 'log again' request - routing to mood workflow")
            mood_workflow = self.registry.get_workflow_for_intent('mood_logging')
            if mood_workflow:
                response = mood_workflow.start(message, workflow_state, user_id)
                workflow_state.add_message('assistant', response.message)
                result = self._convert_response(response, workflow_state, 'mood_logging', user_id)
                return result
        
        # Check if this is a button click that should start a new workflow
        message_lower = message.lower().strip().replace(' ', '_')
        is_button_click = message_lower.startswith('log_')
        is_external_content_button = message_lower.startswith('start_content_')
        is_activity_start_button = message_lower.startswith('start_') and not is_external_content_button
        
        # Check for exact "I want to log X" patterns (more precise)
        if not is_button_click and message_lower in ['i_want_to_log_water', 'i_want_to_log_sleep', 'i_want_to_log_exercise', 'i_want_to_log_weight', 'i_want_to_log_mood']:
            is_button_click = True
            # Extract the actual button ID (e.g., "i_want_to_log_mood" -> "log_mood")
            message_lower = message_lower.replace('i_want_to_', '')
        
        # DEBUG: Log what we're receiving
        logger.info(f"[DEBUG] Received message: '{message}'")
        logger.info(f"[DEBUG] Normalized: '{message_lower}'")
        logger.info(f"[DEBUG] Is button click: {is_button_click}")
        logger.info(f"[DEBUG] Is external content: {is_external_content_button}")
        logger.info(f"[DEBUG] Is activity start: {is_activity_start_button}")
        
        # Also check if it's an activity button that needs mapping
        if not is_button_click and message_lower in ACTIVITY_BUTTON_MAP:
            is_button_click = True
            original_message = message
            message = ACTIVITY_BUTTON_MAP[message_lower]  # Normalize to log_ format
            logger.info(f"Mapped activity button '{original_message}' to '{message}'")
        
        # PRIORITY CHECK: Detect mood expressions even if there's an active workflow
        # This allows users to express their mood at any time
        is_mood_expression = self._is_mood_expression(message)
        
        if is_mood_expression and not is_button_click:
            logger.info(f"[Priority] Detected mood expression: '{message}' - switching to mood workflow")
            # Reset any active workflow and start mood workflow
            workflow_state.complete_workflow()
            mood_workflow = self.registry.get_workflow_for_intent('mood_logging')
            if mood_workflow:
                response = mood_workflow.start(message, workflow_state, user_id)
                workflow_state.add_message('assistant', response.message)
                result = self._convert_response(response, workflow_state, 'mood_logging', user_id)
                return result
        
        # PRIORITY CHECK: External content/activity buttons should always go to activity workflow
        # Even if there's an active mood workflow showing suggestions
        if is_external_content_button or is_activity_start_button:
            logger.info(f"[Priority] Detected external/activity button: '{message}' - routing to activity workflow")
            # Complete any active workflow
            if workflow_state.active_workflow:
                logger.info(f"Completing active workflow '{workflow_state.active_workflow}' to handle activity button")
                workflow_state.complete_workflow()
            
            # Route to activity workflow
            activity_workflow = self.registry.get_workflow_for_intent('activity_logging')
            if activity_workflow:
                response = activity_workflow.start(message, workflow_state, user_id)
                workflow_state.add_message('assistant', response.message)
                result = self._convert_response(response, workflow_state, 'activity_logging', user_id)
                return result
        
        # CRITICAL FIX: If there's an active workflow, ALWAYS send message to it first
        # Let the workflow decide if it can handle the message (including button clicks)
        if workflow_state.active_workflow and not workflow_state.is_idle():
            workflow = self.registry.get_workflow(workflow_state.active_workflow)
            if workflow:
                logger.info(f"Continuing active workflow: {workflow_state.active_workflow}")
                response = workflow.process(message, workflow_state, user_id)
                
                # Store bot response in conversation history
                workflow_state.add_message('assistant', response.message)
                
                # Convert WorkflowResponse to dict
                result = self._convert_response(response, workflow_state, workflow.workflow_name, user_id)
                return result
        
        # Handle button clicks directly without LLM
        if is_button_click or is_external_content_button or is_activity_start_button:
            logger.info(f"[Phase 1] Button click detected: {message}")
            
            # External content buttons (start_content_X) should go to activity workflow
            if is_external_content_button or is_activity_start_button:
                logger.info(f"[Phase 1] Routing external/activity button to activity workflow: {message_lower}")
                activity_workflow = self.registry.get_workflow_for_intent('activity_logging')
                if activity_workflow:
                    # Pass the original message so activity workflow can track it
                    response = activity_workflow.start(message, workflow_state, user_id)
                    workflow_state.add_message('assistant', response.message)
                    result = self._convert_response(response, workflow_state, 'activity_logging', user_id)
                    return result
            
            # Use the normalized message_lower for routing
            # Special handling for log_mood button
            if message_lower == 'log_mood':
                logger.info(f"[Phase 1] Routing log_mood to mood workflow")
                mood_workflow = self.registry.get_workflow_for_intent('mood_logging')
                if mood_workflow:
                    # Pass the normalized button ID so mood workflow knows it's a button click
                    response = mood_workflow.start('Log Mood', workflow_state, user_id)
                    workflow_state.add_message('assistant', response.message)
                    result = self._convert_response(response, workflow_state, 'mood_logging', user_id)
                    return result
            
            # Route other log_* buttons to activity workflow (log_water, log_sleep, etc.)
            activity_workflow = self.registry.get_workflow_for_intent('activity_logging')
            if activity_workflow:
                # Pass the normalized message for proper activity detection
                response = activity_workflow.start(message_lower, workflow_state, user_id)
                
                # Store bot response in conversation history
                workflow_state.add_message('assistant', response.message)
                
                result = self._convert_response(response, workflow_state, 'activity_logging', user_id)
                return result
        
        # Check if message is a mood emoji (direct mood logging)
        from .mood_handler import validate_mood_emoji
        if validate_mood_emoji(message.strip()):
            logger.info(f"[Phase 1] Detected mood emoji: {message}")
            # Start mood workflow directly
            mood_workflow = self.registry.get_workflow_for_intent('mood_logging')
            if mood_workflow:
                response = mood_workflow.start(message, workflow_state, user_id)
                
                # Store bot response in conversation history
                workflow_state.add_message('assistant', response.message)
                
                result = self._convert_response(response, workflow_state, 'mood_logging', user_id)
                return result
        
        # No active workflow - use LLM to detect intent
        logger.info("[Phase 1] No active workflow - detecting intent via LLM")
        
        intent_result = self._detect_intent(message, workflow_state, user_id)
        primary_intent = intent_result.get('primary_intent')
        secondary_intent = intent_result.get('secondary_intent')
        
        logger.info(f"[Phase 1] Detected intent: primary={primary_intent}, secondary={secondary_intent}")
        
        # Get workflow for primary intent
        selected_workflow = self.registry.get_workflow_for_intent(primary_intent)
        
        if not selected_workflow:
            logger.warning(f"No workflow found for intent: {primary_intent}")
            # Fallback to general chat
            selected_workflow = self.registry.get_workflow_for_intent('general_chat')
            
            if not selected_workflow:
                return {
                    'message': "I'm here to help! You can log your mood or activities anytime.",
                    'ui_elements': [],
                    'completed': True,
                    'state': 'idle'
                }
        
        logger.info(f"[Phase 1] Selected workflow: {selected_workflow.workflow_name}")
        
        # Store intent entities in workflow state for workflow to use
        if 'entities' in intent_result:
            workflow_state.set_workflow_data('intent_entities', intent_result['entities'])
            logger.info(f"Stored intent entities: {intent_result['entities']}")
        
        # Check for multi-intent
        if self.enable_multi_intent and secondary_intent and secondary_intent != 'none':
            return self._handle_multi_intent_message(
                message, workflow_state, user_id,
                primary_intent, secondary_intent
            )
        
        # Single intent - execute workflow
        response = selected_workflow.start(message, workflow_state, user_id)
        
        # Validate response
        if self.enable_validation:
            validate_response(response, selected_workflow.workflow_name, strict=False)
        
        # Convert to dict
        result = self._convert_response(response, workflow_state, selected_workflow.workflow_name, user_id)
        
        return result
    
    def _detect_intent(self, message: str, workflow_state, user_id: str) -> dict:
        """
        Detect user intent using LLM with conversation context
        
        Returns:
            {
                'primary_intent': str,
                'secondary_intent': str,
                'confidence': float
            }
        """
        try:
            from chat_assistant.domain.llm.intent_extractor import get_intent_extractor
            
            extractor = get_intent_extractor()
            
            # Pass conversation history for better context understanding
            context = {
                'active_workflow': workflow_state.active_workflow,
                'state': workflow_state.state.value,
                'conversation_history': workflow_state.conversation_history  # Add conversation history
            }
            
            intent_result = extractor.extract_intent(message, context=context)
            
            return intent_result
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            # Fallback to general chat
            return {
                'primary_intent': 'general_chat',
                'secondary_intent': 'none',
                'confidence': 0.5
            }
    
    def _is_mood_expression(self, message: str) -> bool:
        """
        Check if message is a mood expression that should trigger mood workflow
        
        Returns True if message contains mood-related keywords or phrases
        """
        message_lower = message.lower().strip()
        
        # Mood keywords - common emotions
        mood_keywords = [
            'stressed', 'anxious', 'worried', 'nervous', 'overwhelmed',
            'happy', 'sad', 'angry', 'frustrated', 'upset', 'down',
            'excited', 'tired', 'exhausted', 'energetic', 'calm',
            'depressed', 'joyful', 'content', 'lonely', 'scared',
            'afraid', 'confident', 'proud', 'ashamed', 'guilty',
            'relieved', 'hopeful', 'hopeless', 'bored', 'motivated',
            'unmotivated', 'inspired', 'discouraged', 'peaceful',
            'restless', 'comfortable', 'uncomfortable'
        ]
        
        # Mood phrases - common expressions
        mood_phrases = [
            'i feel', "i'm feeling", 'i am', "i'm",
            'feeling', 'not feeling', 'been feeling'
        ]
        
        # Check for mood phrases + keywords
        for phrase in mood_phrases:
            if phrase in message_lower:
                for keyword in mood_keywords:
                    if keyword in message_lower:
                        logger.info(f"Detected mood expression: phrase='{phrase}', keyword='{keyword}'")
                        return True
        
        # Check for standalone mood keywords (like "stressed", "anxious")
        # Only if message is short (likely a direct mood statement)
        # Exclude button click patterns like "start_content_4", "log_water", etc.
        if len(message_lower.split()) <= 3 and not any(pattern in message_lower for pattern in [
            'start_', 'log_', 'content_', '_module', 'button'
        ]):
            for keyword in mood_keywords:
                if keyword in message_lower:
                    logger.info(f"Detected standalone mood keyword: '{keyword}'")
                    return True
        
        return False
    
    def _is_new_intent(self, message: str, workflow_state) -> bool:
        """
        Check if message is clearly a new intent (not a response to current workflow)
        
        Returns True if message contains keywords that indicate a new workflow should start
        """
        message_lower = message.lower()
        
        # Keywords that indicate new intents
        new_intent_keywords = [
            'i drank', 'i drink', 'drank', 'logged',
            'show my challenges', 'my challenges', 'challenges',
            'i exercised', 'i slept', 'i weigh',
            'log water', 'log sleep', 'log exercise', 'log weight'
        ]
        
        for keyword in new_intent_keywords:
            if keyword in message_lower:
                logger.info(f"Detected new intent keyword: '{keyword}' in message")
                return True
        
        return False
    
    def _handle_multi_intent_message(self, message: str, workflow_state, user_id: str,
                                     primary_intent: str, secondary_intent: str) -> dict:
        """
        Handle message with multiple intents by processing them sequentially
        
        Strategy:
        1. Execute primary workflow
        2. If it completes immediately, execute secondary
        3. If primary needs input, defer secondary
        4. Merge responses if both complete
        """
        logger.info(f"[Phase 1] Handling multi-intent: {primary_intent} + {secondary_intent}")
        
        # Get both workflows
        primary_workflow = self.registry.get_workflow_for_intent(primary_intent)
        secondary_workflow = self.registry.get_workflow_for_intent(secondary_intent)
        
        if not primary_workflow:
            logger.warning(f"Primary workflow not found for intent: {primary_intent}")
            return {
                'message': "I'm not sure how to help with that.",
                'ui_elements': [],
                'completed': True,
                'state': 'idle'
            }
        
        # Execute primary workflow
        primary_response = primary_workflow.start(message, workflow_state, user_id)
        primary_result = self._convert_response(primary_response, workflow_state, primary_workflow.workflow_name, user_id)
        
        # If primary doesn't complete, return it (can't do secondary yet)
        if not primary_response.completed:
            logger.info("Primary workflow needs input, deferring secondary")
            return primary_result
        
        # Primary completed - try secondary if available
        if not secondary_workflow:
            logger.info("No secondary workflow found")
            return primary_result
        
        # Reset state for secondary
        workflow_state.complete_workflow()
        
        # Execute secondary workflow
        secondary_response = secondary_workflow.start(message, workflow_state, user_id)
        secondary_result = self._convert_response(secondary_response, workflow_state, secondary_workflow.workflow_name, user_id)
        
        # Merge responses
        if not secondary_response.completed:
            # Secondary needs input - prepend primary confirmation
            secondary_result['message'] = f"{primary_result['message']} {secondary_result['message']}"
            return secondary_result
        else:
            # Both completed - merge
            primary_result['message'] = f"{primary_result['message']} {secondary_result['message']}"
            workflow_state.complete_workflow()
            return primary_result
    
    def _convert_response(self, response, workflow_state, workflow_name: str, user_id: str = None) -> dict:
        """
        Convert WorkflowResponse to dict and publish events (Phase 2)
        
        Args:
            response: WorkflowResponse from workflow
            workflow_state: Current workflow state
            workflow_name: Name of the workflow
            user_id: User ID for event publishing
        """
        result = {
            'message': response.message,
            'ui_elements': response.ui_elements,
            'completed': response.completed,
            'state': response.next_state.value if response.next_state else 'idle'
        }
        result.update(response.extra_data)
        
        logger.info(f"Workflow {workflow_name} - completed: {response.completed}, state: {result['state']}")
        
        # Phase 2: Publish events if workflow completed
        if response.completed and self.enable_events and response.events:
            logger.info(f"[Phase 2] Publishing {len(response.events)} events")
            for event in response.events:
                self._publish_event(event, user_id or 'unknown')
        
        if response.completed:
            workflow_state.complete_workflow()
            logger.info(f"Workflow {workflow_name} completed and state reset")
        
        return result
    
    def _publish_event(self, event: dict, user_id: str):
        """
        Publish event to event system (Phase 2)
        
        Args:
            event: Event dictionary with 'type' and other data
            user_id: User ID
        """
        try:
            from app.services.event_publisher import get_event_publisher
            from app.services.behavior_scorer import get_behavior_scorer
            
            publisher = get_event_publisher()
            event_type = event.get('type')
            
            logger.info(f"[Phase 2] Publishing event: {event_type} for user {user_id}")
            
            # Publish to event store
            if event_type == 'mood_logged':
                publisher.publish_mood_logged(
                    user_id=user_id,
                    mood_emoji=event.get('mood'),
                    reason=event.get('reason'),
                    mood_value=event.get('mood_value')
                )
                
                # Update behavior metrics
                try:
                    scorer = get_behavior_scorer()
                    scorer.update_mood_metrics(user_id, event)
                    logger.info(f"[Phase 2] Updated behavior metrics for mood")
                except Exception as e:
                    logger.warning(f"Failed to update behavior metrics: {e}")
                
            elif event_type == 'activity_logged':
                publisher.publish_activity_logged(
                    user_id=user_id,
                    activity_type=event.get('activity_type'),
                    value=event.get('value'),
                    unit=event.get('unit')
                )
                
                # Update behavior metrics
                try:
                    scorer = get_behavior_scorer()
                    scorer.update_activity_metrics(user_id, event)
                    logger.info(f"[Phase 2] Updated behavior metrics for activity")
                except Exception as e:
                    logger.warning(f"Failed to update behavior metrics: {e}")
                
                # Update challenge progress
                try:
                    from app.services.challenge_service import ChallengeService
                    challenge_service = ChallengeService()
                    challenge_service.update_progress_from_event(user_id, event)
                    logger.info(f"[Phase 2] Updated challenge progress")
                except Exception as e:
                    logger.warning(f"Failed to update challenge progress: {e}")
                
            elif event_type == 'suggestion_shown':
                publisher.publish_suggestion_shown(
                    user_id=user_id,
                    suggestion_key=event.get('suggestion_key'),
                    mood_emoji=event.get('mood'),
                    reason=event.get('reason')
                )
                
            elif event_type == 'suggestion_accepted':
                publisher.publish_suggestion_accepted(
                    user_id=user_id,
                    suggestion_key=event.get('suggestion_key')
                )
            
            logger.info(f"[Phase 2] Event {event_type} published successfully")
            
        except Exception as e:
            logger.error(f"[Phase 2] Failed to publish event {event.get('type')}: {e}")
            # Don't fail the workflow if event publishing fails
            import traceback
            traceback.print_exc()
    
    def init_conversation(self, user_id: str) -> dict:
        """
        Initialize conversation with smart UI based on mood status.
        - If mood NOT logged today: Show MOOD SELECTOR + activity buttons (without Log Mood)
        - If mood logged today: Show activity buttons (with Log Mood)
        """
        from .mood_handler import has_logged_mood_today
        from .unified_state import get_workflow_state
        
        # Reset workflow state on init
        workflow_state = get_workflow_state(user_id)
        workflow_state.complete_workflow()
        logger.info(f"Init conversation - reset workflow state for user {user_id}")
        
        # Check if user has logged mood today
        mood_logged_today = has_logged_mood_today(user_id)
        
        if not mood_logged_today:
            # Mood NOT logged - show MOOD SELECTOR + activity buttons (WITHOUT Log Mood)
            return {
                'message': "Welcome! How are you feeling today? 😊",
                'ui_elements': ['emoji_selector', 'activity_buttons'],
                'activity_options': [
                    {'id': 'log_water', 'label': '💧 Log Water'},
                    {'id': 'log_sleep', 'label': '😴 Log Sleep'},
                    {'id': 'log_exercise', 'label': '🏃 Log Exercise'},
                    {'id': 'log_weight', 'label': '⚖️ Log Weight'}
                    # NO Log Mood button - mood selector is shown above
                ],
                'persistent_buttons': False,
                'completed': False,
                'state': 'idle'
            }
        else:
            # Mood already logged - show activity buttons (WITH Log Mood)
            return {
                'message': "Welcome back! What would you like to track? 🌟",
                'ui_elements': ['activity_buttons'],
                'activity_options': [
                    {'id': 'log_water', 'label': '💧 Log Water'},
                    {'id': 'log_sleep', 'label': '😴 Log Sleep'},
                    {'id': 'log_exercise', 'label': '🏃 Log Exercise'},
                    {'id': 'log_weight', 'label': '⚖️ Log Weight'},
                    {'id': 'log_mood', 'label': '😊 Log Mood'}
                    # Log Mood button available - can log mood again
                ],
                'persistent_buttons': False,
                'completed': True,
                'state': 'idle'
            }


# Global instance
_engine = None

def get_chat_engine() -> ChatEngineWorkflow:
    """Get or create the global chat engine instance"""
    global _engine
    if _engine is None:
        _engine = ChatEngineWorkflow()
    return _engine


def process_message(user_id: str, message: str) -> dict:
    """Convenience function for processing messages"""
    engine = get_chat_engine()
    return engine.process_message(user_id, message)


def init_conversation(user_id: str) -> dict:
    """Convenience function for initializing conversation"""
    engine = get_chat_engine()
    return engine.init_conversation(user_id)
