# action_suggestions.py
# Suggest wellness actions based on mood and reason
# Now uses database instead of hardcoded actions

from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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

def get_quick_actions_from_db() -> List[Dict]:
    """Get quick action activities from database"""
    try:
        from app.core.database import get_db
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT id, name, description, default_duration, icon, best_for
                FROM activity_catalog
                WHERE quick_action = 1 AND active = 1
                ORDER BY name
            """)
            
            actions = []
            for row in cursor.fetchall():
                actions.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'duration': f"{row[3]} min",
                    'icon': row[4],
                    'best_for': row[5].split(',') if row[5] else [],
                    'effort': 'low'  # Default for quick actions
                })
            
            return actions
    
    except Exception as e:
        logger.error(f"Error fetching quick actions from database: {e}")
        # Fallback to empty list
        return []

def suggest_action(mood_emoji: str, reason: str, context: Dict) -> Optional[Dict]:
    """
    Suggest wellness action based on mood, reason, and context.
    Now fetches from database instead of hardcoded actions.
    """
    # Determine if mood is negative
    negative_moods = ['😟', '😢', '😠', '😰', '😞', '😭', '😤', '😔']
    is_negative = mood_emoji in negative_moods
    
    # If positive mood, no suggestion needed
    if not is_negative:
        return None
    
    # Get quick actions from database
    quick_actions = get_quick_actions_from_db()
    
    if not quick_actions:
        logger.warning("No quick actions found in database")
        return None
    
    # Get time context
    hour = context.get('hour', datetime.now().hour)
    is_work_hours = 9 <= hour <= 17
    time_period = context.get('time_period', 'day')
    
    # Build search criteria
    search_terms = []
    
    # Add reason-based terms
    if reason:
        reason_lower = reason.lower()
        search_terms.append(reason_lower)
        
        # Add related terms
        if 'work' in reason_lower:
            search_terms.extend(['work', 'stress'])
        elif any(word in reason_lower for word in ['relationship', 'family', 'friend']):
            search_terms.extend(['relationship', 'family'])
        elif 'education' in reason_lower:
            search_terms.extend(['education', 'study'])
    
    # Add time-based terms
    search_terms.append(time_period)
    
    # Find best matching action
    best_action = None
    best_score = 0
    
    for action in quick_actions:
        score = 0
        best_for = action.get('best_for', [])
        
        # Calculate match score
        for term in search_terms:
            if any(term in bf for bf in best_for):
                score += 1
        
        # Prefer work-friendly actions during work hours
        if is_work_hours and action['id'] in ['breathing', 'take_break']:
            score += 1
        
        if score > best_score:
            best_score = score
            best_action = action
    
    # If no good match, use first action as fallback
    if not best_action and quick_actions:
        best_action = quick_actions[0]
    
    if best_action:
        logger.info(f"Suggested action: {best_action['id']} for mood {mood_emoji}, reason: {reason}")
        return best_action
    
    return None
