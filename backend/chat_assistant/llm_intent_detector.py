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
    """Fallback keyword-based intent detection - SIMPLIFIED for natural conversation"""
    message_lower = user_message.lower()
    
    # Only detect EXPLICIT logging requests
    # Let general chat handle conversational mentions
    
    # Explicit mood logging
    if any(phrase in message_lower for phrase in ['log mood', 'track mood', 'record mood', 'log my mood']):
        return 'log_mood'
    
    # Explicit activity logging
    if any(phrase in message_lower for phrase in ['log workout', 'log activity', 'log exercise', 'track workout']):
        return 'activity_logging'
    
    # Challenge queries
    challenge_keywords = [
        'start challenge', 'join challenge', 'my challenge', 'challenge progress'
    ]
    for keyword in challenge_keywords:
        if keyword in message_lower:
            return 'challenge_query'
    
    # Activity suggestions (explicit requests only)
    activity_keywords = [
        'suggest workout', 'recommend workout', 'what workout',
        'suggest exercise', 'recommend exercise', 'what exercise'
    ]
    for keyword in activity_keywords:
        if keyword in message_lower:
            return 'activity_query'
    
    # Default to general chat - let LLM handle it naturally
    return 'unknown'
