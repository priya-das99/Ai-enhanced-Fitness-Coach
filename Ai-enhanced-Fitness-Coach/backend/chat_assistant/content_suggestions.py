"""Content suggestions for wellness content (blogs, videos, podcasts)"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def get_content_suggestions(user_id: int, mood_emoji: str = None, reason: str = None, user_context: dict = None, count: int = 2) -> List[Dict]:
    """
    Get wellness content suggestions (blogs, videos, podcasts) based on:
    - Current mood and reason
    - User's past content interactions
    - User's activity preferences
    - Time of day and other contextual factors
    
    Args:
        user_id: User ID
        mood_emoji: Current mood emoji
        reason: Reason for mood (stress, work, anxiety, etc.)
        user_context: User context from context_builder (activity history, preferences, etc.)
        count: Number of content items to suggest
    
    Returns:
        List of formatted content suggestions for chat buttons
    """
    try:
        from app.services.content_service import ContentService
        
        content_service = ContentService()
        
        # Build mood context from mood and reason
        mood_context = _build_mood_context(mood_emoji, reason)
        
        # Get personalized content suggestions with user context
        content_items = content_service.get_content_suggestions(
            user_id=user_id,
            mood_context=mood_context,
            user_context=user_context,
            limit=count
        )
        
        if not content_items:
            logger.info(f"No content suggestions found for user {user_id}")
            return []
        
        # Format for chat display
        formatted = content_service.format_content_for_chat(content_items)
        
        logger.info(f"Generated {len(formatted)} personalized content suggestions for user {user_id}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error getting content suggestions: {e}")
        return []

def _build_mood_context(mood_emoji: str = None, reason: str = None) -> str:
    """Build context string from mood and reason"""
    context_parts = []
    
    # Map mood emojis to context
    mood_map = {
        '😊': 'happy positive',
        '😢': 'sad down',
        '😰': 'anxious stressed',
        '😡': 'angry frustrated',
        '😴': 'tired exhausted',
        '🤒': 'sick unwell',
        '😐': 'neutral okay'
    }
    
    if mood_emoji and mood_emoji in mood_map:
        context_parts.append(mood_map[mood_emoji])
    
    if reason:
        context_parts.append(reason)
    
    return ' '.join(context_parts)

def track_content_click(user_id: int, content_id: str):
    """Track when user clicks on content"""
    try:
        from app.services.content_service import ContentService
        
        # Extract numeric ID from content_id (format: "content_123")
        if content_id.startswith('content_'):
            numeric_id = int(content_id.replace('content_', ''))
            
            content_service = ContentService()
            content_service.track_content_interaction(
                user_id=user_id,
                content_id=numeric_id,
                interaction_type='viewed'
            )
            
            logger.info(f"Tracked content click: user={user_id}, content={numeric_id}")
        
    except Exception as e:
        logger.error(f"Error tracking content click: {e}")
