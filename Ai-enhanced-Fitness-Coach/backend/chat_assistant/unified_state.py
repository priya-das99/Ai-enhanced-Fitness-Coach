# unified_state.py
# Unified conversation state model for workflow engine

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import threading
from .session_summary import SessionSummary
from .conversation_depth_tracker import ConversationDepthTracker

logger = logging.getLogger(__name__)

"""
PRECEDENCE ORDER (highest to lowest):
1. Workflow state (active_workflow, workflow_data) - ALWAYS WINS
2. Explicit user input (current message)
3. Session summary (semantic memory)
4. Conversation buffer (recent evidence)

If these conflict, higher precedence wins.
"""

class ConversationState(Enum):
    """Universal conversation states"""
    IDLE = "idle"
    WORKFLOW_ACTIVE = "workflow_active"
    CLARIFICATION_PENDING = "clarification_pending"
    ACTION_CONFIRMATION_PENDING = "action_confirmation_pending"

class WorkflowState:
    """Represents the current workflow execution state"""
    
    # Comprehensive activity-to-topic mapping for depth reset
    ACTIVITY_TO_TOPIC = {
        # Breathing & Meditation
        "breathing_exercise": "breathing",
        "box_breathing": "breathing",
        "pranayama": "breathing",
        "meditation": "meditation",
        "guided_meditation": "meditation",
        "mindfulness": "meditation",
        
        # Sleep
        "sleep_log": "sleep",
        "bedtime_routine": "sleep",
        "sleep_tracking": "sleep",
        
        # Exercise
        "workout": "exercise",
        "quick_workout": "exercise",
        "cardio": "exercise",
        "stretching": "exercise",
        "yoga": "exercise",
        "strength_training": "exercise",
        
        # Hydration
        "water_log": "hydration",
        "hydration_tracking": "hydration",
        
        # Nutrition
        "meal_log": "nutrition",
        "food_tracking": "nutrition",
        
        # Stress & Energy
        "stress_relief": "stress",
        "relaxation": "stress",
        "energy_boost": "energy"
    }
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self._lock = threading.Lock()  # Thread-safe state mutations
        self.state = ConversationState.IDLE
        self.active_workflow: Optional[str] = None
        self.workflow_data: Dict[str, Any] = {}
        self.workflow_step: Optional[str] = None
        self.last_updated = datetime.now()
        self.conversation_history: List[Dict[str, str]] = []  # Raw messages (evidence)
        self.session_summary = SessionSummary(user_id)  # Semantic memory (meaning)
        
        # Depth tracker per user session (MVP: session-only, no persistence)
        self.depth_tracker = ConversationDepthTracker()
        
        # Global rejection tracking (works across ALL workflows)
        self.global_rejection_count = 0
        self.last_rejection_time = None
        
        # TODO (Post-MVP): Consider persistence options:
        # - Daily reset (new day = fresh counters)
        # - Cross-session persistence (store in DB)
        # - Time-based decay (depth decreases over time)
    
    def start_workflow(self, workflow_name: str, initial_data: Dict[str, Any] = None):
        """Start a new workflow (thread-safe)"""
        with self._lock:
            if self.active_workflow:
                logger.warning(f"User {self.user_id}: Attempted to start {workflow_name} while {self.active_workflow} is active")
                raise ValueError(f"Cannot start {workflow_name}: {self.active_workflow} is already active")
            
            self.state = ConversationState.WORKFLOW_ACTIVE
            self.active_workflow = workflow_name
            self.workflow_data = initial_data or {}
            
            # Track workflow start time for timeout detection
            self.workflow_data['last_activity_time'] = datetime.now().isoformat()
            self.workflow_step = None
            self.last_updated = datetime.now()
            
            logger.info(f"User {self.user_id}: Started workflow '{workflow_name}'")
    
    def update_workflow_step(self, step: str, data: Dict[str, Any] = None):
        """Update current workflow step (thread-safe)"""
        with self._lock:
            if not self.active_workflow:
                raise ValueError("No active workflow to update")
            
            self.workflow_step = step
            self.workflow_data['step'] = step  # Also update in workflow_data
            if data:
                self.workflow_data.update(data)
            self.last_updated = datetime.now()
            
            logger.info(f"User {self.user_id}: Workflow '{self.active_workflow}' -> step '{step}'")
    
    def set_state(self, state: ConversationState):
        """Update conversation state (thread-safe)"""
        with self._lock:
            old_state = self.state
            self.state = state
            self.last_updated = datetime.now()
            
            logger.info(f"User {self.user_id}: State transition {old_state.value} -> {state.value}")
    
    def complete_workflow(self):
        """Complete and reset workflow (thread-safe)"""
        with self._lock:
            workflow_name = self.active_workflow
            self.state = ConversationState.IDLE
            self.active_workflow = None
            self.workflow_data = {}
            self.workflow_step = None
            self.last_updated = datetime.now()
            # Keep conversation history for context (limit to last 10 messages)
            self.conversation_history = self.conversation_history[-10:]
            
            logger.info(f"User {self.user_id}: Completed workflow '{workflow_name}'")
    
    def get_workflow_data(self, key: str, default=None):
        """Get workflow data by key (thread-safe read)"""
        with self._lock:
            return self.workflow_data.get(key, default)
    
    def set_workflow_data(self, key: str, value):
        """Set workflow data by key (thread-safe)"""
        with self._lock:
            self.workflow_data[key] = value
            self.last_updated = datetime.now()
            logger.info(f"User {self.user_id}: Set workflow data '{key}' = {value}")
    
    def is_idle(self) -> bool:
        """Check if in IDLE state (thread-safe read)"""
        with self._lock:
            return self.state == ConversationState.IDLE
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history (thread-safe)"""
        with self._lock:
            self.conversation_history.append({
                'role': role,
                'content': content
            })
            # Keep only last 20 messages (10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            self.last_updated = datetime.now()
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history (thread-safe read)"""
        with self._lock:
            return self.conversation_history[-limit:]
    
    def clear_conversation_history(self):
        """Clear conversation history (thread-safe)"""
        with self._lock:
            self.conversation_history = []
            logger.info(f"User {self.user_id}: Cleared conversation history")
    
    def reset_on_logout(self):
        """Reset state on user logout (thread-safe)"""
        # Note: complete_workflow and clear_conversation_history already have locks
        self.complete_workflow()
        self.clear_conversation_history()
        logger.info(f"User {self.user_id}: Reset state on logout")
    
    def on_activity_completed(self, activity_type: str):
        """
        Reset depth when user completes activity (thread-safe).
        Handles partial matches and variations.
        """
        with self._lock:
            # Direct match
            topic = self.ACTIVITY_TO_TOPIC.get(activity_type)
            
            # Partial match fallback
            if not topic:
                activity_lower = activity_type.lower()
                for act_type, topic_name in self.ACTIVITY_TO_TOPIC.items():
                    if act_type in activity_lower or activity_lower in act_type:
                        topic = topic_name
                        break
            
            # Reset if topic found
            if topic:
                self.depth_tracker.reset_topic(topic)
                logger.info(f"User {self.user_id}: Activity '{activity_type}' → Topic '{topic}' depth reset")
            else:
                logger.debug(f"User {self.user_id}: Activity '{activity_type}' has no topic mapping")
    
    def get_depth_tracker(self) -> ConversationDepthTracker:
        """Get user's depth tracker (thread-safe read)"""
        with self._lock:
            return self.depth_tracker
    
    def track_rejection(self):
        """Track a rejection (works across all workflows, thread-safe)"""
        from datetime import datetime, timedelta
        
        with self._lock:
            # Reset counter if last rejection was more than 5 minutes ago
            if self.last_rejection_time:
                time_since_last = datetime.now() - self.last_rejection_time
                if time_since_last > timedelta(minutes=5):
                    self.global_rejection_count = 0
                    logger.info(f"User {self.user_id}: Reset rejection count (timeout)")
            
            self.global_rejection_count += 1
            self.last_rejection_time = datetime.now()
            logger.info(f"User {self.user_id}: Rejection count = {self.global_rejection_count}")
    
    def get_rejection_count(self) -> int:
        """Get current rejection count (thread-safe read)"""
        with self._lock:
            return self.global_rejection_count
    
    def reset_rejection_count(self):
        """Reset rejection counter (thread-safe)"""
        with self._lock:
            self.global_rejection_count = 0
            self.last_rejection_time = None
            logger.info(f"User {self.user_id}: Reset rejection count")
    
    def should_stop_suggesting(self) -> bool:
        """Check if we should stop suggesting based on rejection count (thread-safe read)"""
        with self._lock:
            return self.global_rejection_count >= 2
    
    def is_workflow_stale(self, timeout_minutes: int = 5) -> bool:
        """
        Check if workflow has been inactive too long (thread-safe read)
        
        Args:
            timeout_minutes: Minutes of inactivity before workflow is considered stale
            
        Returns:
            True if workflow should be timed out
        """
        with self._lock:
            if not self.active_workflow:
                return False
                
            last_activity_str = self.workflow_data.get('last_activity_time')
            if not last_activity_str:
                # No activity time recorded - assume stale
                return True
                
            try:
                last_activity = datetime.fromisoformat(last_activity_str)
                elapsed = datetime.now() - last_activity
                is_stale = elapsed.total_seconds() > (timeout_minutes * 60)
                
                if is_stale:
                    logger.info(f"User {self.user_id}: Workflow '{self.active_workflow}' is stale ({elapsed.total_seconds():.0f}s)")
                
                return is_stale
                
            except (ValueError, TypeError) as e:
                logger.warning(f"User {self.user_id}: Invalid last_activity_time format: {e}")
                return True  # Assume stale if we can't parse the time
    
    def update_activity_time(self):
        """Update the last activity time for timeout tracking (thread-safe)"""
        with self._lock:
            self.workflow_data['last_activity_time'] = datetime.now().isoformat()
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (thread-safe read)"""
        with self._lock:
            return {
                'user_id': self.user_id,
                'state': self.state.value,
                'active_workflow': self.active_workflow,
                'workflow_data': self.workflow_data.copy(),  # Copy to prevent external mutation
                'workflow_step': self.workflow_step,
                'last_updated': self.last_updated.isoformat(),
                'conversation_history': self.conversation_history.copy(),  # Copy to prevent external mutation
                'global_rejection_count': self.global_rejection_count
            }

# In-memory state storage (per user)
_user_states: Dict[int, WorkflowState] = {}

def get_workflow_state(user_id: int) -> WorkflowState:
    """Get or create workflow state for user"""
    if user_id not in _user_states:
        _user_states[user_id] = WorkflowState(user_id)
    return _user_states[user_id]

def reset_workflow_state(user_id: int):
    """Reset user's workflow state"""
    if user_id in _user_states:
        _user_states[user_id].complete_workflow()
        logger.info(f"User {user_id}: Workflow state reset")
