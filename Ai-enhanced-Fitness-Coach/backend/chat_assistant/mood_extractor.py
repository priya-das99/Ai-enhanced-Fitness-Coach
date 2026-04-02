# mood_extractor.py
# Extract mood level from natural language

from .llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

# Mood mapping: text sentiment -> emoji
MOOD_MAP = {
    'awesome': '😄',
    'great': '😄',
    'amazing': '😄',
    'fantastic': '😄',
    'wonderful': '😄',
    'excellent': '😄',
    'happy': '😄',
    'joyful': '😄',
    'excited': '😄',
    
    'good': '😊',
    'fine': '😊',
    'okay': '😊',
    'alright': '😊',
    'decent': '😊',
    'pretty good': '😊',
    
    'ok': '😐',
    'meh': '😐',
    'so-so': '😐',
    'neutral': '😐',
    'average': '😐',
    'bored': '😐',
    
    'not good': '😟',
    'bad': '😟',
    'stress': '😟',
    'stressed': '😟',
    'stresses': '😟',
    'anxious': '😟',
    'worried': '😟',
    'upset': '😟',
    'tired': '😟',
    'sleepy': '😟',
    'exhausted': '😟',
    'frustrated': '😟',
    'not well': '😟',
    'unwell': '😟',
    'sick': '😟',
    
    'horrible': '😢',
    'terrible': '😢',
    'awful': '😢',
    'miserable': '😢',
    'depressed': '😢',
    'devastated': '😢',
    'hopeless': '😢'
}

def extract_mood_from_message(message: str) -> tuple:
    """
    Extract mood emoji from natural language message.
    
    Returns: (mood_emoji, confidence)
        - mood_emoji: str (e.g., '😟') or None if can't determine
        - confidence: 'high' or 'low'
    """
    
    # CRITICAL FIX: Don't extract mood from intent-only phrases
    # These phrases express desire to log, not actual mood
    intent_only_phrases = [
        'i want to log mood',
        'i want to log my mood',
        'i want to log_mood',  # Handle underscore version
        'log mood',
        'log my mood',
        'log_mood',  # Handle underscore version
        'track mood',
        'track my mood',
        'record mood',
        'record my mood',
        'can i log mood',
        'how do i log mood',
        'let me log mood'
    ]
    
    # Normalize message: lowercase and replace underscores with spaces
    message_lower = message.lower().strip().replace('_', ' ')
    for phrase in intent_only_phrases:
        if phrase in message_lower:
            logger.info(f"🚫 Skipping mood extraction - intent-only phrase detected: '{message}'")
            return None, 'low'
    
    llm_service = get_llm_service()
    
    # Try LLM first for better accuracy (handles typos and variations)
    if llm_service.is_available():
        try:
            mood_emoji = _extract_with_llm(message, llm_service)
            if mood_emoji:
                logger.info(f"🤖 LLM extracted mood: {mood_emoji} from '{message}'")
                return mood_emoji, 'high'
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to keywords")
    else:
        logger.info("LLM not available, using keyword extraction")
    
    # Fallback to keyword matching
    mood_emoji = _extract_with_keywords(message)
    if mood_emoji:
        logger.info(f"📝 Keyword extracted mood: {mood_emoji} from '{message}'")
        return mood_emoji, 'low'
    
    logger.warning(f"Could not extract mood from: '{message}'")
    return None, 'low'

def _extract_with_llm(message: str, llm_service) -> str:
    """Use LLM to extract mood from message"""
    prompt = f"""You are a mood detection AI. Extract the mood level from the user's message.

User said: "{message}"

Respond with ONLY ONE of these emojis based on the sentiment:
- 😄 (Awesome) - Very positive, excited, happy, great
- 😊 (Pretty Good) - Positive, good, fine
- 😐 (Ok) - Neutral, okay, so-so
- 😟 (Not Good) - Negative, stressed, anxious, not well, tired, sick
- 😢 (Horrible) - Very negative, terrible, awful, depressed

Examples:
"I am not feeling well" → 😟
"I feel great today" → 😄
"I'm stressed about work" → 😟
"I'm so happy!" → 😄
"I feel terrible" → 😢
"I'm okay" → 😐

Mood emoji:"""
    
    try:
        response = llm_service.call(prompt, max_tokens=20, temperature=0.1)
        
        if response:
            # Extract emoji from response
            for emoji in ['😄', '😊', '😐', '😟', '😢']:
                if emoji in response:
                    return emoji
        
        return None
        
    except Exception as e:
        logger.error(f"LLM mood extraction failed: {e}")
        return None

def _extract_with_keywords(message: str) -> str:
    """Fallback keyword-based mood extraction with fuzzy matching"""
    message_lower = message.lower()
    
    # Check for negative indicators first (more specific)
    # These need to be checked before positive keywords
    negative_phrases = [
        'not feeling well', 'not feeling good', 'feeling not good',
        'not well', 'feeling terrible', 'feeling awful',
        'feeling horrible', 'feeling sick', 'feeling unwell',
        'not good', 'feeling bad', 'not great', 'not okay',
        'not fine', 'not happy', 'feeling down', 'feeling sad'
    ]
    
    for phrase in negative_phrases:
        if phrase in message_lower:
            if 'terrible' in phrase or 'awful' in phrase or 'horrible' in phrase:
                return '😢'
            return '😟'
    
    # Check for "not" + positive word patterns
    if 'not' in message_lower:
        positive_words = ['good', 'great', 'fine', 'okay', 'well', 'happy', 'awesome']
        for word in positive_words:
            if word in message_lower:
                return '😟'
    
    # Check mood keywords with fuzzy matching (handles typos like "stresses" → "stressed")
    for keyword, emoji in MOOD_MAP.items():
        # Exact match
        if keyword in message_lower:
            return emoji
        
        # Fuzzy match for common variations (stress/stressed/stresses)
        if len(keyword) > 4:  # Only for longer words
            # Check if keyword is a substring or vice versa
            if keyword in message_lower or any(keyword in word for word in message_lower.split()):
                return emoji
            # Check for word stems (stress → stressed, stresses)
            keyword_stem = keyword[:min(5, len(keyword)-1)]
            if keyword_stem in message_lower:
                return emoji
    
    # Check for general negative words
    negative_words = ['stressed', 'stress', 'stresses', 'anxious', 'worried', 'sad', 'down', 
                     'upset', 'frustrated', 'angry', 'tired', 'exhausted', 'hurt', 'disappointed']
    for word in negative_words:
        if word in message_lower:
            return '😟'
    
    # Check for general positive words
    positive_words = ['happy', 'excited', 'joyful', 'proud', 'confident']
    for word in positive_words:
        if word in message_lower:
            return '😄'
    
    return None
