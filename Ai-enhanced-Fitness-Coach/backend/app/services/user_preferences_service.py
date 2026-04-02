"""
User Wellness Preferences Service
Manages user preferences for personalization without breaking existing functionality
"""
import sqlite3
from typing import Optional, Dict, Any
import json
from datetime import datetime

def get_connection():
    """Get database connection"""
    return sqlite3.connect('backend/mood_capture.db')

class UserPreferencesService:
    """Service for managing user wellness preferences"""
    
    # Supported preference keys
    PREF_FAVORITE_CATEGORIES = "favorite_categories"  # ["mindfulness", "yoga"]
    PREF_ACTIVITY_DURATION = "preferred_duration"     # "short" (5-10min), "medium" (10-20min), "long" (20+min)
    PREF_NOTIFICATION_TIME = "notification_time"      # "08:00"
    PREF_DIFFICULTY_LEVEL = "difficulty_level"        # "beginner", "intermediate", "advanced"
    PREF_CONTENT_TYPES = "preferred_content_types"    # ["video", "audio", "article"]
    
    @staticmethod
    def get_preference(user_id: int, preference_key: str) -> Optional[str]:
        """
        Get a user preference value
        Returns None if preference doesn't exist
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_value FROM user_wellness_preferences
            WHERE user_id = ? AND preference_key = ?
        ''', (user_id, preference_key))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    @staticmethod
    def set_preference(user_id: int, preference_key: str, preference_value: str) -> bool:
        """
        Set or update a user preference
        Returns True if successful
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if preference exists
            cursor.execute('''
                SELECT id FROM user_wellness_preferences
                WHERE user_id = ? AND preference_key = ?
            ''', (user_id, preference_key))
            
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute('''
                    UPDATE user_wellness_preferences
                    SET preference_value = ?, updated_at = ?
                    WHERE user_id = ? AND preference_key = ?
                ''', (preference_value, datetime.now().isoformat(), user_id, preference_key))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO user_wellness_preferences (user_id, preference_key, preference_value)
                    VALUES (?, ?, ?)
                ''', (user_id, preference_key, preference_value))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting preference: {e}")
            conn.close()
            return False
    
    @staticmethod
    def get_all_preferences(user_id: int) -> Dict[str, str]:
        """Get all preferences for a user as a dictionary"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_key, preference_value
            FROM user_wellness_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        preferences = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return preferences
    
    @staticmethod
    def delete_preference(user_id: int, preference_key: str) -> bool:
        """Delete a specific preference"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_wellness_preferences
            WHERE user_id = ? AND preference_key = ?
        ''', (user_id, preference_key))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_preferred_duration(user_id: int) -> str:
        """
        Get user's preferred activity duration
        Returns: "short", "medium", "long", or "any" (default)
        """
        pref = UserPreferencesService.get_preference(user_id, UserPreferencesService.PREF_ACTIVITY_DURATION)
        return pref if pref else "any"
    
    @staticmethod
    def get_favorite_categories(user_id: int) -> list:
        """
        Get user's favorite content categories
        Returns: list of category slugs or empty list
        """
        pref = UserPreferencesService.get_preference(user_id, UserPreferencesService.PREF_FAVORITE_CATEGORIES)
        if pref:
            try:
                return json.loads(pref)
            except:
                return []
        return []
    
    @staticmethod
    def set_favorite_categories(user_id: int, categories: list) -> bool:
        """Set user's favorite categories"""
        return UserPreferencesService.set_preference(
            user_id, 
            UserPreferencesService.PREF_FAVORITE_CATEGORIES,
            json.dumps(categories)
        )
