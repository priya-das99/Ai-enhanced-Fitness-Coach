# workflow_registry.py
# Central registry for all workflows
# Phase 1 Refactoring: Intent-based routing instead of priority-based

from typing import List, Optional
from .workflow_base import BaseWorkflow
from .unified_state import WorkflowState
import logging

logger = logging.getLogger(__name__)

class WorkflowRegistry:
    """
    Central registry for managing workflows
    
    Phase 1 Refactoring: Intent-based routing instead of priority-based
    """
    
    def __init__(self):
        self._workflows: List[BaseWorkflow] = []
        self._intent_to_workflow: dict = {}  # NEW: Intent → Workflow mapping
        self.workflows = {}  # workflow_name → workflow instance
        self.intent_to_workflow = {}  # intent → workflow_name
        self._auto_register_workflows()
    
    def _auto_register_workflows(self):
        """Auto-register all available workflows"""
        # Re-enabled: ActivityWorkflow handles water, sleep, weight, meal logging
        try:
            from .activity_workflow import ActivityWorkflow
            self.register(ActivityWorkflow())
            logger.info("Auto-registered ActivityWorkflow")
        except Exception as e:
            logger.warning(f"Could not register ActivityWorkflow: {e}")
        
        # New: ActivityLoggingWorkflowWrapper handles exercise logging with categories
        try:
            from .activity_logging_workflow_wrapper import ActivityLoggingWorkflowWrapper
            self.register(ActivityLoggingWorkflowWrapper())
            logger.info("Auto-registered ActivityLoggingWorkflowWrapper")
        except Exception as e:
            logger.warning(f"Could not register ActivityLoggingWorkflowWrapper: {e}")
        
        try:
            from .mood_workflow import MoodWorkflow
            mood_wf = MoodWorkflow()
            self.register(mood_wf)
            logger.info("Auto-registered MoodWorkflow")
        except Exception as e:
            logger.warning(f"Could not register MoodWorkflow: {e}")
        
        try:
            from .challenges_workflow import ChallengesWorkflow
            self.register(ChallengesWorkflow())
            logger.info("Auto-registered ChallengesWorkflow")
        except Exception as e:
            logger.warning(f"Could not register ChallengesWorkflow: {e}")
        
        try:
            from .example_workflow import ExampleWorkflow
            self.register(ExampleWorkflow())
            logger.info("Auto-registered ExampleWorkflow")
        except Exception as e:
            logger.warning(f"Could not register ExampleWorkflow: {e}")
        
        try:
            from .activity_query_workflow import ActivityQueryWorkflow
            self.register(ActivityQueryWorkflow())
            logger.info("Auto-registered ActivityQueryWorkflow")
        except Exception as e:
            logger.warning(f"Could not register ActivityQueryWorkflow: {e}")
        
        try:
            from .activity_summary_workflow import ActivitySummaryWorkflow
            self.register(ActivitySummaryWorkflow())
            logger.info("Auto-registered ActivitySummaryWorkflow")
        except Exception as e:
            logger.warning(f"Could not register ActivitySummaryWorkflow: {e}")
        
        try:
            from .general_workflow import GeneralWorkflow
            self.register(GeneralWorkflow())
            logger.info("Auto-registered GeneralWorkflow")
        except Exception as e:
            logger.warning(f"Could not register GeneralWorkflow: {e}")
    
    def register(self, workflow: BaseWorkflow):
        """Register a workflow"""
        self._workflows.append(workflow)
        self.workflows[workflow.workflow_name] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_name}")
        
        # Register intent mappings
        for intent in workflow.get_handled_intents():
            self._intent_to_workflow[intent] = workflow
            self.intent_to_workflow[intent] = workflow.workflow_name
            logger.info(f"  → Handles intent: {intent}")
    
    def _build_intent_mapping(self):
        """Build intent → workflow mapping from registered workflows (DEPRECATED - now done in register())"""
        # This method is no longer needed as mappings are built during registration
        pass
    
    def get_workflow_for_intent(self, intent: str) -> Optional[BaseWorkflow]:
        """
        Get workflow that handles the given intent
        
        Args:
            intent: Intent string from LLM (e.g., 'mood_logging')
            
        Returns:
            Workflow instance or None
        """
        workflow_name = self.intent_to_workflow.get(intent)
        if workflow_name:
            workflow = self.workflows.get(workflow_name)
            return workflow
        else:
            logger.warning(f"No workflow registered for intent: {intent}")
            return None
    
    def find_workflow(self, message: str, state: WorkflowState) -> Optional[BaseWorkflow]:
        """
        DEPRECATED: Use get_workflow_for_intent() instead
        
        This method is kept for backward compatibility during Phase 1 transition.
        Intent detection should be done by LLM, not by workflows.
        
        Args:
            message: User's message
            state: Current workflow state
            
        Returns:
            Workflow instance or None
        """
        logger.warning("find_workflow() is deprecated. Use get_workflow_for_intent() instead.")
        
        # If a workflow is active, return that workflow
        if state.active_workflow:
            for workflow in self._workflows:
                if workflow.workflow_name == state.active_workflow:
                    logger.info(f"Continuing active workflow: {workflow.workflow_name}")
                    return workflow
            
            logger.warning(f"Active workflow '{state.active_workflow}' not found in registry!")
            return None
        
        return None
    
    def get_workflow_by_name(self, name: str) -> Optional[BaseWorkflow]:
        """Get workflow by name"""
        for workflow in self._workflows:
            if workflow.workflow_name == name:
                return workflow
        return None
    
    def list_workflows(self) -> List[str]:
        """List all registered workflows"""
        return [w.workflow_name for w in self._workflows]
    
    def get_workflows_by_priority(self) -> List[BaseWorkflow]:
        """DEPRECATED: Get all workflows (priority no longer used)"""
        logger.warning("get_workflows_by_priority() is deprecated")
        return self._workflows.copy()
    
    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """Get workflow by name (alias for get_workflow_by_name)"""
        return self.get_workflow_by_name(name)
    
    def get_intent_mappings(self) -> dict:
        """Get all intent → workflow mappings"""
        return self._intent_to_workflow.copy()

# Global registry instance
_registry = WorkflowRegistry()

def get_registry() -> WorkflowRegistry:
    """Get the global workflow registry"""
    return _registry

def register_workflow(workflow: BaseWorkflow):
    """Register a workflow in the global registry"""
    _registry.register(workflow)
