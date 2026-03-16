# activity_workflow.py
# Activity logging workflow (water, sleep, exercise, weight)
# Phase 2: Integrated with EventPublisher for analytics

from typing import Optional
from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .activity_intent_detector import ActivityIntentDetector
from .activity_validator import ActivityValidator
from .health_activity_logger import HealthActivityLogger
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging with more specific format for activity tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    force=True  # Override any existing configuration
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level is enabled

class ActivityWorkflow(BaseWorkflow):
    """
    Activity logging workflow for water, sleep, exercise, weight - Phase 1 Refactored
    
    Flow:
    1. Detect activity type and extract quantity
    2. If quantity missing → ask for clarification
    3. Save to database
    4. Confirm briefly
    5. Complete
    
    Phase 1: No longer uses can_handle() - intent detection via LLM
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="activity_logging",
            handled_intents=['activity_logging','activity', 'log_water', 'log_sleep', 'log_weight', 'log_meal', 'log_steps', 'log_calories']
        )
        self.intent_detector = ActivityIntentDetector()
        self.activity_logger = HealthActivityLogger()
        self.validator = ActivityValidator()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start activity logging workflow"""
        logger.info(f"🔵 [ACTIVITY WORKFLOW START] User: {user_id}, Message: '{message}', Message type: {type(message)}, Length: {len(message)}")
        logger.info(f"🔍 [DEBUG] message.lower(): '{message.lower()}', startswith('log_'): {message.lower().startswith('log_')}")
        
        # CRITICAL FIX: If this is a button click and workflow is already active, reset it first
        if message.lower().startswith('log_') and state.active_workflow == self.workflow_name:
            logger.info(f"🔄 [WORKFLOW RESET] Resetting active workflow to handle new button click")
            state.complete_workflow()
        
        # Check if this is an external content or activity start button (start_content_X, start_meditation, etc.)
        if message.lower().startswith('start_'):
            # IMPORTANT: If there's an active workflow (like activity_query showing suggestions),
            # complete it first to avoid context confusion
            if state.active_workflow and state.active_workflow != self.workflow_name:
                logger.info(f"[External Activity] Completing active workflow '{state.active_workflow}' before starting external activity")
                state.complete_workflow()
            
            return self._handle_external_activity_button(message, state, user_id)
        
        # Check if this is a button click (log_water, log_sleep, etc.)
        if message.lower().startswith('log_'):
            logger.info(f"🔘 [BUTTON CLICK] Detected button: '{message}'")
            return self._handle_button_click(message, state, user_id)
        
        # Detect activities from message
        activities = self.intent_detector.detect_all_activities(message)
        
        logger.info(f"🔍 [ACTIVITY DETECTION] Detected {len(activities)} activities: {activities}")
        
        if not activities:
            # Try to detect activity type even without quantity
            activity_type = self.activity_logger.normalize_activity_type(message)
            
            if activity_type:
                # Found activity type but no quantity
                unit = self.activity_logger.ACTIVITY_TYPES[activity_type]['unit']
                
                state.start_workflow(self.workflow_name, {
                    'activity_type': activity_type,
                    'unit': unit,
                    'notes': message
                })
                
                return self._ask_clarification(
                    message=self._get_clarification_message(activity_type),
                    ui_elements=['text_input']
                )
            
            # No activity detected at all
            return self._complete_workflow(
                message="I can help log activities like water, sleep, exercise, or weight."
            )
        
        # Process first activity (sequential, not parallel)
        activity = activities[0]
        
        # CRITICAL FIX: Handle missing value clarification
        if activity.get('needs_value_clarification'):
            # Activity detected but value missing - ask for value
            state.start_workflow(self.workflow_name, {
                'activity_type': activity['activity_type'],
                'unit': activity['unit'],
                'awaiting_value_clarification': True,
                'notes': activity['notes']
            })
            
            return self._ask_value_clarification(activity['activity_type'])
        
        # CRITICAL FIX: Handle missing unit clarification
        if activity.get('needs_unit_clarification'):
            # Activity detected but unit missing - ask for unit
            state.start_workflow(self.workflow_name, {
                'activity_type': activity['activity_type'],
                'pending_value': activity['value'],
                'awaiting_unit_clarification': True,
                'notes': activity['notes']
            })
            
            return self._ask_unit_clarification(activity['activity_type'], activity['value'])
        
        # Check for duplicate sleep logging
        if activity['activity_type'] == 'sleep':
            # Determine target date (same logic as in health_activity_logger)
            from datetime import datetime, timedelta
            now = datetime.now()
            is_nighttime_sleep = activity['value'] >= 5
            is_morning = now.hour < 12
            is_early_afternoon = 12 <= now.hour < 15
            
            if is_morning or (is_early_afternoon and is_nighttime_sleep):
                target_date = (now - timedelta(days=1)).date()
            else:
                target_date = now.date()
            
            # Check if already logged
            existing_sleep = self.activity_logger.check_recent_sleep(user_id, target_date)
            if existing_sleep:
                # Check if the new value is the same as existing
                if abs(float(existing_sleep['value']) - float(activity['value'])) < 0.1:
                    # Same value - just acknowledge
                    # Check if user has logged mood today
                    from .mood_handler import has_logged_mood_today
                    
                    if has_logged_mood_today(user_id):
                        # Mood already logged - show activity options
                        return self._complete_workflow(
                            message=f"You've already logged {existing_sleep['value']} {existing_sleep['unit']} of sleep for that night. Keep it up! 💪",
                            ui_elements=[]  # No buttons - keep chat clean
                        )
                    else:
                        # Mood not logged - ask for mood
                        return self._complete_workflow(
                            message=f"You've already logged {existing_sleep['value']} {existing_sleep['unit']} of sleep for that night. Keep it up! 💪\n\nHow are you feeling today?",
                            ui_elements=['emoji_selector']
                        )
                else:
                    # Different value - ask if they want to update
                    state.start_workflow(self.workflow_name, {
                        'activity_type': 'sleep',
                        'unit': activity['unit'],
                        'new_value': activity['value'],
                        'previous_value': existing_sleep['value'],
                        'awaiting_duplicate_confirmation': True,
                        'notes': activity.get('notes', '')
                    })
                    
                    return self._ask_clarification(
                        message=f"You already logged {existing_sleep['value']} {existing_sleep['unit']} of sleep for that night. Would you like to update it to {activity['value']} {activity['unit']}?",
                        ui_elements=['text_input']
                    )
        
        # Have all info - validate first, then log immediately
        validation_result = self.validator.validate_activity_input(activity['activity_type'], activity['value'], user_id)
        
        if not validation_result['valid']:
            # Invalid input - ask for clarification
            state.start_workflow(self.workflow_name, {
                'activity_type': activity['activity_type'],
                'unit': activity['unit'],
                'notes': activity.get('notes', '')
            })
            
            return self._ask_clarification(
                message=validation_result['message'],
                ui_elements=['text_input']
            )
        
        if validation_result.get('needs_confirmation'):
            # Unusual value - ask for confirmation
            state.start_workflow(self.workflow_name, {
                'activity_type': activity['activity_type'],
                'unit': activity['unit'],
                'pending_value': activity['value'],
                'awaiting_validation_confirmation': True,
                'notes': activity.get('notes', '')
            })
            
            return self._ask_confirmation(
                message=validation_result['message'],
                ui_elements=['yes_no_buttons']
            )
        
        # Validation passed - log immediately
        try:
            self.activity_logger.log_activity(
                user_id=user_id,
                activity_type=activity['activity_type'],
                value=activity['value'],
                unit=activity['unit'],
                notes=activity['notes']
            )
            
            logger.info(f"✅ [ACTIVITY LOGGED] Type: {activity['activity_type']}, Value: {activity['value']} {activity['unit']}, User: {user_id}")
            
            # Update session summary
            self._update_session_summary(state, activity['activity_type'], activity.get('unit'))
            
            # Phase 2: Emit event after successful save
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                publisher.publish_activity_logged(
                    user_id=str(user_id),
                    activity_type=activity['activity_type'],
                    value=activity['value'],
                    unit=activity['unit']
                )
                logger.info(f"📊 Published activity_logged event for user {user_id}")
                
                # Update behavior metrics
                from app.services.behavior_metrics_updater import get_metrics_updater
                updater = get_metrics_updater()
                updater.update_metrics(str(user_id))
                logger.info(f"📊 Updated behavior metrics for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to publish event or update metrics: {e}")
            
            # Keep workflow active for potential follow-ups (e.g., "log more water")
            state.set_workflow_data('last_logged_activity', activity['activity_type'])
            state.set_workflow_data('last_logged_unit', activity['unit'])
            state.set_workflow_data('awaiting_followup', True)
            
            return WorkflowResponse(
                message=self._create_activity_response({
                    'activity_type': activity['activity_type'],
                    'value': activity['value'],
                    'unit': activity['unit'],
                    'user_id': user_id
                }),
                ui_elements=[],  # No buttons - keep chat clean
                completed=False,  # Keep workflow active!
                next_state=ConversationState.WORKFLOW_ACTIVE,
                events=[{'type': 'activity_logged', 'activity_type': activity['activity_type'], 'value': activity['value'], 'unit': activity['unit']}]
            )
        
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return self._complete_workflow(
                message="Sorry, I couldn't log that activity."
            )
    

    def _handle_external_activity_button(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """
        Handle external activity buttons like start_content_4, start_meditation, etc.
        
        These buttons open external content (YouTube, blogs, etc.) in a new tab.
        The workflow should:
        1. Silently track that user started the activity
        2. Mark workflow as WAITING for user to return
        3. Frontend will detect tab return and trigger follow-up
        """
        logger.info(f"[External Activity] User clicked: {message}")
        
        # Extract activity info from message
        # Format: "start_content_4" or "start_meditation_module"
        activity_id = message.lower().strip()
        
        # Store pending activity in workflow state
        state.start_workflow(self.workflow_name, {
            'pending_external_activity': activity_id,
            'awaiting_return': True,
            'activity_started_at': str(__import__('datetime').datetime.now())
        })
        
        # Return empty message - no response needed when starting activity
        # User is immediately redirected to external content
        return WorkflowResponse(
            message="",  # No message - silent tracking
            ui_elements=[],
            completed=False,  # Keep workflow active!
            next_state=ConversationState.CLARIFICATION_PENDING
        )
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Process message in active activity workflow"""
        
        # NEW: Handle value clarification
        awaiting_value_clarification = state.get_workflow_data('awaiting_value_clarification', False)
        
        if awaiting_value_clarification:
            # User is providing value information
            activity_type = state.get_workflow_data('activity_type')
            unit = state.get_workflow_data('unit')
            notes = state.get_workflow_data('notes', '')
            
            # Extract value from user's response
            value = self.intent_detector.extract_number(message)
            
            if value is None:
                # Still no value detected - ask again
                return self._ask_value_clarification(activity_type)
            
            # Clear value clarification state
            state.set_workflow_data('awaiting_value_clarification', False)
            
            # Validate the input
            validation_result = self.validator.validate_activity_input(activity_type, value, user_id)
            
            if not validation_result['valid']:
                return self._ask_clarification(
                    message=validation_result['message'],
                    ui_elements=['text_input']
                )
            
            if validation_result.get('needs_confirmation'):
                state.set_workflow_data('pending_value', value)
                state.set_workflow_data('awaiting_validation_confirmation', True)
                
                return self._ask_confirmation(
                    message=validation_result['message'],
                    ui_elements=['yes_no_buttons']
                )
            
            # Log the activity with provided value
            try:
                self.activity_logger.log_activity(
                    user_id=user_id,
                    activity_type=activity_type,
                    value=value,
                    unit=unit,
                    notes=f"{notes} (Value: {message})"
                )
                
                logger.info(f"✅ [ACTIVITY LOGGED] Type: {activity_type} (with value clarification), Value: {value} {unit}, User: {user_id}")
                
                # Update session summary
                self._update_session_summary(state, activity_type, unit)
                
                # Phase 2: Emit event after successful save
                try:
                    from app.services.event_publisher import get_event_publisher
                    publisher = get_event_publisher()
                    publisher.publish_activity_logged(
                        user_id=str(user_id),
                        activity_type=activity_type,
                        value=value,
                        unit=unit
                    )
                    logger.info(f"📊 Published activity_logged event for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish event: {e}")
                
                return self._complete_workflow(
                    message=self._create_activity_response({
                        'activity_type': activity_type,
                        'value': value,
                        'unit': unit,
                        'user_id': user_id
                    }),
                    ui_elements=[]
                )
                
            except Exception as e:
                logger.error(f"Failed to log activity after value clarification: {e}")
                return self._complete_workflow(
                    message="Sorry, I couldn't log that activity."
                )
        
        # NEW: Handle unit clarification
        awaiting_unit_clarification = state.get_workflow_data('awaiting_unit_clarification', False)
        
        if awaiting_unit_clarification:
            # User is providing unit information
            activity_type = state.get_workflow_data('activity_type')
            pending_value = state.get_workflow_data('pending_value')
            notes = state.get_workflow_data('notes', '')
            
            # Extract unit from user's response
            detected_unit = self.intent_detector.extract_unit(message)
            
            if detected_unit is None:
                # Still no unit detected - ask again with examples
                return self._ask_unit_clarification(activity_type, pending_value, show_examples=True)
            
            # Validate that the unit is appropriate for this activity
            if not self.intent_detector.unit_converter.is_valid_unit(activity_type, detected_unit):
                valid_units = self.intent_detector.unit_converter.get_supported_units(activity_type)
                return self._ask_clarification(
                    message=f"'{detected_unit}' is not a valid unit for {activity_type}. Please use one of: {', '.join(valid_units)}",
                    ui_elements=['text_input']
                )
            
            # Convert to standard unit
            converted_value, standard_unit = self.intent_detector.unit_converter.convert_to_standard_unit(
                activity_type, pending_value, detected_unit
            )
            
            # Create conversion message
            conversion_msg = self.intent_detector.unit_converter.format_conversion_message(
                pending_value, detected_unit, converted_value, standard_unit
            )
            
            updated_notes = f"{notes} {conversion_msg}" if conversion_msg else notes
            
            # Clear unit clarification state
            state.set_workflow_data('awaiting_unit_clarification', False)
            
            # Log the activity with converted values
            try:
                self.activity_logger.log_activity(
                    user_id=user_id,
                    activity_type=activity_type,
                    value=converted_value,
                    unit=standard_unit,
                    notes=updated_notes
                )
                
                logger.info(f"✅ [ACTIVITY LOGGED] Type: {activity_type} (with unit clarification), Value: {converted_value} {standard_unit}, User: {user_id}")
                
                # Update session summary
                self._update_session_summary(state, activity_type, standard_unit)
                
                return self._complete_workflow(
                    message=self._create_friendly_response(activity_type, converted_value, standard_unit, conversion_msg),
                    ui_elements=[]
                )
                
            except Exception as e:
                logger.error(f"Failed to log activity after unit clarification: {e}")
                return self._complete_workflow(
                    message="Sorry, I couldn't log that activity."
                )
        
        # NEW: Handle follow-up requests after successful logging
        awaiting_followup = state.get_workflow_data('awaiting_followup', False)
        
        if awaiting_followup:
            last_activity = state.get_workflow_data('last_logged_activity')
            last_unit = state.get_workflow_data('last_logged_unit')
            
            # Check if user wants to log more of the same activity
            message_lower = message.lower().strip()
            
            # SPECIAL CASE FOR SLEEP: "add X more hours" should be treated as an update, not new entry
            if last_activity == 'sleep' and any(phrase in message_lower for phrase in ['add', 'more']):
                # For sleep, "add more" usually means updating the existing entry
                # Extract the additional amount they want to add
                additional_value = self.intent_detector.extract_number(message)
                
                if additional_value is not None:
                    # They want to add X more hours to their existing sleep
                    # This should trigger duplicate detection logic, not new entry logic
                    logger.info(f"User wants to add {additional_value} more hours to existing sleep")
                    
                    # Get the existing sleep value from today
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    is_morning = now.hour < 12
                    is_early_afternoon = 12 <= now.hour < 15
                    
                    if is_morning or is_early_afternoon:
                        target_date = (now - timedelta(days=1)).date()
                    else:
                        target_date = now.date()
                    
                    existing_sleep = self.activity_logger.check_recent_sleep(user_id, target_date)
                    if existing_sleep:
                        # Calculate the new total (existing + additional)
                        new_total = float(existing_sleep['value']) + additional_value
                        
                        # Set up duplicate confirmation state
                        state.set_workflow_data('awaiting_followup', False)
                        state.set_workflow_data('activity_type', 'sleep')
                        state.set_workflow_data('unit', 'hours')
                        state.set_workflow_data('new_value', new_total)
                        state.set_workflow_data('previous_value', existing_sleep['value'])
                        state.set_workflow_data('awaiting_duplicate_confirmation', True)
                        state.set_workflow_data('notes', f'Update: {message}')
                        
                        return self._ask_clarification(
                            message=f"You already logged {existing_sleep['value']} hours of sleep for that night. Would you like to update it to {new_total} hours?",
                            ui_elements=['text_input']
                        )
                    else:
                        # No existing sleep found - but user said "add more", so ask for clarification
                        logger.info("No existing sleep found, but user said 'add more' - asking for clarification")
                        state.set_workflow_data('awaiting_followup', False)
                        state.set_workflow_data('activity_type', 'sleep')
                        state.set_workflow_data('unit', 'hours')
                        state.set_workflow_data('notes', f'Follow-up: {message}')
                        
                        return self._ask_clarification(
                            message=f"I don't see any sleep logged yet today. Do you want to log {additional_value} hours of sleep?",
                            ui_elements=['text_input']
                        )
                else:
                    # No number detected in "add more" - ask for clarification
                    state.set_workflow_data('awaiting_followup', False)
                    state.set_workflow_data('activity_type', last_activity)
                    state.set_workflow_data('unit', last_unit)
                    state.set_workflow_data('notes', f'Follow-up: {message}')
                    
                    return self._ask_clarification(
                        message=self._get_clarification_message(last_activity),
                        ui_elements=['text_input']
                    )
            
            if any(phrase in message_lower for phrase in ['log more', 'more', 'add more', 'another', 'again']):
                # User wants to log more of the same activity (for non-sleep or when no existing entry)
                logger.info(f"User wants to log more {last_activity}")
                
                # Clear follow-up state and restart the same activity workflow
                state.set_workflow_data('awaiting_followup', False)
                state.set_workflow_data('activity_type', last_activity)
                state.set_workflow_data('unit', last_unit)
                state.set_workflow_data('notes', f'Follow-up: {message}')
                
                return self._ask_clarification(
                    message=self._get_clarification_message(last_activity),
                    ui_elements=['text_input']
                )
            
            elif any(phrase in message_lower for phrase in ['no', 'done', 'finished', 'that\'s all', 'enough']):
                # User is done logging
                logger.info(f"User finished logging {last_activity}")
                return self._complete_workflow(
                    message="Great! Keep up the good work! 💪"
                )
            
            else:
                # User said something else - try to detect if it's a quantity for the same activity
                value = self.intent_detector.extract_number(message)
                
                if value is not None:
                    # User provided a number - assume they want to log more of the same activity
                    logger.info(f"User provided quantity {value} for follow-up {last_activity}")
                    
                    # Validate the input
                    validation_result = self.validator.validate_activity_input(last_activity, value, user_id)
                    
                    if not validation_result['valid']:
                        return self._ask_clarification(
                            message=validation_result['message'],
                            ui_elements=['text_input']
                        )
                    
                    if validation_result.get('needs_confirmation'):
                        state.set_workflow_data('pending_value', value)
                        state.set_workflow_data('awaiting_validation_confirmation', True)
                        state.set_workflow_data('awaiting_followup', False)
                        
                        return self._ask_confirmation(
                            message=validation_result['message'],
                            ui_elements=['yes_no_buttons']
                        )
                    
                    # Valid input - log it
                    try:
                        self.activity_logger.log_activity(
                            user_id=user_id,
                            activity_type=last_activity,
                            value=value,
                            unit=last_unit,
                            notes=f"Follow-up: {message}"
                        )
                        
                        logger.info(f"✅ [ACTIVITY LOGGED] Type: {last_activity} (follow-up), Value: {value} {last_unit}, User: {user_id}")
                        
                        # Keep workflow active for more follow-ups
                        return WorkflowResponse(
                            message=self._create_activity_response({
                                'activity_type': last_activity,
                                'value': value,
                                'unit': last_unit,
                                'user_id': user_id
                            }),
                            ui_elements=[],
                            completed=False,  # Keep active for more follow-ups
                            next_state=ConversationState.WORKFLOW_ACTIVE
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to log follow-up activity: {e}")
                        return self._complete_workflow(
                            message="Sorry, I couldn't log that activity."
                        )
                
                else:
                    # No number detected - complete workflow and let other workflows handle it
                    logger.info(f"No follow-up detected, completing workflow")
                    state.complete_workflow()
                    
                    # Let the message be processed by other workflows
                    # from .chat_engine_workflow import ChatEngineWorkflow
                    # chat_engine = ChatEngineWorkflow()
                    # return chat_engine.start(message, state, user_id)/
                    return WorkflowResponse(
                        message="Got it. Let me know if you'd like to track anything else.",
                        ui_elements=[],
                        completed=True
                    )
        
        # Check if we're waiting for user to return from external activity
        awaiting_return = state.get_workflow_data('awaiting_return', False)
        pending_activity = state.get_workflow_data('pending_external_activity')
        
        if awaiting_return and pending_activity:
            logger.info(f"[External Activity] User returned from: {pending_activity}")
            
            # Check if this is the automatic return message from frontend
            if message.lower().startswith('returned_from_'):
                # Automatic return detection - ask for feedback with buttons
                state.set_workflow_data('awaiting_return', False)
                state.set_workflow_data('awaiting_feedback', True)
                
                return WorkflowResponse(
                    message="Welcome back! How did that go? 😊",
                    ui_elements=['action_buttons_multiple'],
                    completed=False,
                    next_state=ConversationState.ACTION_CONFIRMATION_PENDING,
                    extra_data={
                        'actions': [
                            {'id': 'helpful', 'name': '👍 Helpful'},
                            {'id': 'not_helpful', 'name': '👎 Not helpful'},
                            {'id': 'skip_feedback', 'name': 'Skip'}
                        ]
                    }
                )
            else:
                # User typed something - they're providing feedback already
                # Complete the workflow with acknowledgment
                state.set_workflow_data('awaiting_return', False)
                state.set_workflow_data('pending_external_activity', None)
                
                return self._complete_workflow(
                    message=f"Thanks for sharing! I'm glad you tried it. 💪",
                    ui_elements=[]
                )
        
        # Check if we're awaiting feedback after external activity
        awaiting_feedback = state.get_workflow_data('awaiting_feedback', False)
        
        if awaiting_feedback:
            logger.info(f"[External Activity] User provided feedback: {message}")
            
            # Clear feedback state
            state.set_workflow_data('awaiting_feedback', False)
            state.set_workflow_data('pending_external_activity', None)
            
            # Handle different feedback responses
            message_lower = message.lower().strip()
            
            if message_lower == 'helpful' or '👍' in message:
                response_msg = "That's great to hear! Glad it was helpful. 💪"
            elif message_lower == 'not_helpful' or '👎' in message:
                response_msg = "Thanks for the feedback! We'll keep that in mind. 😊"
            elif message_lower == 'skip_feedback' or message_lower == 'skip':
                response_msg = "No problem! Thanks for trying it out. 🌟"
            else:
                # User typed something instead of clicking button
                response_msg = "Thanks for the feedback! I'm glad you tried it. 💪"
            
            # Complete workflow
            return self._complete_workflow(
                message=response_msg,
                ui_elements=[]
            )
        
        activity_type = state.get_workflow_data('activity_type')
        unit = state.get_workflow_data('unit')
        notes = state.get_workflow_data('notes')
        
        # Check if we're awaiting validation confirmation
        awaiting_validation_confirmation = state.get_workflow_data('awaiting_validation_confirmation', False)
        
        if awaiting_validation_confirmation:
            # User is responding to validation warning (e.g., "15 glasses is quite high, are you sure?")
            message_lower = message.lower().strip()
            
            if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                # User confirmed - proceed with the pending value
                pending_value = state.get_workflow_data('pending_value')
                state.set_workflow_data('awaiting_validation_confirmation', False)
                
                if pending_value:
                    return self._log_activity_with_validation(user_id, activity_type, pending_value, unit, notes, state)
                else:
                    # No pending value - ask again
                    return self._ask_clarification(
                        message=self._get_clarification_message(activity_type),
                        ui_elements=['text_input']
                    )
            else:
                # User declined - ask for a different value
                state.set_workflow_data('awaiting_validation_confirmation', False)
                
                # Provide helpful guidance about typical ranges
                guidance = self.validator.get_typical_range_message(activity_type)
                message = f"No problem! {guidance} Please enter a different amount:"
                
                return self._ask_clarification(
                    message=message,
                    ui_elements=['text_input']
                )
        
        # Check if we're awaiting duplicate confirmation
        awaiting_confirmation = state.get_workflow_data('awaiting_duplicate_confirmation', False)
        
        if awaiting_confirmation:
            # User is responding to "already logged" confirmation
            message_lower = message.lower().strip()
            
            # FIRST: Check if user is providing a new quantity instead of yes/no
            # This handles cases like "I have slept for 5 hours" in response to confirmation
            detected_activities = self.intent_detector.detect_all_activities(message)
            if detected_activities:
                # User provided a new activity value - treat this as an update
                new_activity = detected_activities[0]
                if new_activity['activity_type'] == activity_type:
                    logger.info(f"User provided new {activity_type} value during confirmation: {new_activity['value']}")
                    
                    # Validate the new value
                    validation_result = self.validator.validate_activity_input(activity_type, new_activity['value'], user_id)
                    
                    if not validation_result['valid']:
                        return self._ask_clarification(
                            message=validation_result['message'],
                            ui_elements=['text_input']
                        )
                    
                    if validation_result.get('needs_confirmation'):
                        # New value also needs confirmation - update pending value and ask again
                        state.set_workflow_data('new_value', new_activity['value'])
                        state.set_workflow_data('pending_value', new_activity['value'])
                        state.set_workflow_data('awaiting_validation_confirmation', True)
                        state.set_workflow_data('awaiting_duplicate_confirmation', False)
                        
                        return self._ask_confirmation(
                            message=validation_result['message'],
                            ui_elements=['yes_no_buttons']
                        )
                    
                    # Valid new value - log it directly
                    try:
                        self.activity_logger.log_activity(
                            user_id=user_id,
                            activity_type=activity_type,
                            value=new_activity['value'],
                            unit=new_activity['unit'],
                            notes=new_activity.get('notes', '')
                        )
                        
                        logger.info(f"Updated {activity_type}: {new_activity['value']} {new_activity['unit']}")
                        
                        # Update session summary
                        self._update_session_summary(state, activity_type, new_activity['unit'])
                        
                        return self._complete_workflow(
                            message=f"Got it! Updated your {activity_type} to {new_activity['value']} {new_activity['unit']}. 💪",
                            ui_elements=[]
                        )
                    except Exception as e:
                        logger.error(f"Failed to update activity: {e}")
                        return self._complete_workflow(
                            message="Sorry, I couldn't update that activity."
                        )
            
            # SECOND: Check for explicit yes/no responses
            if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                # User wants to update - use the new value they provided earlier
                new_value = state.get_workflow_data('new_value')
                
                if new_value:
                    # Log the new value
                    try:
                        self.activity_logger.log_activity(
                            user_id=user_id,
                            activity_type=activity_type,
                            value=new_value,
                            unit=unit,
                            notes=notes
                        )
                        
                        logger.info(f"Updated {activity_type}: {new_value} {unit}")
                        
                        # Update session summary
                        self._update_session_summary(state, activity_type, unit)
                        
                        return self._complete_workflow(
                            message=f"Got it! Updated your {activity_type} to {new_value} {unit}. 💪",
                            ui_elements=[]  # No buttons - keep chat clean
                        )
                    except Exception as e:
                        logger.error(f"Failed to update activity: {e}")
                        return self._complete_workflow(
                            message="Sorry, I couldn't update that activity."
                        )
                else:
                    # No new value stored - ask for quantity
                    state.set_workflow_data('awaiting_duplicate_confirmation', False)
                    
                    return self._ask_clarification(
                        message=self._get_clarification_message(activity_type),
                        ui_elements=['text_input']
                    )
            else:
                # User doesn't want to log again - acknowledge and move on
                previous_value = state.get_workflow_data('previous_value')
                
                # Check if user has logged mood today
                from .mood_handler import has_logged_mood_today
                
                if has_logged_mood_today(user_id):
                    # Mood already logged - show activity options
                    return self._complete_workflow(
                        message=f"No problem! You've already logged {previous_value} {unit} of {activity_type} today. Keep it up! 💪",
                        ui_elements=[]  # No buttons - keep chat clean
                    )
                else:
                    # Mood not logged - ask for mood
                    return self._complete_workflow(
                        message=f"No problem! You've already logged {previous_value} {unit} of {activity_type} today. Keep it up! 💪\n\nHow are you feeling today?",
                        ui_elements=['emoji_selector']
                    )
        
        # Check if user wants to cancel using LLM with conversation history
        if self._is_cancellation_request(message, state):
            logger.info(f"User cancelled activity logging: {message}")
            return self._complete_workflow(
                message="No problem! Activity logging cancelled. Anything else I can help with?",
                ui_elements=[]  # No buttons - keep chat clean
            )
        
        # Extract quantity from message
        value = self.intent_detector.extract_number(message)
        
        if value is None:
            # Still no quantity - ask again
            return self._ask_clarification(
                message=f"Please enter a number for {activity_type}.",
                ui_elements=['text_input']
            )
        
        # NEW: Validate the input using comprehensive validation system
        validation_result = self.validator.validate_activity_input(activity_type, value, user_id)
        
        if not validation_result['valid']:
            # Invalid input - ask again with helpful guidance
            return self._ask_clarification(
                message=validation_result['message'],
                ui_elements=['text_input']
            )
        
        if validation_result.get('needs_confirmation'):
            # Unusual value - ask for confirmation
            state.set_workflow_data('pending_value', value)
            state.set_workflow_data('awaiting_validation_confirmation', True)
            
            return self._ask_confirmation(
                message=validation_result['message'],
                ui_elements=['yes_no_buttons']
            )
        
        # Valid input - proceed with logging
        return self._log_activity_with_validation(user_id, activity_type, value, unit, notes, state)
    
    def _log_activity_with_validation(self, user_id: int, activity_type: str, value: float, unit: str, notes: str, state) -> WorkflowResponse:
        """Log activity after validation has passed"""
        try:
            self.activity_logger.log_activity(
                user_id=user_id,
                activity_type=activity_type,
                value=value,
                unit=unit,
                notes=f"{notes} - validated"
            )
            
            logger.info(f"✅ [ACTIVITY LOGGED] Type: {activity_type} (validated), Value: {value} {unit}, User: {user_id}")
            
            # Update session summary
            self._update_session_summary(state, activity_type, unit)
            
            # Phase 2: Emit event after successful save
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                publisher.publish_activity_logged(
                    user_id=str(user_id),
                    activity_type=activity_type,
                    value=value,
                    unit=unit
                )
                logger.info(f"📊 Published activity_logged event for user {user_id}")
                
                # Update behavior metrics
                from app.services.behavior_metrics_updater import get_metrics_updater
                updater = get_metrics_updater()
                updater.update_metrics(str(user_id))
                logger.info(f"📊 Updated behavior metrics for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to publish event or update metrics: {e}")
            
            # Keep workflow active for potential follow-ups (e.g., "log more water")
            state.set_workflow_data('last_logged_activity', activity_type)
            state.set_workflow_data('last_logged_unit', unit)
            state.set_workflow_data('awaiting_followup', True)
            
            return WorkflowResponse(
                message=self._create_activity_response({
                    'activity_type': activity_type,
                    'value': value,
                    'unit': unit,
                    'user_id': user_id
                }),
                ui_elements=[],  # No buttons - keep chat clean
                completed=False,  # Keep workflow active!
                next_state=ConversationState.WORKFLOW_ACTIVE,
                events=[{'type': 'activity_logged', 'activity_type': activity_type, 'value': value, 'unit': unit}]
            )
        
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return self._complete_workflow(
                message="Sorry, I couldn't log that activity."
            )
    
    def _get_clarification_message(self, activity_type: str) -> str:
        """Get appropriate clarification message for activity type using LLM"""
        try:
            from .llm_service import get_llm_service
            llm = get_llm_service()
            
            # Get the expected unit for this activity type
            expected_unit = self.activity_logger.ACTIVITY_TYPES.get(activity_type, {}).get('unit', activity_type)
            
            # Create a natural prompt for the LLM with the specific unit
            prompt = f"""Generate a friendly, conversational question asking the user how much {activity_type} they want to log.

Activity type: {activity_type}
Expected unit: {expected_unit}

Requirements:
- Keep it short and friendly (1 sentence)
- Use natural language
- Be encouraging
- Don't use emojis
- MUST use the expected unit: {expected_unit}

Examples:
- For water (glasses): "How many glasses of water did you drink?"
- For sleep (hours): "How many hours did you sleep last night?"
- For exercise (minutes): "How many minutes did you exercise?"
- For weight (kg): "What's your current weight in kg?"

Generate the question using the unit "{expected_unit}":"""
            
            response = llm.call(
                prompt=prompt,
                system_message="You are a friendly wellness assistant helping users log their health activities. Always use the specified unit in your questions.",
                max_tokens=50,
                temperature=0.3
            )
            
            # Extract just the question from the response
            message = response.strip()
            
            # Fallback to simple message if LLM response is too long or weird
            if len(message) > 100 or '\n' in message:
                messages = {
                    'water': "How many glasses of water?",
                    'sleep': "How many hours did you sleep?",
                    'exercise': "How many minutes did you exercise?",
                    'weight': "What is your weight?",
                    'meal': "How many meals?"
                }
                return messages.get(activity_type, f"How much {activity_type}?")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate LLM clarification message: {e}")
            # Fallback to hardcoded messages
            messages = {
                'water': "How many glasses of water?",
                'sleep': "How many hours did you sleep?",
                'exercise': "How many minutes did you exercise?",
                'weight': "What is your weight?",
                'meal': "How many meals?"
            }
            return messages.get(activity_type, f"How much {activity_type}?")
    
    def _get_other_activity_suggestions(self, exclude_activity: str) -> list:
        """Get activity suggestions excluding the one just checked"""
        all_activities = [
            {'id': 'log_water', 'name': '💧 Log Water', 'type': 'water'},
            {'id': 'log_sleep', 'name': '😴 Log Sleep', 'type': 'sleep'},
            {'id': 'log_exercise', 'name': '🏃 Log Exercise', 'type': 'exercise'},
            {'id': 'log_weight', 'name': '⚖️ Update Weight', 'type': 'weight'}
        ]
        
        # Filter out the activity that was just checked
        filtered = [act for act in all_activities if act['type'] != exclude_activity]
        
        # Return only id and name
        return [{'id': act['id'], 'name': act['name']} for act in filtered]
    
    def _handle_button_click(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle button clicks like log_water, log_sleep, etc."""
        logger.info(f"🔘 [BUTTON HANDLER] Processing button: '{message}' for user {user_id}")
        
        # Map button IDs to activity types
        # NOTE: log_exercise is NOT here - it's handled by ActivityLoggingWorkflowWrapper
        button_to_activity = {
            'log_water': 'water',
            'log_sleep': 'sleep',
            'log_weight': 'weight',
            'log_meal': 'meal',
            'log_calories': 'calories',
            'log_steps': 'steps'
        }
        
        button_id = message.lower().strip()
        activity_type = button_to_activity.get(button_id)
        
        logger.info(f"🔘 [BUTTON HANDLER] Button ID: '{button_id}' → Activity Type: '{activity_type}'")
        
        if not activity_type:
            # Unknown button or log_exercise (which should go to exercise_logging workflow)
            if button_id == 'log_exercise':
                logger.info(f"🔘 [BUTTON HANDLER] log_exercise should be handled by exercise_logging workflow, not here")
                return self._complete_workflow(
                    message="Please use the Log Exercise button to start exercise logging."
                )
            
            # Unknown button, treat as regular message
            return self._complete_workflow(
                message="I didn't understand that. Please try again."
            )
        
        # For water, allow multiple logs per day without asking
        # For other activities, check for duplicates
        if activity_type != 'water':
            recent_log = self._check_recent_activity(user_id, activity_type)
            
            if recent_log:
                # User already logged this activity today
                value = recent_log['value']
                unit = recent_log['unit']
                
                # Store in state for confirmation flow
                state.start_workflow(self.workflow_name, {
                    'activity_type': activity_type,
                    'unit': unit,
                    'notes': f'Button: {button_id}',
                    'awaiting_duplicate_confirmation': True,
                    'previous_value': value
                })
                
                return self._ask_confirmation(
                    message=f"I see you already logged {value} {unit} of {activity_type} today. Would you like to log more?",
                    ui_elements=['yes_no_buttons']
                )
        
        # Get unit for this activity type
        unit = self.activity_logger.ACTIVITY_TYPES[activity_type]['unit']
        
        logger.info(f"🔘 [BUTTON HANDLER] Starting workflow for '{activity_type}' with unit '{unit}'")
        
        # Start workflow and ask for quantity
        state.start_workflow(self.workflow_name, {
            'activity_type': activity_type,
            'unit': unit,
            'notes': f'Button: {button_id}'
        })
        
        clarification_msg = self._get_clarification_message(activity_type)
        logger.info(f"❓ [BUTTON HANDLER] Asking for clarification: '{clarification_msg}'")
        
        return self._ask_clarification(
            message=clarification_msg,
            ui_elements=['text_input']
        )
    
    def _check_recent_activity(self, user_id: int, activity_type: str) -> dict:
        """Check if user logged this activity today"""
        try:
            from db import get_connection
            from datetime import datetime
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check for logs from today
            cursor.execute('''
                SELECT value, unit, timestamp
                FROM health_activities
                WHERE user_id = ? AND activity_type = ? AND DATE(timestamp) = DATE('now')
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, activity_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'value': result[0],
                    'unit': result[1],
                    'timestamp': result[2]
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to check recent activity: {e}")
            return None
    
    def _is_cancellation_request(self, message: str, state: WorkflowState) -> bool:
        """
        Check if user wants to cancel using LLM with conversation history and semantic summary.
        
        Uses structured LLM output for reliability.
        
        Examples of cancellation:
        - "don't log"
        - "cancel"
        - "never mind"
        - "I changed my mind"
        - "Actually, I want to log my mood instead" (context switch)
        """
        message_lower = message.lower().strip()
        
        # Quick keyword check first (fast path)
        cancellation_keywords = [
            'cancel', 'stop', 'never mind', 'nevermind', 
            "don't", "dont", 'no thanks', 'not now',
            'changed my mind', 'forget it'
        ]
        
        for keyword in cancellation_keywords:
            if keyword in message_lower:
                logger.info(f"Cancellation keyword detected: '{keyword}'")
                return True
        
        # ENHANCED: Check for explicit context switch patterns
        # These indicate user wants to switch to a different activity
        context_switch_patterns = [
            ('actually', 'instead'),  # "Actually, I want to log my mood instead"
            ('actually', 'rather'),   # "Actually, I'd rather log sleep"
            ('instead', 'log'),       # "Instead, log my mood"
            ('instead', 'track'),     # "Instead, track my sleep"
            ('rather', 'log'),        # "I'd rather log exercise"
            ('rather', 'track'),      # "I'd rather track water"
        ]
        
        # Check if message contains context switch pattern
        for pattern in context_switch_patterns:
            if all(word in message_lower for word in pattern):
                logger.info(f"Context switch pattern detected: {pattern}")
                return True
        
        # Also check for single strong context switch indicators with activity mentions
        strong_switch_words = ['actually', 'instead', 'rather']
        activity_words = ['log', 'track', 'mood', 'water', 'sleep', 'exercise', 'weight']
        
        has_switch_word = any(word in message_lower for word in strong_switch_words)
        has_activity_word = any(word in message_lower for word in activity_words)
        
        if has_switch_word and has_activity_word:
            logger.info(f"Context switch detected: switch word + activity mention")
            return True
        
        # If ambiguous, use LLM with semantic summary + conversation history
        try:
            from .llm_service import get_llm_service
            llm = get_llm_service()
            
            # Check and clear stale summary
            state.session_summary.clear_if_stale()
            
            # Build context: summary FIRST, then buffer
            messages = [
                {"role": "system", "content": """Analyze if the user wants to cancel the current action or switch to a different activity.
Respond in exactly this format:
intent=cancel|continue
confidence=0.85

Examples of CANCEL:
- "cancel"
- "never mind"
- "I changed my mind"
- "Actually, I want to log my mood instead" (switching to different activity)
- "Instead, log sleep" (switching to different activity)
- "I'd rather track water" (switching to different activity)

Examples of CONTINUE:
- "2 glasses" (providing requested value)
- "yes" (confirming)
- "a lot" (attempting to provide value, even if unclear)
"""}
            ]
            
            # Add semantic summary (if exists)
            summary_text = state.session_summary.to_prompt()
            if summary_text:
                messages.append({
                    "role": "system", 
                    "content": f"Context: {summary_text}"
                })
            
            # Add recent conversation (evidence)
            history = state.get_conversation_history(limit=3)
            messages.extend(history)
            
            # Add analysis question
            messages.append({
                "role": "user",
                "content": f"User said: '{message}'"
            })
            
            # LLM interprets (returns structured output)
            response = llm.call(messages=messages, max_tokens=30, temperature=0.1)
            
            # Parse structured output (defensive)
            try:
                lines = response.strip().split('\n')
                intent_line = [l for l in lines if l.startswith('intent=')][0]
                conf_line = [l for l in lines if l.startswith('confidence=')][0]
                
                intent = intent_line.split('=')[1].strip()
                confidence = float(conf_line.split('=')[1].strip())
                
                logger.info(f"LLM cancellation analysis: intent={intent}, confidence={confidence}")
                
                # Workflow decides based on confidence threshold
                is_cancel = confidence > 0.7 and intent == "cancel"
                return is_cancel
                
            except (IndexError, ValueError) as e:
                # Parsing failed - fail safe (treat as continue)
                logger.warning(f"Failed to parse LLM output, treating as continue: {e}")
                logger.warning(f"LLM response was: {response}")
                return False
            
        except Exception as e:
            logger.warning(f"LLM cancellation detection failed: {e}")
            return False

    def _create_activity_response(self, activity: dict) -> str:
        """
        Create friendly, natural activity response message
        
        Args:
            activity: Dict with activity_type, value, unit, user_id (optional)
            
        Returns:
            Natural, friendly confirmation message
        """
        activity_type = activity['activity_type']
        value = activity['value']
        unit = activity['unit']
        user_id = activity.get('user_id')
        
        # Format value nicely (remove .0 for whole numbers)
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        
        # Get today's total for cumulative activities (water, exercise)
        daily_total = None
        if user_id and activity_type in ['water', 'exercise']:
            try:
                today_activities = self.activity_logger.get_today_activities(user_id)
                daily_total = sum(
                    a['value'] for a in today_activities 
                    if a['activity_type'] == activity_type
                )
                
                # Format daily_total nicely too (remove .0 for whole numbers)
                if isinstance(daily_total, float) and daily_total.is_integer():
                    daily_total = int(daily_total)
                
                logger.info(f"Daily total for {activity_type}: {daily_total} {unit}")
            except Exception as e:
                logger.warning(f"Could not get daily total: {e}")
        
        # Create friendly, natural responses
        emoji_map = {'water': '💧', 'sleep': '😴', 'exercise': '💪', 'weight': '⚖️'}
        emoji = emoji_map.get(activity_type, '✅')
        
        if activity_type == 'water':
            import random
            if daily_total and daily_total > value:
                # Multiple water entries
                if daily_total >= 8:
                    responses = [
                        f"Awesome! That's {daily_total} glasses today - you're crushing it!",
                        f"Nice! {daily_total} glasses total. You're well hydrated!",
                        f"Perfect! {daily_total} glasses today. Great job!"
                    ]
                else:
                    responses = [
                        f"Got it! That's {daily_total} glasses so far today.",
                        f"Nice! {daily_total} glasses total today.",
                        f"Perfect! {daily_total} glasses logged for today."
                    ]
            else:
                # Single water entry
                if value >= 4:
                    responses = [
                        f"Great! {value} glasses is a solid start.",
                        f"Nice! {value} glasses logged.",
                        f"Awesome! {value} glasses - good hydration."
                    ]
                else:
                    responses = [
                        f"Got it! {value} glasses logged.",
                        f"Thanks! {value} glasses noted.",
                        f"Perfect! {value} glasses is a good start."
                    ]
            return random.choice(responses) + f" {emoji}"
                
        elif activity_type == 'weight':
            return f"Perfect! Weight logged. {emoji}"
            
        elif activity_type == 'sleep':
            import random
            if daily_total and daily_total > value:
                # Multiple sleep entries
                responses = [
                    f"Got it! That's {daily_total} hours total today.",
                    f"Nice! {daily_total} hours total for today.",
                    f"Perfect! {daily_total} hours logged for today."
                ]
            else:
                # Single sleep entry
                if value >= 8:
                    responses = [
                        f"Nice! {value} hours is solid sleep.",
                        f"Great! {value} hours should have you feeling good.",
                        f"Awesome! {value} hours is excellent."
                    ]
                elif value >= 6:
                    responses = [
                        f"Got it! {value} hours logged.",
                        f"Thanks! {value} hours noted.",
                        f"Perfect! {value} hours is decent."
                    ]
                else:
                    responses = [
                        f"Got it! {value} hours logged. Hope you can rest more later.",
                        f"Thanks! {value} hours noted. That's pretty short.",
                        f"Logged! {value} hours is not much - take care of yourself."
                    ]
            return random.choice(responses) + f" {emoji}"
            
        elif activity_type == 'exercise':
            import random
            if daily_total and daily_total > value:
                if daily_total >= 60:
                    responses = [
                        f"Wow! That's {daily_total} minutes today. You're on fire!",
                        f"Amazing! {daily_total} minutes total - you're crushing it!",
                        f"Incredible! {daily_total} minutes today. Beast mode!"
                    ]
                else:
                    responses = [
                        f"Nice! That's {daily_total} minutes today.",
                        f"Great! {daily_total} minutes total so far.",
                        f"Awesome! {daily_total} minutes logged today."
                    ]
            else:
                if value >= 30:
                    responses = [
                        f"Excellent! {value} minutes is a solid workout.",
                        f"Great job! {value} minutes of movement.",
                        f"Nice! {value} minutes - that's awesome."
                    ]
                else:
                    responses = [
                        f"Good! {value} minutes logged.",
                        f"Nice! {value} minutes of movement.",
                        f"Great! {value} minutes is a good start."
                    ]
            return random.choice(responses) + f" {emoji}"
        else:
            # Generic fallback
            return f"Perfect! {value} {unit} logged! {emoji}"
    
    def _get_wellness_suggestions(self, user_id: int) -> list:
        """Get personalized wellness activity suggestions for engagement after logging"""
        try:
            from chat_assistant.smart_suggestions import get_smart_suggestions
            from chat_assistant.context_builder_simple import build_context
            
            # Build user context
            context = build_context(user_id)
            
            # Get suggestions for general wellness
            # This uses smart_suggestions with full personalization
            suggestions = get_smart_suggestions(
                mood_emoji="😊",
                reason="general",
                context=context,
                count=4
            )
            
            logger.info(f"Got {len(suggestions)} wellness suggestions for engagement")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get wellness suggestions: {e}")
            return []

    def _update_session_summary(self, state: WorkflowState, activity_type: str, unit: Optional[str] = None):
        """
        Update session summary after activity logging
        
        Args:
            state: Workflow state with session summary
            activity_type: Type of activity logged
            unit: Unit used (for preferences)
        """
        from .session_summary import SessionFocus
        
        # Map activity type to focus
        focus_map = {
            'water': SessionFocus.HYDRATION,
            'sleep': SessionFocus.SLEEP,
            'exercise': SessionFocus.EXERCISE,
            'weight': SessionFocus.WEIGHT
        }
        
        focus = focus_map.get(activity_type)
        if focus:
            state.session_summary.set_focus(focus)
        
        # Capture explicit unit preference
        if unit and activity_type == 'water':
            state.session_summary.set_preference('water_unit', unit)
        elif unit and activity_type == 'sleep':
            state.session_summary.set_preference('sleep_unit', unit)
        
        logger.info(f"Updated session summary: {state.session_summary}")
    
    def _ask_value_clarification(self, activity_type: str) -> WorkflowResponse:
        """
        Ask user to provide the value for their activity
        
        Args:
            activity_type: Type of activity (steps, calories, etc.)
            
        Returns:
            WorkflowResponse asking for value clarification
        """
        if activity_type == 'steps':
            message = "How many steps did you take?"
        elif activity_type == 'calories':
            message = "How many calories did you consume?"
        elif activity_type == 'meal':
            message = "How many meals/servings did you have?"
        elif activity_type == 'water':
            message = "How much water did you drink?"
        elif activity_type == 'sleep':
            message = "How many hours did you sleep?"
        elif activity_type == 'exercise':
            message = "How many minutes did you exercise?"
        elif activity_type == 'weight':
            message = "What is your weight?"
        else:
            message = f"How much {activity_type} would you like to log?"
        
        return WorkflowResponse(
            message=message,
            ui_elements=['text_input'],
            completed=False,
            next_state=ConversationState.CLARIFICATION_PENDING
        )
    
    def _ask_unit_clarification(self, activity_type: str, value: float, show_examples: bool = False) -> WorkflowResponse:
        """
        Ask user to clarify the unit for their input
        
        Args:
            activity_type: Type of activity (water, weight, etc.)
            value: The numeric value they provided
            show_examples: Whether to show unit examples
            
        Returns:
            WorkflowResponse asking for unit clarification
        """
        # Get supported units for this activity
        supported_units = self.intent_detector.unit_converter.get_supported_units(activity_type)
        
        if show_examples:
            # Second attempt - show examples
            examples = ", ".join(supported_units[:3])  # Show first 3 units
            message = f"Please specify the unit for {value}. For example: '{examples}'. What unit did you mean?"
        else:
            # First attempt - simple question
            if activity_type == 'weight':
                message = f"{value} what? kg or lbs?"
            elif activity_type == 'water':
                message = f"{value} what? glasses, liters, or ml?"
            elif activity_type == 'sleep':
                message = f"{value} what? hours or minutes?"
            elif activity_type == 'exercise':
                message = f"{value} what? minutes or hours?"
            else:
                message = f"What unit for {value}? Please specify."
        
        return WorkflowResponse(
            message=message,
            ui_elements=['text_input'],
            completed=False,
            next_state=ConversationState.CLARIFICATION_PENDING
        )
    
    def _create_friendly_response(self, activity_type: str, value: float, unit: str, conversion_msg: str = "") -> str:
        """
        Create a friendly, natural response for activity logging
        
        Args:
            activity_type: Type of activity logged
            value: Converted value
            unit: Standard unit
            conversion_msg: Optional conversion message
            
        Returns:
            Natural, friendly response message
        """
        # Format value nicely (remove .0 for whole numbers)
        formatted_value = int(value) if value == int(value) else value
        
        # Create natural responses based on activity type
        if activity_type == 'weight':
            if conversion_msg:
                return f"Got it! {conversion_msg}. Weight logged! ⚖️"
            else:
                return f"Perfect! {formatted_value} {unit} logged. ⚖️"
                
        elif activity_type == 'water':
            if conversion_msg:
                return f"Nice! {conversion_msg} of water logged. Stay hydrated! 💧"
            else:
                return f"Great! {formatted_value} {unit} logged. Keep it up! 💧"
                
        elif activity_type == 'sleep':
            if conversion_msg:
                return f"Thanks! {conversion_msg} of sleep logged. Rest is important! 😴"
            else:
                return f"Good! {formatted_value} {unit} logged. Sweet dreams! 😴"
                
        elif activity_type == 'exercise':
            if conversion_msg:
                return f"Awesome! {conversion_msg} of exercise logged. Keep moving! 💪"
            else:
                return f"Excellent! {formatted_value} {unit} logged. You're doing great! 💪"
                
        else:
            # Generic fallback
            if conversion_msg:
                return f"Got it! {conversion_msg}. Activity logged! ✅"
            else:
                return f"Perfect! {formatted_value} {unit} logged. ✅"
