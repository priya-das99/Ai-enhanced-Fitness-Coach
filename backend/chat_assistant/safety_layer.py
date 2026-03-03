# safety_layer.py
# Safety filter for spam, abuse, and invalid messages

import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class SafetyFilter:
    """Pre-processing safety layer"""
    
    # Abusive/offensive patterns (basic list - expand as needed)
    ABUSIVE_PATTERNS = [
        r'\b(fuck|shit|damn|bitch|asshole|bastard)\b',
        r'\b(idiot|stupid|dumb|moron)\b',
        # Add more patterns as needed
    ]
    
    # Spam patterns
    SPAM_PATTERNS = [
        r'^(.)\1{10,}$',  # Repeated characters (aaaaaaaaaa)
        r'^[!@#$%^&*()]{5,}$',  # Only special characters
    ]
    
    SAFE_RESPONSE = "I'm here to help with your fitness activities."
    
    @staticmethod
    def check_message(message: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message is safe to process
        
        Returns:
            (is_safe, reason)
            - is_safe: True if message passes safety checks
            - reason: None if safe, otherwise reason for rejection
        """
        if not message or not message.strip():
            logger.warning("Safety: Empty message detected")
            return False, "empty_message"
        
        message_lower = message.lower().strip()
        
        # Check length
        if len(message) > 500:
            logger.warning(f"Safety: Message too long ({len(message)} chars)")
            return False, "message_too_long"
        
        # Check for abusive language
        for pattern in SafetyFilter.ABUSIVE_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"Safety: Abusive language detected")
                return False, "abusive_language"
        
        # Check for spam
        for pattern in SafetyFilter.SPAM_PATTERNS:
            if re.search(pattern, message):
                logger.warning(f"Safety: Spam pattern detected")
                return False, "spam"
        
        # Message is safe
        return True, None
    
    @staticmethod
    def get_safe_response() -> str:
        """Get standard safe response"""
        return SafetyFilter.SAFE_RESPONSE

def filter_message(message: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Filter message through safety layer
    
    Returns:
        (is_safe, rejection_reason, safe_response)
    """
    is_safe, reason = SafetyFilter.check_message(message)
    
    if not is_safe:
        return False, reason, SafetyFilter.get_safe_response()
    
    return True, None, None
