# chat_assistant/response_validator.py
# Validates workflow responses match the expected contract

import logging
from typing import Dict, Any, List
from .workflow_base import WorkflowResponse
from .unified_state import ConversationState

logger = logging.getLogger(__name__)

class ResponseValidator:
    """
    Validates workflow responses to ensure they match the expected contract.
    
    Contract Requirements:
    - message: str (required)
    - ui_elements: list (optional, default [])
    - completed: bool (required)
    - next_state: ConversationState (optional)
    - events: list (optional, default [])
    - ui_type: str (optional)
    - metadata: dict (optional, default {})
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, raises exceptions on validation failures.
                        If False, only logs warnings.
        """
        self.strict_mode = strict_mode
        self.validation_errors: List[str] = []
    
    def validate(self, response: WorkflowResponse, workflow_name: str) -> bool:
        """
        Validate a workflow response.
        
        Args:
            response: WorkflowResponse to validate
            workflow_name: Name of workflow that generated response
            
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []
        
        # Check required fields
        if not self._validate_message(response):
            self._log_error(workflow_name, "Missing or invalid 'message' field")
        
        if not self._validate_completed(response):
            self._log_error(workflow_name, "Missing or invalid 'completed' field")
        
        # Check optional fields have correct types
        if not self._validate_ui_elements(response):
            self._log_error(workflow_name, "Invalid 'ui_elements' field (must be list)")
        
        if not self._validate_next_state(response):
            self._log_error(workflow_name, "Invalid 'next_state' field (must be ConversationState)")
        
        if not self._validate_events(response):
            self._log_error(workflow_name, "Invalid 'events' field (must be list)")
        
        if not self._validate_metadata(response):
            self._log_error(workflow_name, "Invalid 'metadata' field (must be dict)")
        
        # Check logical consistency
        if not self._validate_consistency(response):
            self._log_error(workflow_name, "Logical inconsistency in response")
        
        is_valid = len(self.validation_errors) == 0
        
        if not is_valid:
            if self.strict_mode:
                raise ValueError(f"Validation failed for {workflow_name}: {self.validation_errors}")
            else:
                logger.warning(f"Validation warnings for {workflow_name}: {self.validation_errors}")
        
        return is_valid
    
    def _validate_message(self, response: WorkflowResponse) -> bool:
        """Validate message field"""
        if not hasattr(response, 'message'):
            return False
        if not isinstance(response.message, str):
            return False
        if len(response.message.strip()) == 0:
            return False
        return True
    
    def _validate_completed(self, response: WorkflowResponse) -> bool:
        """Validate completed field"""
        if not hasattr(response, 'completed'):
            return False
        if not isinstance(response.completed, bool):
            return False
        return True
    
    def _validate_ui_elements(self, response: WorkflowResponse) -> bool:
        """Validate ui_elements field"""
        if not hasattr(response, 'ui_elements'):
            return True  # Optional field
        if response.ui_elements is None:
            return True
        if not isinstance(response.ui_elements, list):
            return False
        return True
    
    def _validate_next_state(self, response: WorkflowResponse) -> bool:
        """Validate next_state field"""
        if not hasattr(response, 'next_state'):
            return True  # Optional field
        if response.next_state is None:
            return True
        if not isinstance(response.next_state, ConversationState):
            return False
        return True
    
    def _validate_events(self, response: WorkflowResponse) -> bool:
        """Validate events field"""
        if not hasattr(response, 'events'):
            return True  # Optional field
        if response.events is None:
            return True
        if not isinstance(response.events, list):
            return False
        # Validate each event is a dict
        for event in response.events:
            if not isinstance(event, dict):
                return False
        return True
    
    def _validate_metadata(self, response: WorkflowResponse) -> bool:
        """Validate metadata field"""
        if not hasattr(response, 'metadata'):
            return True  # Optional field
        if response.metadata is None:
            return True
        if not isinstance(response.metadata, dict):
            return False
        return True
    
    def _validate_consistency(self, response: WorkflowResponse) -> bool:
        """Validate logical consistency"""
        # If completed=True, next_state should be IDLE or None
        if response.completed:
            if response.next_state and response.next_state != ConversationState.IDLE:
                self.validation_errors.append(
                    "completed=True but next_state is not IDLE"
                )
                return False
        
        # If completed=False, should have next_state
        if not response.completed:
            if not response.next_state or response.next_state == ConversationState.IDLE:
                self.validation_errors.append(
                    "completed=False but next_state is IDLE or None"
                )
                return False
        
        return True
    
    def _log_error(self, workflow_name: str, error: str):
        """Log validation error"""
        full_error = f"[{workflow_name}] {error}"
        self.validation_errors.append(full_error)
        logger.warning(f"Validation error: {full_error}")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report"""
        return {
            'is_valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'error_count': len(self.validation_errors)
        }


# Global validator instance
_validator = None

def get_response_validator(strict_mode: bool = False) -> ResponseValidator:
    """Get or create global ResponseValidator instance"""
    global _validator
    if _validator is None:
        _validator = ResponseValidator(strict_mode=strict_mode)
    return _validator


def validate_response(response: WorkflowResponse, workflow_name: str, strict: bool = False) -> bool:
    """
    Convenience function to validate a workflow response.
    
    Args:
        response: WorkflowResponse to validate
        workflow_name: Name of workflow
        strict: If True, raises exception on validation failure
        
    Returns:
        True if valid, False otherwise
    """
    validator = get_response_validator(strict_mode=strict)
    return validator.validate(response, workflow_name)
