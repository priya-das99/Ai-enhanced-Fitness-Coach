# context_router.py
# Context-aware message routing system for workflow management
# Prevents context loss between workflows by detecting intent before processing

from typing import Optional, Dict, Any
from .workflow_base import WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .activity_intent_detector import ActivityIntentDetector
import logging

logger = logging.getLogger(__name__)

class ContextRouter:
    """
    Routes messages to correct workflow based on intent detection
    
    Key Features:
    - Detects activity intent before workflow processing
    - Handles context switching between workflows
    - Prevents wrong activity logging
    - Includes confidence thresholds and timeout handling
    """
    
    # Required fields for complete activity data
    REQUIRED_FIELDS = {
        "water": ["value"],
        "sleep": ["value"], 
        "exercise": ["value"],
        "weight": ["value"],
        "meal": ["value"]
    }
    
    # Confidence threshold for workflow switching
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        self.intent_detector = ActivityIntentDetector()
    
    def route_message(self, message: str, state: WorkflowState, user_id: int) -> Optional[WorkflowResponse]:
        """
        Route message to appropriate workflow based on intent detection
        
        Args:
            message: User's message
            state: Current workflow state
            user_id: User identifier
            
        Returns:
            WorkflowResponse if routing handled, None if should continue to chat engine
        """
        
        # Check for stale workflow timeout first
        if state.is_workflow_stale(timeout_minutes=5):
            logger.info(f"Workflow timeout | user={user_id} | clearing stale workflow")
            state.complete_workflow()
        
        # Check for explicit context switch first (highest priority)
        explicit_switch = self._detect_explicit_context_switch(message, state)
        if explicit_switch:
            logger.info(f"Explicit context switch detected | user={user_id} | switching to {explicit_switch}")
            state.complete_workflow()
            return self._start_workflow_by_name(explicit_switch, state, user_id, message)
        
        # Detect primary activity intent
        detected_intent = self._detect_primary_activity(message)
        
        # Get current workflow context
        current_workflow = state.active_workflow
        expected_activity = state.get_workflow_data('activity_type') if current_workflow else None
        
        # Enhanced logging for debugging
        logger.info(
            f"Context routing | user={user_id} | "
            f"workflow={current_workflow} | expected={expected_activity} | "
            f"detected={detected_intent.get('activity_type') if detected_intent else None} | "
            f"confidence={detected_intent.get('confidence', 0) if detected_intent else 0} | "
            f"message='{message[:50]}...'"
        )
        
        # Handle active workflow scenarios
        if current_workflow and expected_activity:
            return self._handle_active_workflow(
                message, detected_intent, expected_activity, state, user_id
            )
        
        # No active workflow - route based on detected intent
        if detected_intent and detected_intent['confidence'] >= self.CONFIDENCE_THRESHOLD:
            return self._start_activity_workflow(detected_intent, state, user_id, message)
        
        # No clear activity intent - let chat engine handle
        return None
    
    def _detect_primary_activity(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect single primary activity with confidence scoring
        
        Returns:
            Dict with activity_type, value, unit, confidence, has_complete_data
            None if no activity detected
        """
        try:
            activities = self.intent_detector.detect_all_activities(message)
            
            if not activities:
                return None
            
            # Get highest confidence activity
            primary = activities[0]
            
            # Check if activity has complete data
            activity_type = primary['activity_type']
            required_fields = self.REQUIRED_FIELDS.get(activity_type, ['value'])
            
            has_complete_data = all(
                primary.get(field) is not None 
                for field in required_fields
            )
            
            return {
                'activity_type': activity_type,
                'value': primary.get('value'),
                'unit': primary.get('unit'),
                'confidence': primary.get('confidence', 0.8),  # Default confidence
                'has_complete_data': has_complete_data,
                'notes': primary.get('notes', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to detect primary activity: {e}")
            return None
    
    def _handle_active_workflow(self, message: str, detected_intent: Optional[Dict], 
                              expected_activity: str, state: WorkflowState, user_id: int) -> Optional[WorkflowResponse]:
        """
        Handle message when there's an active workflow
        
        Returns:
            WorkflowResponse if handled, None to continue with current workflow
        """
        
        # Safety rule: If no activity detected and no number, treat as general chat
        if not detected_intent and not self._contains_number(message):
            # Check if message looks like general chat
            general_chat_indicators = [
                'hello', 'hi', 'hey', 'thanks', 'thank you', 'ok', 'okay', 
                'yes', 'no', 'haha', 'lol', 'cool', 'nice', 'great'
            ]
            
            message_lower = message.lower().strip()
            if any(indicator in message_lower for indicator in general_chat_indicators):
                logger.info(f"General chat detected during workflow | user={user_id} | message='{message}'")
                # Let current workflow handle it (might be a response to clarification)
                return None
        
        # Check for context mismatch
        if detected_intent and detected_intent['confidence'] >= self.CONFIDENCE_THRESHOLD:
            detected_activity = detected_intent['activity_type']
            
            # Same activity shortcut - avoid restarting workflow unnecessarily
            if detected_activity == expected_activity:
                logger.info(f"Same activity detected | user={user_id} | continuing current workflow")
                return None  # Continue with current workflow
            
            # Different activity detected - handle context switch
            return self._handle_context_switch(
                expected_activity, detected_intent, state, user_id, message
            )
        elif detected_intent:
            # Log why we didn't switch (confidence too low)
            logger.info(
                f"Low confidence detection | user={user_id} | "
                f"activity={detected_intent['activity_type']} | "
                f"confidence={detected_intent['confidence']:.2f} < {self.CONFIDENCE_THRESHOLD} | "
                f"not switching workflows"
            )
        
        # No clear different intent - continue with current workflow
        return None
    
    def _handle_context_switch(self, expected_activity: str, detected_intent: Dict, 
                             state: WorkflowState, user_id: int, message: str) -> WorkflowResponse:
        """
        Handle switching from one activity workflow to another
        
        Args:
            expected_activity: What the current workflow expects
            detected_intent: What was actually detected
            state: Current workflow state
            user_id: User identifier
            message: Original user message
            
        Returns:
            WorkflowResponse handling the context switch
        """
        detected_activity = detected_intent['activity_type']
        
        logger.info(
            f"Context switch | user={user_id} | "
            f"{expected_activity} → {detected_activity} | "
            f"complete_data={detected_intent['has_complete_data']} | "
            f"message='{message}'"
        )
        
        if detected_intent['has_complete_data']:
            # Auto-switch: user provided complete activity data
            state.complete_workflow()
            return self._start_activity_workflow(detected_intent, state, user_id, message)
        else:
            # Ask clarification: incomplete data detected
            return self._ask_context_clarification(expected_activity, detected_intent)
    
    def _start_activity_workflow(self, detected_intent: Dict, state: WorkflowState, 
                               user_id: int, message: str) -> WorkflowResponse:
        """
        Start activity workflow with detected intent
        
        Args:
            detected_intent: Detected activity data
            state: Workflow state
            user_id: User identifier
            message: Original message
            
        Returns:
            WorkflowResponse from activity workflow
        """
        try:
            from .activity_workflow import ActivityWorkflow
            
            activity_workflow = ActivityWorkflow()
            
            logger.info(
                f"Starting activity workflow | user={user_id} | "
                f"activity={detected_intent['activity_type']} | "
                f"confidence={detected_intent['confidence']}"
            )
            
            return activity_workflow.start(message, state, user_id)
            
        except Exception as e:
            logger.error(f"Failed to start activity workflow: {e}")
            return WorkflowResponse(
                message="Sorry, I couldn't process that activity. Please try again.",
                ui_elements=[],
                completed=True,
                next_state=ConversationState.LISTENING
            )
    
    def _ask_context_clarification(self, expected_activity: str, detected_intent: Dict) -> WorkflowResponse:
        """
        Ask user to clarify which activity they want to log
        
        Args:
            expected_activity: What was expected
            detected_intent: What was detected
            
        Returns:
            WorkflowResponse asking for clarification
        """
        detected_activity = detected_intent['activity_type']
        
        message = f"I was expecting {expected_activity} info, but you mentioned {detected_activity}. Which would you like to log?"
        
        return WorkflowResponse(
            message=message,
            ui_elements=['action_buttons_multiple'],
            completed=False,
            next_state=ConversationState.ACTION_CONFIRMATION_PENDING,
            extra_data={
                'actions': [
                    {'id': f'log_{expected_activity}', 'name': f'Log {expected_activity.title()}'},
                    {'id': f'log_{detected_activity}', 'name': f'Log {detected_activity.title()}'}
                ]
            }
        )
    
    def _contains_number(self, message: str) -> bool:
        """Check if message contains any numbers"""
        try:
            value = self.intent_detector.extract_number(message)
            return value is not None
        except:
            return False
    
    def _detect_explicit_context_switch(self, message: str, state: WorkflowState) -> Optional[str]:
        """
        Detect explicit context switch phrases like:
        - "Actually, I want to log my mood instead"
        - "No, I want to log sleep"
        - "Let me log exercise instead"
        
        Returns:
            Workflow name to switch to, or None
        """
        message_lower = message.lower().strip()
        
        # Explicit switch indicators
        switch_indicators = [
            'actually', 'instead', 'no,', 'wait,', 'let me', 
            'i want to log', 'i want log', 'change to', 'switch to'
        ]
        
        # Check if message contains switch indicator
        has_switch_indicator = any(indicator in message_lower for indicator in switch_indicators)
        
        if not has_switch_indicator:
            return None
        
        # Map activity keywords to workflow names
        activity_to_workflow = {
            'mood': 'mood_logging',
            'water': 'activity_logging',
            'sleep': 'activity_logging',
            'exercise': 'exercise_logging',
            'weight': 'activity_logging',
            'steps': 'activity_logging',
        }
        
        # Check which activity is mentioned
        for activity, workflow in activity_to_workflow.items():
            if activity in message_lower:
                logger.info(f"Explicit switch detected: '{message}' → {workflow} ({activity})")
                return workflow
        
        return None
    
    def _start_workflow_by_name(self, workflow_name: str, state: WorkflowState, 
                               user_id: int, message: str) -> WorkflowResponse:
        """
        Start a specific workflow by name
        
        Args:
            workflow_name: Name of workflow to start
            state: Workflow state
            user_id: User identifier
            message: Original message
            
        Returns:
            WorkflowResponse from the workflow
        """
        try:
            if workflow_name == 'mood_logging':
                from .mood_workflow import MoodWorkflow
                workflow = MoodWorkflow()
            elif workflow_name == 'exercise_logging':
                from .activity_workflow import ActivityWorkflow
                workflow = ActivityWorkflow()
            else:
                from .activity_workflow import ActivityWorkflow
                workflow = ActivityWorkflow()
            
            logger.info(f"Starting workflow by name | user={user_id} | workflow={workflow_name}")
            return workflow.start(message, state, user_id)
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_name}: {e}")
            return WorkflowResponse(
                message="Sorry, I couldn't process that. Please try again.",
                ui_elements=[],
                completed=True,
                next_state=ConversationState.LISTENING
            )