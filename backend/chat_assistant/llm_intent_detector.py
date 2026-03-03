# llm_intent_detector.py
# LLM-powered intent detection with fallback

from .llm_service import get_llm_service
from typing import Optional, List, Dict

def detect_intent(user_message: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """
    Detect user intent from message using LLM with optional conversation context.
    Falls back to keyword matching if LLM unavailable.
    
    Args:
        user_message: The current user message
        conversation_history: Optional list of previous messages for context
    
    Returns: 'log_mood', 'activity_query', 'challenge_query', 'activity_logging', or 'unknown'
    """
    llm_service = get_llm_service()
    
    # Try LLM first (with context if available)
    if llm_service.is_available():
        return llm_service.detect_intent(user_message, conversation_history)
    
    # Fallback to keyword matching
    return _keyword_intent_detection(user_message)

def _keyword_intent_detection(user_message: str) -> str:
    """Fallback keyword-based intent detection"""
    message_lower = user_message.lower()
    
    # Activity query keywords - check first (most specific)
    # These are explicit requests for activity suggestions
    activity_keywords = [
        'what activity', 'what can i do', 'suggest activity',
        'activities for', 'activity for', 'what should i do',
        'recommend activity', 'activities to', 'what to do',
        'suggest something', 'what would help'
    ]
    
    for keyword in activity_keywords:
        if keyword in message_lower:
            return 'activity_query'
    
    # "help me with X" or "help with X" where X is a problem (not a feeling)
    # This is tricky - if they say "help me with stress" it could be either
    # But if they say "help me with anxiety" followed by a question mark or "what", it's likely activity query
    if ('help me with' in message_lower or 'help with' in message_lower):
        # If it contains question words, it's likely asking for suggestions
        if any(word in message_lower for word in ['what', 'how', '?']):
            return 'activity_query'
    
    # Challenge query keywords
    challenge_keywords = [
        'challenge', 'challenges', 'my challenge', 'challenge progress',
        'start challenge', 'join challenge'
    ]
    
    for keyword in challenge_keywords:
        if keyword in message_lower:
            return 'challenge_query'
    
    # Mood-related keywords - expanded list
    mood_keywords = [
        'feel', 'feeling', 'mood', 'emotion', 'happy', 'sad',
        'anxious', 'stressed', 'great', 'terrible', 'okay',
        'good', 'bad', 'angry', 'worried', 'excited', 'tired',
        'depressed', 'nervous', 'calm', 'frustrated', 'down',
        'upset', 'joyful', 'content', 'overwhelmed', 'well',
        'unwell', 'sick', 'ill', 'awful', 'horrible', 'amazing',
        'fantastic', 'wonderful', 'miserable', 'lonely', 'scared',
        'afraid', 'confident', 'proud', 'ashamed', 'guilty',
        'relieved', 'hopeful', 'hopeless', 'energetic', 'exhausted',
        'bored', 'interested', 'confused', 'clear', 'motivated',
        'unmotivated', 'inspired', 'discouraged', 'peaceful',
        'restless', 'comfortable', 'uncomfortable', 'safe', 'unsafe'
    ]
    
    # Mood phrases - common expressions
    mood_phrases = [
        'not feeling', 'feeling like', 'i feel', "i'm feeling",
        'i am', "i'm not", 'i am not', 'having a', 'been feeling',
        'log mood', 'track mood', 'record mood', 'check in',
        'how i feel', 'my mood', 'today i', 'right now i'
    ]
    
    # Check for mood phrases first (more specific)
    for phrase in mood_phrases:
        if phrase in message_lower:
            return 'log_mood'
    
    # Check for mood keywords
    for keyword in mood_keywords:
        if keyword in message_lower:
            return 'log_mood'
    
    # Default to unknown
    return 'unknown'
