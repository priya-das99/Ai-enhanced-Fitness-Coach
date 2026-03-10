# universal_context_handler.py
# Universal context system that works across all workflows

from typing import Optional, Dict, Any
from .unified_state import WorkflowState
from .session_summary import SessionFocus
import logging

logger = logging.getLogger(__name__)

class UniversalContextHandler:
    """
    Handles follow-up requests across all workflows using session summary.
    
    Examples:
    - After mood logging: "I want to change my mood"
    - After challenge query: "I want to complete that challenge"  
    - After activity logging: "I want to log more"
    - Cross-workflow: "Show my water progress" → "I want to log more"
    """
    
    def __init__(self):
        self.follow_up_patterns = {
            # Activity-related follow-ups
            'log_more': ['log more', 'add more', 'more', 'another', 'again', 'log another'],
            'change_mood': ['change my mood', 'update mood', 'different mood', 'log mood again'],
            'complete_challenge': ['complete', 'do that', 'start that', 'try that'],
            'show_progress': ['my progress', 'how am i doing', 'show my', 'check my'],
            'cancel': ['cancel', 'stop', 'never mind', 'forget it', 'no thanks']
        }
    
    def can_handle_followup(self, message: str, state: WorkflowState) -> bool:
        """
        Check if this message is a follow-up to recent activity.
        
        Uses session summary + LLM for natural language understanding.
        """
        # Check if we have recent focus
        state.session_summary.clear_if_stale()
        current_focus = state.session_summary.current_focus
        
        if not current_focus:
            return False
        
        # Quick keyword check first (fast path)
        message_lower = message.lower().strip()
        
        for pattern_type, patterns in self.follow_up_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                logger.info(f"Detected follow-up pattern '{pattern_type}' with focus '{current_focus}' (keyword match)")
                return True
        
        # If no keyword match, use LLM for natural understanding
        return self._llm_detect_followup(message, current_focus, state)
    
    def _llm_detect_followup(self, message: str, current_focus: str, state: WorkflowState) -> bool:
        """
        Use LLM to detect if message is a follow-up request.
        
        This handles natural language variations that keywords miss.
        """
        try:
            from .llm_service import get_llm_service
            llm = get_llm_service()
            
            # Build context for LLM
            focus_context = {
                'hydration': 'water logging',
                'mood': 'mood logging', 
                'sleep': 'sleep tracking',
                'exercise': 'exercise logging',
                'weight': 'weight tracking'
            }.get(current_focus, current_focus)
            
            # Get recent conversation for context
            recent_messages = state.get_conversation_history(limit=3)
            conversation_context = ""
            if recent_messages:
                conversation_context = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in recent_messages[-2:]  # Last 2 messages
                ])
            
            # Structured prompt for follow-up detection
            prompt = f"""Analyze if the user wants to continue/follow-up on their recent {focus_context} activity.

Recent conversation:
{conversation_context}

Current user message: "{message}"

The user was recently focused on: {focus_context}

Is this message a follow-up request to continue the same activity?

Follow-up indicators:
- Wants to log/add/record MORE of the same thing
- Wants to UPDATE/CHANGE the same activity  
- References "additional", "more", "another", "extra"
- Uses words like "also", "too", "as well"
- Wants to modify/correct what they just logged

Examples of FOLLOW-UPS:
- "I want to log more" → YES
- "Can I add some more water?" → YES  
- "Let me record additional glasses" → YES
- "I'd like to update that" → YES
- "Could I log some additional water?" → YES
- "I need to add another entry" → YES
- "Actually, I'm feeling different now" → YES (mood change)

Examples of NEW TOPICS:
- "What's the weather?" → NO
- "How are you?" → NO
- "Show my challenges" → NO (unless asking about progress)
- "I want to log sleep" → NO (different activity)

Respond with exactly:
intent=followup|new_topic
confidence=0.85"""

            response = llm.call(
                prompt=prompt,
                system_message="You are an expert at detecting user intent in conversation context.",
                max_tokens=30,
                temperature=0.1
            )
            
            # Parse structured response
            try:
                lines = response.strip().split('\n')
                intent_line = [l for l in lines if l.startswith('intent=')][0]
                conf_line = [l for l in lines if l.startswith('confidence=')][0]
                
                intent = intent_line.split('=')[1].strip()
                confidence = float(conf_line.split('=')[1].strip())
                
                is_followup = confidence > 0.7 and intent == "followup"
                
                if is_followup:
                    logger.info(f"LLM detected follow-up: intent={intent}, confidence={confidence}")
                else:
                    logger.info(f"LLM detected new topic: intent={intent}, confidence={confidence}")
                
                return is_followup
                
            except (IndexError, ValueError) as e:
                logger.warning(f"Failed to parse LLM follow-up response: {e}")
                return False
            
        except Exception as e:
            logger.warning(f"LLM follow-up detection failed: {e}")
            return False
    
    def handle_followup(self, message: str, state: WorkflowState, user_id: int):
        """
        Handle follow-up request based on session context.
        
        Uses LLM to understand natural language variations.
        Returns appropriate workflow response or None if can't handle.
        """
        current_focus = state.session_summary.current_focus
        message_lower = message.lower().strip()
        
        # First try keyword matching (fast path)
        followup_type = self._detect_followup_type_keywords(message_lower)
        
        # If no keyword match, use LLM for natural understanding
        if not followup_type:
            followup_type = self._llm_detect_followup_type(message, current_focus, state)
        
        if not followup_type:
            return None
        
        logger.info(f"Handling follow-up type '{followup_type}' for focus '{current_focus}'")
        
        # Route to appropriate handler based on focus and type
        if current_focus == SessionFocus.HYDRATION:
            return self._handle_hydration_followup_typed(followup_type, message, state, user_id)
        
        elif current_focus == SessionFocus.MOOD:
            return self._handle_mood_followup_typed(followup_type, message, state, user_id)
        
        elif current_focus == SessionFocus.SLEEP:
            return self._handle_sleep_followup_typed(followup_type, message, state, user_id)
        
        elif current_focus == SessionFocus.EXERCISE:
            return self._handle_exercise_followup_typed(followup_type, message, state, user_id)
        
        elif current_focus == SessionFocus.WEIGHT:
            return self._handle_weight_followup_typed(followup_type, message, state, user_id)
        
        return None
    
    def _detect_followup_type_keywords(self, message_lower: str) -> str:
        """Fast keyword-based follow-up type detection"""
        for pattern_type, patterns in self.follow_up_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return pattern_type
        return None
    
    def _llm_detect_followup_type(self, message: str, current_focus: str, state: WorkflowState) -> str:
        """Use LLM to detect specific follow-up intent type"""
        try:
            from .llm_service import get_llm_service
            llm = get_llm_service()
            
            focus_context = {
                'hydration': 'water logging',
                'mood': 'mood logging', 
                'sleep': 'sleep tracking',
                'exercise': 'exercise logging',
                'weight': 'weight tracking'
            }.get(current_focus, current_focus)
            
            prompt = f"""The user was recently doing {focus_context}. Classify their follow-up request:

User message: "{message}"

Follow-up types:
- log_more: wants to log/add/record more of the same activity (water, sleep, exercise, etc.)
- change_mood: wants to change/update/modify their mood  
- show_progress: wants to see their progress/status/how they're doing
- complete_challenge: wants to complete/start/do a challenge/activity
- cancel: wants to cancel/stop/forget about something

Key phrases for log_more:
- "more", "additional", "another", "extra", "add", "record", "log"
- "I'd like to add", "Can I log", "Let me record"

Examples:
- "I want to log more water" → log_more
- "Can I add some more?" → log_more
- "Let me record additional glasses" → log_more
- "I'd like to add some more water" → log_more
- "Could I log some additional water?" → log_more
- "I'd like to update my mood" → change_mood
- "I want to change my mood" → change_mood
- "How am I doing?" → show_progress
- "Show my progress" → show_progress
- "Let's do that challenge" → complete_challenge
- "Cancel this" → cancel

Respond with exactly:
type=log_more
confidence=0.90"""

            response = llm.call(
                prompt=prompt,
                system_message="You classify user follow-up intents accurately.",
                max_tokens=20,
                temperature=0.1
            )
            
            # Parse response
            try:
                lines = response.strip().split('\n')
                type_line = [l for l in lines if l.startswith('type=')][0]
                conf_line = [l for l in lines if l.startswith('confidence=')][0]
                
                followup_type = type_line.split('=')[1].strip()
                confidence = float(conf_line.split('=')[1].strip())
                
                if confidence > 0.7:
                    logger.info(f"LLM detected follow-up type: {followup_type} (confidence: {confidence})")
                    return followup_type
                else:
                    logger.info(f"LLM confidence too low: {confidence}")
                    return None
                
            except (IndexError, ValueError) as e:
                logger.warning(f"Failed to parse LLM follow-up type: {e}")
                return None
            
        except Exception as e:
            logger.warning(f"LLM follow-up type detection failed: {e}")
            return None
    
    def _handle_hydration_followup_typed(self, followup_type: str, message: str, state: WorkflowState, user_id: int):
        """Handle water-related follow-ups with typed intent"""
        if followup_type == 'log_more':
            # User wants to log more water
            from .activity_workflow import ActivityWorkflow
            activity_workflow = ActivityWorkflow()
            
            # Start water logging workflow
            state.start_workflow('activity_logging', {
                'activity_type': 'water',
                'unit': state.session_summary.preferences.get('water_unit', 'glasses'),
                'notes': f'Follow-up: {message}'
            })
            
            return activity_workflow._ask_clarification(
                message="How many more glasses of water?",
                ui_elements=['text_input']
            )
        
        elif followup_type == 'show_progress':
            # User wants to see water progress
            from .challenges_workflow import ChallengesWorkflow
            challenges_workflow = ChallengesWorkflow()
            return challenges_workflow.start("show my water progress", state, user_id)
        
        return None
    
    def _handle_mood_followup_typed(self, followup_type: str, message: str, state: WorkflowState, user_id: int):
        """Handle mood-related follow-ups with typed intent"""
        if followup_type == 'change_mood' or followup_type == 'log_more':
            # User wants to change/update their mood
            from .mood_workflow import MoodWorkflow
            mood_workflow = MoodWorkflow()
            return mood_workflow.start("log mood again", state, user_id)
        
        return None
    
    def _handle_sleep_followup_typed(self, followup_type: str, message: str, state: WorkflowState, user_id: int):
        """Handle sleep-related follow-ups with typed intent"""
        if followup_type == 'log_more':
            # User wants to log more sleep (update sleep)
            from .activity_workflow import ActivityWorkflow
            activity_workflow = ActivityWorkflow()
            
            state.start_workflow('activity_logging', {
                'activity_type': 'sleep',
                'unit': state.session_summary.preferences.get('sleep_unit', 'hours'),
                'notes': f'Follow-up: {message}'
            })
            
            return activity_workflow._ask_clarification(
                message="How many hours did you sleep?",
                ui_elements=['text_input']
            )
        
        return None
    
    def _handle_exercise_followup_typed(self, followup_type: str, message: str, state: WorkflowState, user_id: int):
        """Handle exercise-related follow-ups with typed intent"""
        if followup_type == 'log_more':
            # User wants to log more exercise
            from .activity_workflow import ActivityWorkflow
            activity_workflow = ActivityWorkflow()
            
            state.start_workflow('activity_logging', {
                'activity_type': 'exercise',
                'unit': 'minutes',
                'notes': f'Follow-up: {message}'
            })
            
            return activity_workflow._ask_clarification(
                message="How many more minutes did you exercise?",
                ui_elements=['text_input']
            )
        
        return None
    
    def _handle_weight_followup_typed(self, followup_type: str, message: str, state: WorkflowState, user_id: int):
        """Handle weight-related follow-ups with typed intent"""
        if followup_type == 'log_more':
            # User wants to update weight
            from .activity_workflow import ActivityWorkflow
            activity_workflow = ActivityWorkflow()
            
            state.start_workflow('activity_logging', {
                'activity_type': 'weight',
                'unit': 'kg',
                'notes': f'Follow-up: {message}'
            })
            
            return activity_workflow._ask_clarification(
                message="What's your current weight?",
                ui_elements=['text_input']
            )
        
        return None


# Global instance
_universal_context_handler = None

def get_universal_context_handler() -> UniversalContextHandler:
    """Get or create global UniversalContextHandler instance"""
    global _universal_context_handler
    if _universal_context_handler is None:
        _universal_context_handler = UniversalContextHandler()
    return _universal_context_handler