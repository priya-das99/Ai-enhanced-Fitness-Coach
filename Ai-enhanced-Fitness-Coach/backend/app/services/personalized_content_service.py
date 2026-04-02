"""
Personalized Content Service
Uses user preferences to filter and rank content suggestions
"""
import sqlite3
from typing import List, Dict, Any
from app.services.user_preferences_service import UserPreferencesService

def get_connection():
    return sqlite3.connect('backend/mood_capture.db')

class PersonalizedContentService:
    """Service that uses preferences to personalize content"""
    
    @staticmethod
    def get_personalized_content(user_id: int, mood_emoji: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get content suggestions personalized for the user
        Falls back to regular suggestions if no preferences set
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get user preferences
        prefs = UserPreferencesService.get_all_preferences(user_id)
        favorite_categories = UserPreferencesService.get_favorite_categories(user_id)
        preferred_duration = UserPreferencesService.get_preferred_duration(user_id)
        
        # Build query based on preferences
        query = '''
            SELECT 
                ci.id,
                ci.title,
                ci.description,
                ci.content_type,
                ci.content_url,
                ci.duration_minutes,
                ci.difficulty_level,
                cc.name as category_name,
                cc.slug as category_slug
            FROM content_items ci
            JOIN content_categories cc ON ci.category_id = cc.id
            WHERE ci.is_active = 1
        '''
        
        params = []
        
        # Filter by favorite categories if set
        if favorite_categories:
            placeholders = ','.join('?' * len(favorite_categories))
            query += f' AND cc.slug IN ({placeholders})'
            params.extend(favorite_categories)
        
        # Filter by duration preference
        if preferred_duration == "short":
            query += ' AND ci.duration_minutes <= 10'
        elif preferred_duration == "medium":
            query += ' AND ci.duration_minutes BETWEEN 10 AND 20'
        elif preferred_duration == "long":
            query += ' AND ci.duration_minutes > 20'
        
        # Order by featured first, then random
        query += ' ORDER BY ci.is_featured DESC, RANDOM() LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        
        # If no results (preferences too restrictive), fall back to general content
        if not results:
            return PersonalizedContentService._get_fallback_content(user_id, limit)
        
        return results
    
    @staticmethod
    def _get_fallback_content(user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Fallback to general content if preferences are too restrictive"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ci.id,
                ci.title,
                ci.description,
                ci.content_type,
                ci.content_url,
                ci.duration_minutes,
                ci.difficulty_level,
                cc.name as category_name,
                cc.slug as category_slug
            FROM content_items ci
            JOIN content_categories cc ON ci.category_id = cc.id
            WHERE ci.is_active = 1
            ORDER BY ci.is_featured DESC, RANDOM()
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return results
