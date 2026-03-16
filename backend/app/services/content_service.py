"""
Content Service - Database layer for wellness activities
Provides standardized activity data for suggestion engine
"""
import sqlite3
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection"""
    return sqlite3.connect('backend/mood_capture.db')

# Mood to category mapping for fallback
MOOD_TO_CATEGORY_MAP = {
    # Negative/Stress
    'stressed': ['mindfulness', 'relaxation', 'yoga'],
    'anxious': ['mindfulness', 'relaxation'],
    'overwhelmed': ['mindfulness', 'relaxation'],
    'angry': ['exercise', 'yoga', 'mindfulness'],
    'sad': ['mindfulness', 'relaxation'],
    
    # Engagement/Boredom
    'bored': ['yoga', 'mindfulness', 'exercise'],
    'restless': ['exercise', 'yoga'],
    'lonely': ['mindfulness', 'relaxation'],
    
    # Physical
    'tired': ['mindfulness', 'relaxation'],
    'energetic': ['exercise', 'yoga'],
    'sleepy': ['relaxation', 'mindfulness'],
    
    # Positive
    'happy': ['exercise', 'yoga', 'mindfulness'],
    'excited': ['exercise', 'yoga'],
    'calm': ['mindfulness', 'yoga'],
}

def get_activities_for_mood(mood: str, limit: int = 10) -> List[Dict]:
    """
    Query database for activities matching mood/state
    Returns standardized format for ranking engine
    
    Args:
        mood: User's mood/state ('bored', 'stressed', etc.)
        limit: Max activities to return
    
    Returns:
        List of activities in standardized format:
        [
            {
                "id": int,
                "title": str,
                "description": str,
                "duration_minutes": int,
                "category": str,
                "difficulty_level": str,
                "tags": list,
                "source": "database"
            }
        ]
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Step 1: Try direct mood match in best_for field
        cursor.execute('''
            SELECT 
                ci.id,
                ci.title,
                ci.description,
                ci.duration_minutes,
                cc.slug as category,
                ci.difficulty_level,
                ci.tags,
                ci.content_url,
                ci.content_type
            FROM content_items ci
            JOIN content_categories cc ON ci.category_id = cc.id
            WHERE ci.is_active = 1
            AND (
                ci.tags LIKE ? 
                OR ci.description LIKE ?
            )
            ORDER BY ci.is_featured DESC, ci.view_count DESC
            LIMIT ?
        ''', (f'%{mood}%', f'%{mood}%', limit))
        
        results = cursor.fetchall()
        
        # Step 2: If no results, try category mapping
        if not results and mood in MOOD_TO_CATEGORY_MAP:
            categories = MOOD_TO_CATEGORY_MAP[mood]
            placeholders = ','.join('?' * len(categories))
            
            cursor.execute(f'''
                SELECT 
                    ci.id,
                    ci.title,
                    ci.description,
                    ci.duration_minutes,
                    cc.slug as category,
                    ci.difficulty_level,
                    ci.tags,
                    ci.content_url,
                    ci.content_type
                FROM content_items ci
                JOIN content_categories cc ON ci.category_id = cc.id
                WHERE ci.is_active = 1
                AND cc.slug IN ({placeholders})
                ORDER BY ci.is_featured DESC, ci.view_count DESC
                LIMIT ?
            ''', (*categories, limit))
            
            results = cursor.fetchall()
        
        conn.close()
        
        # Step 3: Normalize to standard format
        activities = []
        for row in results:
            activities.append({
                'id': row[0],
                'title': row[1],
                'description': row[2] or '',
                'duration_minutes': row[3] or 10,
                'category': row[4],
                'difficulty_level': row[5] or 'low',
                'tags': json.loads(row[6]) if row[6] else [],
                'content_url': row[7] if len(row) > 7 else None,  # External URL
                'content_type': row[8] if len(row) > 8 else None,  # video/blog/podcast
                'source': 'database'
            })
        
        logger.info(f"✅ Found {len(activities)} activities for mood '{mood}' from database")
        return activities
        
    except Exception as e:
        logger.error(f"❌ Database query failed for mood '{mood}': {e}")
        return []

class ContentService:
    """
    Content Service class for compatibility with existing imports
    Provides methods for querying wellness activities from database
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_activities_for_mood(self, mood: str, limit: int = 10) -> List[Dict]:
        """Get activities for a specific mood"""
        return get_activities_for_mood(mood, limit)
    
    def normalize_activity_format(self, activity: Dict) -> Dict:
        """Normalize activity format"""
        return normalize_activity_format(activity)

def normalize_activity_format(activity: Dict) -> Dict:
    """
    Ensure activity has all required fields for ranking
    Used to standardize both DB and fallback activities
    
    Args:
        activity: Activity dict (may be incomplete)
    
    Returns:
        Standardized activity dict
    """
    # Get duration and format it properly
    duration_minutes = activity.get('duration_minutes', activity.get('duration', 10))
    if isinstance(duration_minutes, str):
        duration_str = duration_minutes  # Already formatted
    else:
        duration_str = f"{duration_minutes} min"  # Format as string
    
    # Determine if this is external content
    content_url = activity.get('content_url', '')
    content_type = activity.get('content_type', '')
    action_type = 'open_external' if content_url else 'activity'
    
    return {
        'id': activity.get('id', 0),
        'title': activity.get('title', activity.get('name', 'Activity')),
        'name': activity.get('name', activity.get('title', 'Activity')),  # Frontend expects 'name'
        'description': activity.get('description', ''),
        'duration_minutes': duration_minutes,  # Keep numeric for backend
        'duration': duration_str,  # Add formatted string for frontend
        'category': activity.get('category', 'general'),
        'difficulty_level': activity.get('difficulty_level', activity.get('effort', 'low')),
        'tags': activity.get('tags', []),
        'source': activity.get('source', 'fallback'),
        'content_url': content_url,  # External URL (YouTube, blog, etc.)
        'content_type': content_type,  # 'video', 'blog', 'podcast'
        'action_type': action_type  # 'open_external' or 'activity'
    }
