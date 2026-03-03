# activity_workflow.py
# Activity logging workflow (water, sleep, exercise, weight)
# Phase 2: Integrated with EventPublisher for analytics

from typing import Optional
from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .activity_intent_detector import ActivityIntentDetector
from .health_activity_logger import HealthActivityLogger
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

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
            handled_intents=['activity_logging', 'log_water', 'log_exercise', 'log_sleep', 'log_weight', 'log_meal']
        )
        self.intent_detector = ActivityIntentDetector()
        self.activity_logger = HealthActivityLogger()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start activity logging workflow"""
        logger.info(f"Starting activity workflow for user {user_id}")
        
        # Check if this is an external content or activity start button (start_content_X, start_meditation, etc.)
        if message.lower().startswith('start_'):
            return self._handle_external_activity_button(message, state, user_id)
        
        # Check if this is a button click (log_water, log_sleep, etc.)
        if message.lower().startswith('log_'):
            return self._handle_button_click(message, state, user_id)
        
        # Detect activities from message
        activities = self.intent_detector.detect_all_activities(message)
        
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
        
        # Have all info - log immediately
        try:
            self.activity_logger.log_activity(
                user_id=user_id,
                activity_type=activity['activity_type'],
                value=activity['value'],
                unit=activity['unit'],
                notes=activity['notes']
            )
            
            logger.info(f"Logged {activity['activity_type']}: {activity['value']} {activity['unit']}")
            
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
            
            return self._complete_workflow(
                message=self._create_activity_response({
                    'activity_type': activity['activity_type'],
                    'value': activity['value'],
                    'unit': activity['unit'],
                    'user_id': user_id
                }),
                ui_elements=[],  # No buttons - keep chat clean
                events=[{'type': 'activity_logged', 'activity_type': activity['activity_type'], 'value': activity['value'], 'unit': activity['unit']}]
            )
        
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return self._complete_workflow(
                message="Sorry, I couldn't log that activity."
            )
    
    def _handle_button_click(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle button clicks like log_water, log_sleep, etc."""
        # Map button IDs to activity types
        button_to_activity = {
            'log_water': 'water',
            'log_sleep': 'sleep',
            'log_exercise': 'exercise',
            'log_weight': 'weight'
        }
        
        message_lower = message.lower().strip()
        activity_type = button_to_activity.get(message_lower)
        
        if not activity_type:
            # Unknown button, treat as regular message
            return self._complete_workflow(
                message="I didn't understand that. Please try again."
            )
        
        # Get unit for this activity type
        unit = self.activity_logger.ACTIVITY_TYPES[activity_type]['unit']
        
        # Start workflow and ask for quantity
        state.start_workflow(self.workflow_name, {
            'activity_type': activity_type,
            'unit': unit,
            'notes': f'Button: {message}'
        })
        
        return self._ask_clarification(
            message=self._get_clarification_message(activity_type),
            ui_elements=['text_input']
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
        
        # Check if we're awaiting duplicate confirmation
        awaiting_confirmation = state.get_workflow_data('awaiting_duplicate_confirmation', False)
        
        if awaiting_confirmation:
            # User is responding to "already logged" confirmation
            message_lower = message.lower().strip()
            
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
        
        # Got quantity - log activity
        try:
            self.activity_logger.log_activity(
                user_id=user_id,
                activity_type=activity_type,
                value=value,
                unit=unit,
                notes=f"{notes} - {message}"
            )
            
            logger.info(f"Logged {activity_type}: {value} {unit}")
            
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
            
            return self._complete_workflow(
                message=self._create_activity_response({
                    'activity_type': activity_type,
                    'value': value,
                    'unit': unit,
                    'user_id': user_id
                }),
                ui_elements=[],  # No buttons - keep chat clean
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
            
            # Create a natural prompt for the LLM
            prompt = f"""Generate a friendly, conversational question asking the user how much {activity_type} they want to log.

Activity type: {activity_type}

Requirements:
- Keep it short and friendly (1 sentence)
- Use natural language
- Be encouraging
- Don't use emojis

Examples:
- For water: "How many glasses of water did you drink?"
- For sleep: "How many hours did you sleep last night?"
- For exercise: "How long did you exercise for?"
- For weight: "What's your current weight?"

Generate the question:"""
            
            response = llm.generate_response(
                user_message=prompt,
                conversation_history=[],
                system_context="You are a friendly wellness assistant helping users log their health activities."
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
        # Map button IDs to activity types
        button_to_activity = {
            'log_water': 'water',
            'log_sleep': 'sleep',
            'log_weight': 'weight',
            'log_exercise': 'exercise'
        }
        
        button_id = message.lower().strip()
        activity_type = button_to_activity.get(button_id)
        
        if not activity_type:
            # Unknown button, treat as regular message
            return self._complete_workflow(
                message="I didn't understand that. Please try again."
            )
        
        # Check if user already logged this activity recently (today)
        recent_log = self._check_recent_activity(user_id, activity_type)
        
        if recent_log:
            # User already logged this activity today
            activity_name = activity_type.capitalize()
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
        
        # Start workflow and ask for quantity
        state.start_workflow(self.workflow_name, {
            'activity_type': activity_type,
            'unit': unit,
            'notes': f'Button: {button_id}'
        })
        
        return self._ask_clarification(
            message=self._get_clarification_message(activity_type),
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
        
        # If ambiguous, use LLM with semantic summary + conversation history
        try:
            from .llm_service import get_llm_service
            llm = get_llm_service()
            
            # Check and clear stale summary
            state.session_summary.clear_if_stale()
            
            # Build context: summary FIRST, then buffer
            messages = [
                {"role": "system", "content": """Analyze if the user wants to cancel the current action.
Respond in exactly this format:
intent=cancel|continue
confidence=0.85"""}
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
        Create motivational activity response message using LLM
        Shows daily total for cumulative activities like water
        
        Args:
            activity: Dict with activity_type, value, unit, user_id (optional)
            
        Returns:
            Formatted response message with daily total
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
                
                # Format daily_total nicely too
                if isinstance(daily_total, float) and daily_total.is_integer():
                    daily_total = int(daily_total)
                
                logger.info(f"Daily total for {activity_type}: {daily_total} {unit}")
            except Exception as e:
                logger.warning(f"Could not get daily total: {e}")
        
        # Use LLM to generate natural, context-aware response
        try:
            from chat_assistant.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            # Build context for LLM
            if daily_total and daily_total > value:
                context = f"User just logged: {value} {unit} of {activity_type}. Daily total so far: {daily_total} {unit}"
            else:
                context = f"User logged: {value} {unit} of {activity_type}"
            
            # Add health context based on values
            health_notes = []
            check_value = daily_total if daily_total else value
            
            if activity_type == 'sleep':
                if check_value < 6:
                    health_notes.append("This is below the recommended 7-8 hours")
                elif check_value >= 7 and check_value <= 9:
                    health_notes.append("This is in the ideal range of 7-9 hours")
            elif activity_type == 'water':
                if check_value < 4:
                    health_notes.append("Below the recommended 8 glasses daily")
                elif check_value >= 8:
                    health_notes.append("Great! You've hit the daily goal")
            elif activity_type == 'exercise':
                if check_value < 15:
                    health_notes.append("This is a short session")
                elif check_value >= 30:
                    health_notes.append("This meets the recommended 30 minutes daily")
            
            if health_notes:
                context += f". {health_notes[0]}"
            
            prompt = f"""You are MoodCapture, a supportive wellness assistant.

User just logged an activity:
- Activity: {activity_type}
- Amount logged now: {value} {unit}
{f"- Daily total so far: {daily_total} {unit}" if daily_total and daily_total > value else ""}
{f"- Note: {health_notes[0]}" if health_notes else ""}

Generate a brief, natural response (1-2 sentences max).

Guidelines:
- Be warm and conversational, like a friend
- If there's a daily total, mention it naturally (e.g., "That's 5 glasses today!")
- If the value is concerning (like low sleep), show gentle concern
- If the value is good, celebrate it naturally
- Use ONE relevant emoji
- Sound human and casual, not robotic
- Vary your phrasing - avoid templates
- DO NOT ask if they want to log another activity

Examples:
- For 2 glasses water (5 total today): "2 more glasses! That's 5 today. 💧"
- For 3 glasses water (3 total): "3 glasses down! 💧"
- For 5 hours sleep: "Only 5 hours? That's rough. 😟 Try to get more rest tonight!"
- For 8 hours sleep: "Nice! 8 hours is perfect. 😴"
- For 30 min exercise: "30 minutes! That's awesome! 💪"

Response:"""
            
            message = llm_service.call(
                prompt=prompt,
                system_message="You are a supportive wellness assistant. Be encouraging, casual, and human.",
                temperature=0.8,  # Higher for more variety
                max_tokens=60
            )
            
            logger.info(f"🤖 LLM generated activity response: {message[:50]}...")
            
        except Exception as e:
            logger.warning(f"LLM response generation failed, using fallback: {e}")
            # Fallback to template-based responses
            emoji_map = {'water': '💧', 'sleep': '😴', 'exercise': '�', 'weight': '⚖️'}
            emoji = emoji_map.get(activity_type, '✅')
            
            if activity_type == 'sleep' and value < 6:
                message = f"Only {value} {unit}? Try to get more rest tonight! 😟"
            elif activity_type == 'water' and value >= 8:
                message = f"Great job staying hydrated! {emoji}"
            elif activity_type == 'exercise' and value >= 30:
                message = f"{value} minutes! That's awesome! {emoji}"
            else:
                message = f"{value} {unit} logged! {emoji}"
        
        # Try to get challenge progress
        try:
            from app.services.challenge_service import ChallengeService
            challenge_service = ChallengeService()
            
            # Get user's active challenges for this activity type
            user_id = activity.get('user_id')
            if user_id:
                challenges = challenge_service.get_user_challenges(user_id)
                
                challenge_updates = []
                for challenge in challenges:
                    if challenge.get('challenge_type') == activity_type:
                        progress = challenge.get('progress', 0)
                        title = challenge.get('title', '')
        
        # ===== ADD STREAK CELEBRATION =====
        # Check for activity streak
        if user_id:
            try:
                from app.services.pattern_detector import PatternDetector
                pattern_detector = PatternDetector()
                patterns = pattern_detector.detect_all_patterns(user_id)
                
                streak = patterns['activity_patterns']['streak']
                
                # Celebrate streaks of 3+ days
                if streak >= 3:
                    if streak >= 7:
                        message += f"\n\n🔥 That's {streak} days in a row! You're on fire!"
                    elif streak >= 5:
                        message += f"\n\n🔥 {streak}-day streak! Keep it going!"
                    else:
                        message += f"\n\n🔥 {streak} days in a row!"
                    
                    logger.info(f"🔥 Celebrated {streak}-day streak for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not check streak: {e}")
        # ==================================
                    
                    if progress >= 100:
                        challenge_updates.append(f"🎉 Challenge completed: {title}!")
                    else:
                        challenge_updates.append(f"📊 {title}: {progress:.0f}%")
            
            if challenge_updates:
                message += "\n\n" + "\n".join(challenge_updates)
                
        except Exception as e:
            logger.warning(f"Could not get challenge progress: {e}")
        
        return message
    
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
