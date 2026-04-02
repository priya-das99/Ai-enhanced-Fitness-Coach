# workflow_base.py
# Base class for all workflows

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from .unified_state import WorkflowState, ConversationState
import logging

logger = logging.getLogger(__name__)

class WorkflowResponse:
    """Standardized workflow response"""
    
    def __init__(
        self,
        message: str,
        ui_elements: list = None,
        completed: bool = False,
        next_state: Optional[ConversationState] = None,
        extra_data: Dict[str, Any] = None,
        events: list = None,
        ui_type: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.message = message
        self.ui_elements = ui_elements or []
        self.completed = completed
        self.next_state = next_state
        self.extra_data = extra_data or {}
        self.events = events or []  # NEW: Events to publish
        self.ui_type = ui_type  # NEW: Explicit UI type
        self.metadata = metadata or {}  # NEW: Metadata for debugging/analytics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        response = {
            'message': self.message,
            'ui_elements': self.ui_elements,
            'state': self.next_state.value if self.next_state else None
        }
        response.update(self.extra_data)
        return response

class BaseWorkflow(ABC):
    """
    Base class for all workflows
    
    Phase 1 Refactoring: Workflows no longer need can_handle()
    Intent detection is handled by LLM, workflows are pure handlers
    """
    
    def __init__(self, workflow_name: str, handled_intents: list = None):
        self.workflow_name = workflow_name
        self.handled_intents = handled_intents or []  # Intents this workflow handles
    
    def is_rejection(self, message: str) -> bool:
        """
        Detect if message is a rejection (works across all workflows)
        
        Args:
            message: User's message
            
        Returns:
            True if message is a rejection
        """
        message_lower = message.lower().strip()
        
        rejection_phrases = [
            'no', 'nope', 'nah', 'no thanks', 'no thank you',
            'i will not', 'i wont', "i won't", 'will not do',
            'dont want', "don't want", 'not interested',
            'skip', 'pass', 'not now', 'maybe later',
            'i refuse', 'refuse', 'decline'
        ]
        
        return any(phrase in message_lower for phrase in rejection_phrases)
    
    @abstractmethod
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """
        Start the workflow
        
        Args:
            message: User's message that triggered the workflow
            state: Workflow state object
            user_id: User ID
            
        Returns:
            WorkflowResponse with next message and state
        """
        pass
    
    @abstractmethod
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """
        Process a message within an active workflow
        
        Args:
            message: User's message
            state: Current workflow state
            user_id: User ID
            
        Returns:
            WorkflowResponse with next message and state
        """
        pass
    
    def get_priority(self) -> int:
        """
        DEPRECATED: Priority no longer used in Phase 1
        Intent routing is handled by LLM, not priority
        
        Returns:
            Priority number (kept for backward compatibility)
        """
        return 999  # Default low priority
    
    def get_handled_intents(self) -> list:
        """
        Get list of intents this workflow handles
        
        Returns:
            List of intent strings (e.g., ['mood_logging', 'mood_check'])
        """
        return self.handled_intents
    
    def _create_response(
        self,
        message: str,
        ui_elements: list = None,
        completed: bool = False,
        next_state: Optional[ConversationState] = None,
        **extra_data
    ) -> WorkflowResponse:
        """Helper to create workflow response"""
        return WorkflowResponse(
            message=message,
            ui_elements=ui_elements,
            completed=completed,
            next_state=next_state,
            extra_data=extra_data
        )
    
    def _complete_workflow(self, message: str, ui_elements: list = None, **extra_data) -> WorkflowResponse:
        """Helper to create completion response"""
        return WorkflowResponse(
            message=message,
            ui_elements=ui_elements or [],
            completed=True,
            next_state=ConversationState.IDLE,
            extra_data=extra_data
        )
    
    def _ask_clarification(
        self,
        message: str,
        ui_elements: list = None,
        **extra_data
    ) -> WorkflowResponse:
        """Helper to ask for clarification"""
        return WorkflowResponse(
            message=message,
            ui_elements=ui_elements or ['text_input'],
            completed=False,
            next_state=ConversationState.CLARIFICATION_PENDING,
            extra_data=extra_data
        )
    
    def _ask_confirmation(
        self,
        message: str,
        ui_elements: list = None,
        **extra_data
    ) -> WorkflowResponse:
        """Helper to ask for action confirmation"""
        return WorkflowResponse(
            message=message,
            ui_elements=ui_elements or ['action_buttons'],
            completed=False,
            next_state=ConversationState.ACTION_CONFIRMATION_PENDING,
            extra_data=extra_data
        )
    
    def handle_contextless_input(self, message: str) -> Optional[str]:
        """
        Handle short contextless inputs like 'yes', 'no', 'ok'
        
        Returns:
            Mapped intent or None if not contextless
        """
        message_lower = message.lower().strip()
        
        # Map common confirmations
        if message_lower in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
            return 'confirm'
        
        if message_lower in ['no', 'nope', 'nah', 'skip']:
            return 'decline'
        
        return None

    
    # ===== UNIVERSAL FEEDBACK HANDLING =====
    # Extracted from activity_workflow.py for reuse across all workflows
    
    def handle_external_activity_return(
        self, 
        message: str, 
        state: WorkflowState, 
        user_id: int,
        activity_name: str = None
    ) -> Optional[WorkflowResponse]:
        """
        Universal handler for when user returns from external activity.
        
        This should be called in the process() method of any workflow that
        handles external activities (YouTube videos, blogs, etc.)
        
        Args:
            message: User's message
            state: Workflow state
            user_id: User ID
            activity_name: Name of the activity (optional, will try to get from state)
            
        Returns:
            WorkflowResponse if this is a return event, None otherwise
        """
        # Check if we're waiting for user to return from external activity
        awaiting_return = state.get_workflow_data('awaiting_return', False)
        pending_activity = state.get_workflow_data('pending_external_activity')
        
        if not (awaiting_return and pending_activity):
            return None  # Not waiting for return
        
        # Get activity name
        if not activity_name:
            activity_name = state.get_workflow_data('activity_name', 'the activity')
        
        logger.info(f"[External Activity] User returned from: {pending_activity}")
        
        # Check if this is the automatic return message from frontend
        if message.lower().startswith('returned_from_'):
            # Automatic return detection - ask for feedback with buttons
            state.set_workflow_data('awaiting_return', False)
            state.set_workflow_data('awaiting_feedback', True)
            
            return WorkflowResponse(
                message=f"Welcome back! How did that go? 😊",
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
            state.set_workflow_data('awaiting_return', False)
            state.set_workflow_data('pending_external_activity', None)
            
            return self._complete_workflow(
                message=f"Thanks for sharing! I'm glad you tried it. 💪",
                ui_elements=[]
            )
    
    def handle_external_activity_feedback(
        self,
        message: str,
        state: WorkflowState,
        user_id: int
    ) -> Optional[WorkflowResponse]:
        """
        Universal handler for feedback after external activity.
        
        This should be called in the process() method after handle_external_activity_return()
        
        Args:
            message: User's feedback message
            state: Workflow state
            user_id: User ID
            
        Returns:
            WorkflowResponse if this is feedback, None otherwise
        """
        # Check if we're awaiting feedback
        awaiting_feedback = state.get_workflow_data('awaiting_feedback', False)
        
        if not awaiting_feedback:
            return None  # Not waiting for feedback
        
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
    
    def start_external_activity(
        self,
        state: WorkflowState,
        activity_id: str,
        activity_name: str
    ) -> WorkflowResponse:
        """
        Universal method to start an external activity and wait for return.
        
        Call this when user selects an external activity (YouTube, blog, etc.)
        
        Args:
            state: Workflow state
            activity_id: ID of the activity
            activity_name: Name of the activity
            
        Returns:
            WorkflowResponse that keeps workflow active
        """
        logger.info(f"[External Activity] Starting: {activity_name} (ID: {activity_id})")
        
        # Get current workflow data
        current_data = state.workflow_data.copy() if state.workflow_data else {}
        
        # Update with external activity info
        current_data.update({
            'pending_external_activity': activity_id,
            'activity_name': activity_name,
            'awaiting_return': True,
            'activity_started_at': str(__import__('datetime').datetime.now())
        })
        
        # Update workflow step with merged data
        current_step = state.get_workflow_data('step', 'waiting_feedback')
        state.update_workflow_step(current_step, current_data)
        
        # Return message that activity is starting
        # Frontend will open the external link
        return WorkflowResponse(
            message=f"Great choice! Opening {activity_name}. Take your time, and let me know when you're done! 💙",
            ui_elements=[],
            completed=False,  # Keep workflow active!
            next_state=None  # Stay in current workflow state
        )
