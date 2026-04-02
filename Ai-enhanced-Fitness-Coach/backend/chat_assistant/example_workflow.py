# example_workflow.py
# Example workflow for testing

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
import logging

logger = logging.getLogger(__name__)

class ExampleWorkflow(BaseWorkflow):
    """Example workflow for testing the system - Phase 1 Refactored"""
    
    def __init__(self):
        super().__init__(
            workflow_name="example_workflow",
            handled_intents=['example', 'test_workflow']
        )
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start the example workflow"""
        logger.info(f"Starting example workflow for user {user_id}")
        
        # Start the workflow
        state.start_workflow(self.workflow_name, {'step': 1})
        
        # Ask for name
        return self._ask_clarification(
            message="What's your name?",
            ui_elements=['text_input']
        )
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Process message in active workflow"""
        step = state.get_workflow_data('step', 1)
        
        if step == 1:
            # Got name, ask for age
            state.update_workflow_step('got_name', {'name': message, 'step': 2})
            
            return self._ask_clarification(
                message=f"Nice to meet you, {message}! How old are you?",
                ui_elements=['text_input']
            )
        
        elif step == 2:
            # Got age, complete
            name = state.get_workflow_data('name')
            
            return self._complete_workflow(
                message=f"Thanks {name}! You're {message} years old. Test complete!"
            )
        
        # Shouldn't reach here
        return self._complete_workflow(message="Test workflow completed.")
