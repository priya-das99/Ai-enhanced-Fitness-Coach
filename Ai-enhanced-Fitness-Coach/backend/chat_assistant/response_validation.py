# response_validation.py
# Validate LLM responses before sending to user

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Forbidden keywords (medical/therapeutic advice)
FORBIDDEN_KEYWORDS = [
    'diagnose', 'diagnosis', 'disorder', 'disease', 'medication',
    'prescribe', 'prescription', 'therapy', 'therapist', 'doctor',
    'medical', 'clinical', 'treatment', 'cure', 'symptom'
]

# Inappropriate phrases
INAPPROPRIATE_PHRASES = [
    'kill yourself', 'end it all', 'give up', 'hopeless',
    'you should', 'you must', 'you need to'
]

def validate_response(response: str, max_length: int = 200) -> tuple[bool, Optional[str]]:
    """
    Validate LLM response before sending to user.
    
    Args:
        response: The response text to validate
        max_length: Maximum allowed length
    
    Returns:
        (is_valid, error_reason)
    """
    if not response or not response.strip():
        return False, "empty_response"
    
    response_lower = response.lower()
    
    # Check length
    if len(response) > max_length:
        logger.warning(f"Response too long: {len(response)} chars")
        return False, "too_long"
    
    # Check for forbidden medical keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in response_lower:
            logger.warning(f"Forbidden keyword detected: {keyword}")
            return False, "medical_advice"
    
    # Check for inappropriate phrases
    for phrase in INAPPROPRIATE_PHRASES:
        if phrase in response_lower:
            logger.warning(f"Inappropriate phrase detected: {phrase}")
            return False, "inappropriate"
    
    # Check for multiple questions (should ask one thing at a time)
    question_marks = response.count('?')
    if question_marks > 1:
        logger.warning(f"Multiple questions detected: {question_marks}")
        return False, "multiple_questions"
    
    # Check for emotional manipulation
    manipulation_words = ['always', 'never', 'everyone', 'nobody', 'forever']
    manipulation_count = sum(1 for word in manipulation_words if word in response_lower)
    if manipulation_count >= 2:
        logger.warning(f"Potential emotional manipulation detected")
        return False, "manipulation"
    
    # All checks passed
    return True, None

def get_fallback_response(template_key: str) -> str:
    """
    Get safe fallback response if validation fails.
    """
    fallbacks = {
        'ask_mood': 'How are you feeling right now?',
        'ask_reason': "What's contributing to this feeling?",
        'confirm': 'Your mood has been logged.',
        'unknown': "I can help you log your mood.",
        'default': "Let me know how I can help you."
    }
    
    return fallbacks.get(template_key, fallbacks['default'])
