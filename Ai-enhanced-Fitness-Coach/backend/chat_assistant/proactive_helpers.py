# chat_assistant/proactive_helpers.py
# Helper functions for proactive chat features

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def add_proactive_mood_response(user_id: int, mood_emoji: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Add proactive elements to mood logging response:
    - Empathetic acknowledgment
    - Streak celebration
    - Offer help for negative moods
    - Follow-up questions
    
    Args:
        user_id: User ID
        mood_emoji: Mood emoji logged
        reason: Optional reason for mood
        
    Returns:
        Dict with message, buttons, and metadata
    """
    from app.services.streak_service import get_streak_service
    
    streak_service = get_streak_service()
    
    # Get current streak
    streak = streak_service.get_mood_logging_streak(user_id)
    
    # Build response
    response_parts = []
    buttons = []
    
    # 1. Empathetic acknowledgment
    if mood_emoji in ['😟', '😢', '😠', '😰', '😞']:
        # Negative mood
        response_parts.append(f"I'm sorry you're feeling {mood_emoji}")
        
        if reason:
            response_parts.append(f"{reason.capitalize()} can be really tough.")
        else:
            response_parts.append("That can be really hard.")
        
        response_parts.append("\nI've logged your mood.")
        
        # Offer help
        response_parts.append("\nWould you like some activity suggestions that might help?")
        
        buttons = [
            {'text': '✨ Yes, show me activities', 'action': 'get_suggestions', 'style': 'primary'},
            {'text': 'No, just logging', 'action': 'end_workflow', 'style': 'secondary'}
        ]
        
    elif mood_emoji in ['😊', '😄', '🎉', '😁', '🥰']:
        # Positive mood
        response_parts.append(f"That's wonderful to hear! {mood_emoji}")
        
        if reason:
            response_parts.append(f"I'm glad {reason} is going well!")
        
        response_parts.append("\nYour mood has been logged.")
        
    else:
        # Neutral mood
        response_parts.append(f"Thanks for sharing how you're feeling {mood_emoji}")
        response_parts.append("\nYour mood has been logged.")
    
    # 2. Streak celebration
    if streak > 0 and streak_service.should_celebrate_streak(user_id, 'mood_logging', streak):
        celebration = streak_service.get_celebration_message('mood_logging', streak)
        response_parts.append(f"\n\n{celebration}")
    elif streak >= 2:
        # Mention streak even if not celebrating
        response_parts.append(f"\n\n🔥 {streak}-day logging streak! Keep it up!")
    
    return {
        'message': ' '.join(response_parts),
        'buttons': buttons,
        'metadata': {
            'streak': streak,
            'mood_emoji': mood_emoji,
            'proactive': True
        }
    }


def add_activity_completion_response(user_id: int, activity_id: str, activity_name: str, 
                                     mood_before: str, completion_id: int = None) -> Dict[str, Any]:
    """
    Add proactive elements after activity completion:
    - Celebration
    - Ask for feedback
    - Show success rate
    - Streak celebration
    
    Args:
        user_id: User ID
        activity_id: Activity ID
        activity_name: Activity name
        mood_before: Mood before activity
        completion_id: Completion record ID
        
    Returns:
        Dict with message, buttons, and metadata
    """
    from app.services.streak_service import get_streak_service
    from app.services.activity_feedback_service import get_activity_feedback_service
    
    streak_service = get_streak_service()
    feedback_service = get_activity_feedback_service()
    
    # Get current streak
    streak = streak_service.get_activity_completion_streak(user_id)
    
    # Build response
    response_parts = []
    buttons = []
    
    # 1. Celebration
    response_parts.append(f"Great job completing {activity_name}! 🎉")
    
    # 2. Streak celebration
    if streak > 0 and streak_service.should_celebrate_streak(user_id, 'activity_completion', streak):
        celebration = streak_service.get_celebration_message('activity_completion', streak)
        response_parts.append(f"\n\n{celebration}")
    elif streak >= 2:
        response_parts.append(f"\n\n💪 {streak}-day activity streak!")
    
    # 3. Ask for feedback (not every time)
    should_ask = feedback_service.should_ask_for_feedback(user_id, activity_id)
    
    if should_ask:
        response_parts.append("\n\nHow do you feel now?")
        
        buttons = [
            {'text': '😊 Much better', 'action': 'feedback_helpful', 'data': {'helpful': True, 'mood_after': '😊'}},
            {'text': '😐 A little better', 'action': 'feedback_helpful', 'data': {'helpful': True, 'mood_after': '😐'}},
            {'text': '😟 About the same', 'action': 'feedback_not_helpful', 'data': {'helpful': False, 'mood_after': '😟'}},
            {'text': '😢 Worse', 'action': 'feedback_not_helpful', 'data': {'helpful': False, 'mood_after': '😢'}}
        ]
    else:
        # Show success rate if we have data
        success_rate = feedback_service.get_activity_success_rate(user_id, activity_id)
        
        if success_rate > 0:
            response_parts.append(f"\n\nThis activity has a {success_rate:.0f}% success rate for you!")
    
    return {
        'message': ' '.join(response_parts),
        'buttons': buttons,
        'metadata': {
            'streak': streak,
            'activity_id': activity_id,
            'completion_id': completion_id,
            'mood_before': mood_before,
            'proactive': True
        }
    }


def add_feedback_thank_you_response(user_id: int, activity_id: str, helpful: bool, 
                                    mood_after: str) -> Dict[str, Any]:
    """
    Thank user for feedback and provide insights
    
    Args:
        user_id: User ID
        activity_id: Activity ID
        helpful: Whether activity was helpful
        mood_after: Mood after activity
        
    Returns:
        Dict with message and metadata
    """
    from app.services.activity_feedback_service import get_activity_feedback_service
    
    feedback_service = get_activity_feedback_service()
    
    response_parts = []
    
    if helpful:
        if mood_after == '😊':
            response_parts.append("That's wonderful! I'm so glad it helped. 🌟")
        else:
            response_parts.append("I'm glad it helped a bit! 💙")
        
        # Get updated success rate
        success_rate = feedback_service.get_activity_success_rate(user_id, activity_id)
        
        if success_rate >= 80:
            response_parts.append(f"\n\nThis activity works really well for you ({success_rate:.0f}% success rate)!")
            response_parts.append("Want me to suggest this first next time?")
        elif success_rate >= 50:
            response_parts.append(f"\n\nThis activity has a {success_rate:.0f}% success rate for you.")
    else:
        if mood_after == '😢':
            response_parts.append("I'm sorry it didn't help. 😔")
            response_parts.append("\nLet's try something different next time.")
        else:
            response_parts.append("Thanks for letting me know.")
            response_parts.append("\nI'll remember this and suggest other activities next time.")
    
    return {
        'message': ' '.join(response_parts),
        'metadata': {
            'feedback_recorded': True,
            'helpful': helpful
        }
    }


def get_mood_emoji_sentiment(mood_emoji: str) -> str:
    """
    Get sentiment category for mood emoji
    
    Returns: 'positive', 'negative', or 'neutral'
    """
    positive_moods = ['😊', '😄', '🎉', '😁', '🥰', '😌', '🤗', '😍']
    negative_moods = ['😟', '😢', '😠', '😰', '😞', '😭', '😤', '😩', '😫']
    
    if mood_emoji in positive_moods:
        return 'positive'
    elif mood_emoji in negative_moods:
        return 'negative'
    else:
        return 'neutral'
