# action_suggestions.py
# Suggest wellness actions based on mood and reason

from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Predefined wellness actions
WELLNESS_ACTIONS = {
    "breathing": {
        "id": "breathing",
        "name": "Breathing Exercise",
        "description": "Quick breathing exercises",
        "duration": "3-5 min",
        "effort": "low"
    },
    "meditation": {
        "id": "meditation",
        "name": "Meditation",
        "description": "Mindfulness or meditation",
        "duration": "5-10 min",
        "effort": "low"
    },
    "stretching": {
        "id": "stretching",
        "name": "Stretching",
        "description": "Gentle stretches",
        "duration": "5-10 min",
        "effort": "low"
    },
    "short_walk": {
        "id": "short_walk",
        "name": "Short Walk",
        "description": "Brief walk or movement",
        "duration": "10-15 min",
        "effort": "medium"
    },
    "take_break": {
        "id": "take_break",
        "name": "Take a Break",
        "description": "Step away from current activity",
        "duration": "5 min",
        "effort": "low"
    },
    "listen_to_music": {
        "id": "listen_to_music",
        "name": "Listen to Music",
        "description": "Relaxing music to calm your mind",
        "duration": "10-15 min",
        "effort": "low",
        "url": "https://youtu.be/uwEaQk5VeS4?si=81cpsJQScEinmIop"
    }
}

# Predefined mood reasons
MOOD_REASONS = [
    {"id": "work", "label": "Work"},
    {"id": "family", "label": "Family"},
    {"id": "relationship", "label": "Relationship"},
    {"id": "education", "label": "Education"},
    {"id": "food", "label": "Food"},
    {"id": "travel", "label": "Travel"},
    {"id": "friend", "label": "Friend"},
    {"id": "exercise", "label": "Exercise"},
    {"id": "other", "label": "Other"}
]

def get_mood_reasons():
    """Get list of predefined mood reasons"""
    return MOOD_REASONS

def suggest_action(mood_emoji: str, reason: str, context: Dict) -> Optional[Dict]:
    """
    Suggest wellness action based on mood, reason, and context.
    Uses rule-based logic for deterministic suggestions.
    """
    # Determine if mood is negative
    negative_moods = [ '😟', '😢']
    is_negative = mood_emoji in negative_moods
    
    # If positive mood, no suggestion needed
    if not is_negative:
        return None
    
    # Get time context
    hour = context.get('hour', datetime.now().hour)
    is_work_hours = 9 <= hour <= 17
    time_period = context.get('time_period', 'day')
    
    # Rule-based suggestion logic
    suggestion_id = None
    
    # Work-related stress
    if reason and 'work' in reason.lower():
        if is_work_hours:
            suggestion_id = 'breathing'  # Quick, work-friendly
        else:
            suggestion_id = 'short_walk'  # After work, get moving
    
    # Relationship/family stress
    elif reason and any(word in reason.lower() for word in ['relationship', 'family', 'friend']):
        suggestion_id = 'meditation'  # Calming
    
    # Education/study stress
    elif reason and 'education' in reason.lower():
        suggestion_id = 'take_break'  # Need a break from studying
    
    # Exercise-related
    elif reason and 'exercise' in reason.lower():
        suggestion_id = 'stretching'  # Gentle recovery
    
    # Food-related
    elif reason and 'food' in reason.lower():
        suggestion_id = 'short_walk'  # Help digestion
    
    # Travel stress
    elif reason and 'travel' in reason.lower():
        suggestion_id = 'breathing'  # Quick stress relief
    
    # Default based on time of day
    else:
        if time_period == 'morning':
            suggestion_id = 'stretching'
        elif time_period == 'afternoon':
            suggestion_id = 'take_break'
        elif time_period == 'evening':
            suggestion_id = 'meditation'
        else:  # night
            suggestion_id = 'breathing'
    
    # Return action details
    if suggestion_id and suggestion_id in WELLNESS_ACTIONS:
        action = WELLNESS_ACTIONS[suggestion_id].copy()
        logger.info(f"Suggested action: {suggestion_id} for mood {mood_emoji}, reason: {reason}")
        return action
    
    return None
