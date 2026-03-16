"""
Activity Logging Workflow Wrapper

Wraps the activity logging workflow to integrate with the chat engine
"""

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState
from .activity_logging_workflow import ActivityLoggingWorkflow
from .activity_extractor import ActivityExtractor
from app.core.database import get_db_connection
from app.services.activity_catalog_service import ActivityCatalogService
import logging

logger = logging.getLogger(__name__)


class ActivityLoggingWorkflowWrapper(BaseWorkflow):
    """Wrapper for activity logging workflow"""
    
    def __init__(self):
        super().__init__(
            workflow_name="exercise_logging",  # Different name to avoid conflict
            handled_intents=["log_exercise"]  # Only handle log_exercise
        )
        self.extractor = ActivityExtractor()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start activity logging workflow"""
        logger.info(f"[ActivityLogging] Starting workflow for user {user_id}")
        
        # Set this workflow as active
        state.start_workflow("exercise_logging")
        
        conn = get_db_connection()
        workflow = ActivityLoggingWorkflow(conn)
        catalog_service = ActivityCatalogService(conn)
        
        try:
            # Try to extract activity details from message
            extracted = self.extractor.extract_from_message(message)
            
            # If we have high confidence extraction, use it
            if extracted['confidence'] >= 0.8 and extracted.get('activity_id'):
                activity = catalog_service.get_activity_by_id(extracted['activity_id'])
                
                if activity:
                    # Build state from extracted data
                    workflow_state = {
                        'activity_id': extracted['activity_id'],
                        'activity_name': activity['name'],
                        'activity_icon': activity['icon'],
                        'activity_category': activity['category'],
                        'default_duration': activity['default_duration']
                    }
                    
                    # If we have date, proceed to date step
                    if extracted.get('date'):
                        response = workflow.select_date(user_id, extracted['date'], workflow_state)
                    else:
                        response = workflow.select_activity(user_id, extracted['activity_id'], workflow_state)
                    
                    # Store state
                    state.workflow_data = response.get('state', workflow_state)
                    
                    return self._create_response(
                        message=response['message'],
                        ui_elements=self._convert_buttons(response.get('buttons', [])),
                        completed=response.get('step') == 'complete'
                    )
            
            # Otherwise, start from category selection
            response = workflow.start_logging(user_id)
            
            return self._create_response(
                message=response['message'],
                ui_elements=self._convert_buttons(response.get('buttons', [])),
                completed=False
            )
            
        except Exception as e:
            logger.error(f"[ActivityLogging] Error starting workflow: {e}")
            return self._create_response(
                message="Sorry, I had trouble starting activity logging. Please try again.",
                completed=True
            )
        finally:
            conn.close()
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Process activity logging steps"""
        logger.info(f"[ActivityLogging] Processing message for user {user_id}")
        
        conn = get_db_connection()
        workflow = ActivityLoggingWorkflow(conn)
        
        try:
            # Get current workflow state
            workflow_state = state.workflow_data or {}
            current_step = workflow_state.get('step', 'select_category')
            
            # Handle awaiting custom date input
            if workflow_state.get('awaiting_custom_date'):
                response = workflow.handle_custom_date(user_id, message, workflow_state)
            
            # Handle awaiting custom time input
            elif workflow_state.get('awaiting_custom_time'):
                response = workflow.handle_custom_time(user_id, message, workflow_state)
            
            # Handle button actions
            elif message.startswith('log_activity_'):
                action_parts = message.split(':', 1)
                action = action_parts[0].replace('log_activity_', '')
                value = action_parts[1] if len(action_parts) > 1 else None
                
                if action == 'category':
                    response = workflow.select_category(user_id, value, workflow_state)
                elif action == 'select':
                    response = workflow.select_activity(user_id, value, workflow_state)
                elif action == 'date':
                    response = workflow.select_date(user_id, value, workflow_state)
                elif action == 'time':
                    response = workflow.select_time(user_id, value, workflow_state)
                elif action == 'duration':
                    if value == 'custom':
                        # Ask for custom duration
                        workflow_state['awaiting_custom_duration'] = True
                        state.workflow_data = workflow_state
                        return self._create_response(
                            message="Please enter the duration in minutes (e.g., '45' or '45 minutes'):",
                            completed=False
                        )
                    else:
                        duration = int(value)
                        response = workflow.select_duration(user_id, duration, workflow_state)
                else:
                    response = {'message': 'Unknown action', 'step': 'error'}
            
            # Handle custom duration input
            elif workflow_state.get('awaiting_custom_duration'):
                workflow_state.pop('awaiting_custom_duration', None)
                response = workflow.handle_custom_duration(user_id, message, workflow_state)
            
            # Handle cancel
            elif message.lower() in ['cancel', 'stop', 'nevermind']:
                response = workflow.cancel_logging(user_id)
            
            else:
                # Try to extract from natural language
                extracted = self.extractor.extract_from_message(message)
                
                if extracted['confidence'] >= 0.6:
                    # Continue workflow based on what we extracted
                    if extracted.get('duration') and workflow_state.get('start_time'):
                        response = workflow.select_duration(user_id, extracted['duration'], workflow_state)
                    else:
                        response = {'message': "I didn't quite understand. Please use the buttons or say 'cancel' to stop.", 'step': 'error'}
                else:
                    response = {'message': "I didn't quite understand. Please use the buttons or say 'cancel' to stop.", 'step': 'error'}
            
            # Store updated state
            state.workflow_data = response.get('state', workflow_state)
            
            return self._create_response(
                message=response['message'],
                ui_elements=self._convert_buttons(response.get('buttons', [])),
                completed=response.get('step') in ['complete', 'cancelled', 'error']
            )
            
        except Exception as e:
            logger.error(f"[ActivityLogging] Error processing: {e}")
            import traceback
            traceback.print_exc()
            return self._create_response(
                message="Sorry, something went wrong. Please try again.",
                completed=True
            )
        finally:
            conn.close()
    
    def _convert_buttons(self, buttons: list) -> list:
        """Convert workflow buttons to UI elements"""
        if not buttons:
            return []
        
        return [{
            'type': 'button',
            'text': btn['text'],
            'action': btn['action']
        } for btn in buttons]
