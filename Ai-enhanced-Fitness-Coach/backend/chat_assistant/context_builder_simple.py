# context_builder_simple.py
# Build context for LLM from user data and environment

from datetime import datetime
from typing import Dict, Any
from .mood_handler import get_user_mood_logs
from .user_history import get_activity_stats, get_recent_activities

def build_context(user_id: str) -> Dict[str, Any]:
    """
    Build rich context for LLM from user data and current environment.
    This provides safe, relevant information for better suggestions.
    """
    now = datetime.now()
    
    context = {
        # Time context
        'hour': now.hour,
        'day_of_week': now.strftime("%A"),
        'is_weekend': now.weekday() >= 5,
        'is_work_hours': 9 <= now.hour <= 17,
        'time_period': _get_time_period(now.hour),
        
        # User context
        'user_id': user_id,
        'has_mood_history': False,
        'recent_mood_trend': None,
        
        # Activity history context (NEW!)
        'has_activity_history': False,
        'favorite_activities': [],
        'recent_activities': [],
        'time_preferences': {},
        'day_preferences': {},
        'reason_preferences': {}
    }
    
    # Get recent mood history (last 3 days)
    try:
        recent_moods = get_user_mood_logs(user_id, limit=10)
        if recent_moods:
            context['has_mood_history'] = True
            context['recent_mood_count'] = len(recent_moods)
            
            # Calculate trend (simplified)
            if len(recent_moods) >= 2:
                recent_values = [log['mood_value'] for log in recent_moods[:3]]
                avg_recent = sum(recent_values) / len(recent_values)
                
                if avg_recent >= 4:
                    context['recent_mood_trend'] = 'positive'
                elif avg_recent <= 2:
                    context['recent_mood_trend'] = 'negative'
                else:
                    context['recent_mood_trend'] = 'neutral'
    except Exception as e:
        # Don't fail if mood history unavailable
        pass
    
    # Get activity history and preferences (NEW!)
    try:
        stats = get_activity_stats(user_id, days=30)
        
        if stats['activity_counts']:
            context['has_activity_history'] = True
            
            # Top 3 favorite activities
            sorted_activities = sorted(
                stats['activity_counts'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            context['favorite_activities'] = [
                {'id': act_id, 'name': act_data['name'], 'count': act_data['count']}
                for act_id, act_data in sorted_activities[:3]
            ]
            
            # Time preferences
            context['time_preferences'] = stats['time_preferences']
            
            # Day preferences
            context['day_preferences'] = stats['day_preferences']
            
            # Reason preferences
            context['reason_preferences'] = stats['reason_preferences']
        
        # Recent activities
        recent = get_recent_activities(user_id, limit=5)
        context['recent_activities'] = recent
        
    except Exception as e:
        # Don't fail if activity history unavailable
        pass
    
    return context

def _get_time_period(hour: int) -> str:
    """Categorize time of day"""
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"
