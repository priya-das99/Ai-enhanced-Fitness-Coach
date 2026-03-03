"""
Context detection for selective history passing.
Only uses context when message genuinely requires it.

Design Principles:
- Context must be EARNED, not defaulted
- Strict rules prevent token waste
- Structured state over text extraction
"""

from typing import Optional
from .unified_state import WorkflowState


# Acknowledgment phrases that don't need context
ACKNOWLEDGMENTS = {
    "thanks", "thank you", "ok", "okay", "got it", "cool", 
    "nice", "great", "awesome", "perfect", "sure", "alright",
    "yes", "no", "yep", "nope", "yeah", "nah"
}

# Question indicators
# NOTE: Broad list includes "is", "do", "can" which appear in non-questions
# Safe because we check has_question in context with other patterns
# DO NOT loosen the combined checks without testing
QUESTION_INDICATORS = [
    "?", "how", "what", "when", "where", "why", "who", "which", 
    "can", "should", "is", "does", "do", "will", "would", "could"
]


def needs_conversation_context(message: str, state: WorkflowState) -> bool:
    """
    Determine if message needs conversation history.
    
    MVP MODE: Always pass context for better user experience.
    This ensures the bot never loses context during demos.
    
    Can be optimized later for token efficiency.
    """
    
    message_lower = message.lower().strip()
    # Remove punctuation for word matching
    import string
    words_clean = message_lower.translate(str.maketrans('', '', string.punctuation)).split()
    words = message_lower.split()  # Keep for other checks
    
    # 0. Empty messages don't need context
    if len(words_clean) == 0:
        return False
    
    # MVP: Always pass context for better understanding
    # Exception: Very simple greetings don't need history
    simple_greetings = ['hi', 'hello', 'hey']
    if len(words_clean) == 1 and words_clean[0] in simple_greetings:
        return False
    
    # MVP: Pass context for everything else
    return True


def get_recent_topic_from_state(state: WorkflowState) -> Optional[str]:
    """
    Get recent topic from STRUCTURED state, not text extraction.
    
    Sources (in priority order):
    1. Active workflow name
    2. Depth tracker (most discussed topic)
    3. Semantic summary focus
    
    This avoids NLP extraction and potential hallucination.
    """
    
    # 1. Check active workflow
    if state.active_workflow:
        return state.active_workflow
    
    # 2. Check depth tracker (knows current topics)
    if hasattr(state, 'depth_tracker'):
        # Get topic with highest count (most recent discussion)
        if state.depth_tracker.topic_info_responses:
            topics = state.depth_tracker.topic_info_responses
            recent_topic = max(topics.items(), key=lambda x: x[1])[0]
            return recent_topic
    
    # 3. Check semantic summary
    if state.session_summary and state.session_summary.current_focus:
        return state.session_summary.current_focus
    
    return None
