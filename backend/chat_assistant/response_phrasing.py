# response_phrasing.py
# LLM-powered response phrasing for natural language

from typing import Dict, Any, Optional
from .llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

def phrase_response(template_key: str, context: Dict[str, Any] = None) -> str:
    """
    Generate natural language response using LLM or templates.
    
    Args:
        template_key: Type of response needed
        context: User and environment context
    
    Returns:
        Natural language response string
    """
    llm_service = get_llm_service()
    
    # Static templates as fallback
    templates = {
        'ask_mood_proactive': 'How are you feeling right now?',
        'ask_mood_reactive': 'How are you feeling right now?',
        'ask_reason': "What's contributing to this feeling?",
        'confirm_positive': 'Great! Your mood has been logged.',
        'confirm_negative': 'Got it. Your mood has been logged.',
        'unknown_intent': "I can help you log your mood. Just let me know how you're feeling.",
        'greeting': 'Hi! How can I help you today?',
        'continue': "Let me know when you're ready to continue.",
    }
    
    # For MVP, use templates
    # Can enhance with LLM later for more natural responses
    response = templates.get(template_key, templates['greeting'])
    
    # Optional: Use LLM for more natural phrasing (future enhancement)
    if llm_service.is_available() and context and template_key in ['confirm_positive', 'confirm_negative']:
        llm_response = _try_llm_phrasing(template_key, context, llm_service)
        if llm_response:
            return llm_response
    
    return response

def _try_llm_phrasing(template_key: str, context: Dict[str, Any], llm_service) -> Optional[str]:
    """
    Try to use LLM for more natural response phrasing.
    Falls back to template if LLM fails.
    """
    try:
        # Build prompt based on template type
        if template_key == 'confirm_positive':
            prompt = f"""Generate a brief, encouraging confirmation message for logging a positive mood.
Time: {context.get('time_period', 'day')}
Keep it under 15 words, friendly and supportive.
Example: "Awesome! Your mood has been logged. Keep up the positive energy!"
Response:"""
        
        elif template_key == 'confirm_negative':
            prompt = f"""Generate a brief, empathetic confirmation message for logging a negative mood.
Time: {context.get('time_period', 'day')}
Keep it under 15 words, supportive but not overly emotional.
Example: "Got it. Your mood has been logged. Take care of yourself."
Response:"""
        
        else:
            return None
        
        response = llm_service.call(prompt, max_tokens=30, temperature=0.7)
        
        if response and len(response) < 100:  # Sanity check
            logger.info(f"LLM phrased response: {response}")
            return response
            
    except Exception as e:
        logger.warning(f"LLM phrasing failed: {e}")
    
    return None
