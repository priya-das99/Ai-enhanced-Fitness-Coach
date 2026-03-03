# mood_categories.py
# Categorize moods for appropriate response handling

from typing import Tuple

# Mood categories with handling strategy
MOOD_CATEGORIES = {
    # Positive moods - quick acknowledgment
    'positive': {
        'emojis': ['😄', '😊'],
        'keywords': ['happy', 'great', 'awesome', 'excited', 'good', 'wonderful', 
                    'fantastic', 'amazing', 'joyful', 'excellent', 'energetic'],
        'ask_reason': False,
        'suggest_activities': False,
        'response_type': 'celebrate'
    },
    
    # Mild negative - physical/temporary (skip reason, suggest quick fixes)
    'mild_physical': {
        'emojis': ['😐'],
        'keywords': ['tired', 'sleepy', 'exhausted', 'bored', 'restless', 
                    'hungry', 'thirsty', 'drowsy', 'sluggish', 'fatigued',
                    'drained', 'weary', 'lethargic'],
        'ask_reason': False,
        'suggest_activities': True,
        'response_type': 'quick_fix',
        'activity_types': ['power_nap', 'stretch', 'walk', 'water', 'snack']
    },
    
    # Emotional negative - need context
    'emotional_negative': {
        'emojis': ['😟'],
        'keywords': ['stressed', 'stress', 'stresses', 'anxious', 'worried', 
                    'frustrated', 'upset', 'angry', 'nervous', 'overwhelmed', 
                    'tense', 'irritated', 'annoyed', 'disappointed', 'confused',
                    'sad', 'down', 'unhappy', 'lonely', 'hurt', 'bothered'],
        'ask_reason': True,
        'suggest_activities': True,
        'response_type': 'empathetic',
        'activity_types': ['meditation', 'breathing', 'walk', 'talk', 'journal']
    },
    
    # Severe negative - need support
    'severe_negative': {
        'emojis': ['😢'],
        'keywords': ['depressed', 'terrible', 'awful', 'hopeless', 'devastated',
                    'miserable', 'horrible', 'desperate', 'worthless'],
        'ask_reason': True,
        'suggest_activities': True,
        'response_type': 'supportive',
        'activity_types': ['talk_to_someone', 'professional_help', 'breathing', 'meditation']
    },
    
    # Neutral - acknowledge
    'neutral': {
        'emojis': ['😐'],
        'keywords': ['okay', 'ok', 'meh', 'so-so', 'neutral', 'fine', 'alright', 'average'],
        'ask_reason': False,
        'suggest_activities': False,
        'response_type': 'acknowledge'
    }
}

def categorize_mood(mood_emoji: str = None, mood_text: str = None) -> Tuple[str, dict]:
    """
    Categorize a mood to determine appropriate response
    
    Args:
        mood_emoji: Mood emoji (😄, 😊, 😐, 😟, 😢)
        mood_text: Text description of mood (e.g., "tired", "stressed")
    
    Returns:
        (category_name, category_config)
    """
    # Check by keyword FIRST (more specific than emoji)
    if mood_text:
        text_lower = mood_text.lower()
        
        # Check for negations that would flip positive keywords
        has_negation = any(neg in text_lower for neg in ['not', "n't", 'no ', 'never', 'hardly', 'barely'])
        
        for category_name, config in MOOD_CATEGORIES.items():
            # Skip positive category if there's a negation
            if category_name == 'positive' and has_negation:
                continue
                
            for keyword in config['keywords']:
                if keyword in text_lower:
                    return category_name, config
    
    # Check by emoji if no keyword match
    if mood_emoji:
        for category_name, config in MOOD_CATEGORIES.items():
            if mood_emoji in config['emojis']:
                return category_name, config
    
    # Default to emotional_negative if can't determine
    return 'emotional_negative', MOOD_CATEGORIES['emotional_negative']

def should_ask_reason(mood_emoji: str = None, mood_text: str = None) -> bool:
    """Determine if we should ask for reason based on mood"""
    category_name, config = categorize_mood(mood_emoji, mood_text)
    return config['ask_reason']

def get_response_type(mood_emoji: str = None, mood_text: str = None) -> str:
    """Get the response type for this mood"""
    category_name, config = categorize_mood(mood_emoji, mood_text)
    return config['response_type']

def get_suggested_activity_types(mood_emoji: str = None, mood_text: str = None) -> list:
    """Get recommended activity types for this mood"""
    category_name, config = categorize_mood(mood_emoji, mood_text)
    return config.get('activity_types', [])
