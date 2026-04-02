"""
Mood and Reason Extractor
Extracts both mood and reason from a single user message using LLM
"""
from .llm_service import get_llm_service, LLMUnavailableError, LLMAPIError
import logging

logger = logging.getLogger(__name__)

llm_service = get_llm_service()


def extract_mood_and_reason(message: str) -> dict:
    """
    Extract both mood and reason from a user message.
    
    Examples:
    - "I am stressed about my presentation" → mood: 😟, reason: "presentation"
    - "I'm worried about my health" → mood: 😟, reason: "health"
    - "Feeling anxious about work" → mood: 😰, reason: "work"
    
    Returns:
        {
            'mood_emoji': str or None,
            'reason': str or None,
            'confidence': 'high' or 'low'
        }
    """
    if not llm_service.is_available():
        logger.warning("[Mood+Reason Extractor] LLM not available")
        return {'mood_emoji': None, 'reason': None, 'confidence': 'low'}
    
    try:
        prompt = f"""Extract the mood and reason from this message.

User said: "{message}"

Mood emojis:
- 😄 = Awesome/Great/Excellent
- 😊 = Pretty Good/Happy/Fine
- 😐 = Okay/Neutral/Meh
- 😟 = Not Good/Stressed/Worried/Anxious
- 😢 = Horrible/Terrible/Very Bad

Reason: What is causing this feeling? (work, presentation, health, relationship, etc.)

Respond ONLY with valid JSON (no markdown, no code blocks):
{{"mood_emoji": "emoji", "reason": "short reason", "has_both": true/false}}

If the message doesn't express a clear mood or reason, set has_both to false."""

        logger.info(f"[Mood+Reason Extractor] Extracting from: '{message}'")
        
        result = llm_service.call_structured(
            prompt=prompt,
            json_schema={
                "type": "object",
                "properties": {
                    "mood_emoji": {"type": "string"},
                    "reason": {"type": "string"},
                    "has_both": {"type": "boolean"}
                },
                "required": ["mood_emoji", "reason", "has_both"],
                "additionalProperties": False
            },
            schema_name="mood_reason_extraction",
            temperature=0.2,
            max_tokens=50
        )
        
        mood_emoji = result.get('mood_emoji', '').strip()
        reason = result.get('reason', '').strip()
        has_both = result.get('has_both', False)
        
        # Validate mood emoji
        valid_moods = ['😄', '😊', '🙂', '😐', '😟', '😢']
        if mood_emoji not in valid_moods:
            mood_emoji = None
        
        # Clean up reason
        if reason and reason.lower() in ['none', 'unknown', 'n/a', '']:
            reason = None
        
        confidence = 'high' if has_both else 'low'
        
        logger.info(f"[Mood+Reason Extractor] Result: mood={mood_emoji}, reason={reason}, confidence={confidence}")
        
        return {
            'mood_emoji': mood_emoji,
            'reason': reason,
            'confidence': confidence
        }
        
    except (LLMUnavailableError, LLMAPIError) as e:
        logger.error(f"[Mood+Reason Extractor] LLM error: {e}")
        return {'mood_emoji': None, 'reason': None, 'confidence': 'low'}
    except Exception as e:
        logger.error(f"[Mood+Reason Extractor] Unexpected error: {e}")
        return {'mood_emoji': None, 'reason': None, 'confidence': 'low'}
