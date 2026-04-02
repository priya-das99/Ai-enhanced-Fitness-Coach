# app/services/activity_feedback_service.py
# Service for collecting and analyzing activity feedback

from datetime import datetime
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class ActivityFeedbackService:
    """
    Collects feedback on activity effectiveness and calculates success rates
    """
    
    def record_feedback(self, user_id: int, activity_id: str, mood_before: str, 
                       mood_after: str, helpful: bool, completion_id: int = None):
        """
        Record user feedback on activity effectiveness
        
        Args:
            user_id: User ID
            activity_id: Activity ID
            mood_before: Mood emoji before activity
            mood_after: Mood emoji after activity
            helpful: Whether activity was helpful (True/False)
            completion_id: Optional completion record ID
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                cursor.execute('''
                    INSERT INTO activity_feedback
                    (user_id, activity_id, mood_before, mood_after, helpful, 
                     completion_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, activity_id, mood_before, mood_after, helpful,
                      completion_id, datetime.now()))
                
                logger.info(f"Recorded feedback for user {user_id}, activity {activity_id}: helpful={helpful}")
                
        except Exception as e:
            logger.error(f"Error recording activity feedback: {e}")
    
    def get_activity_success_rate(self, user_id: int, activity_id: str) -> float:
        """
        Get success rate for specific activity for this user
        
        Returns: Success rate as percentage (0-100)
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count
                    FROM activity_feedback
                    WHERE user_id = ? AND activity_id = ?
                ''', (user_id, activity_id))
                
                row = cursor.fetchone()
                
                if row and row['total'] > 0:
                    return (row['helpful_count'] / row['total']) * 100
                
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting activity success rate: {e}")
            return 0.0
    
    def get_activity_success_rate_for_reason(self, user_id: int, activity_id: str, reason: str) -> float:
        """
        Get success rate for activity when used for specific reason
        
        Returns: Success rate as percentage (0-100)
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                # Get feedback records with reason context
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN af.helpful = 1 THEN 1 ELSE 0 END) as helpful_count
                    FROM activity_feedback af
                    JOIN activity_completions ac ON af.completion_id = ac.id
                    WHERE af.user_id = ? 
                    AND af.activity_id = ?
                    AND LOWER(ac.reason) LIKE ?
                ''', (user_id, activity_id, f'%{reason.lower()}%'))
                
                row = cursor.fetchone()
                
                if row and row['total'] > 0:
                    return (row['helpful_count'] / row['total']) * 100
                
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting activity success rate for reason: {e}")
            return 0.0
    
    def get_top_activities_for_user(self, user_id: int, limit: int = 5):
        """
        Get top performing activities for user based on feedback
        
        Returns: List of (activity_id, success_rate, total_uses)
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                cursor.execute('''
                    SELECT 
                        activity_id,
                        COUNT(*) as total_uses,
                        (SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate
                    FROM activity_feedback
                    WHERE user_id = ?
                    GROUP BY activity_id
                    HAVING total_uses >= 2
                    ORDER BY success_rate DESC, total_uses DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                return [
                    {
                        'activity_id': row['activity_id'],
                        'success_rate': row['success_rate'],
                        'total_uses': row['total_uses']
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting top activities: {e}")
            return []
    
    def should_ask_for_feedback(self, user_id: int, activity_id: str) -> bool:
        """
        Determine if we should ask for feedback (don't ask every time)
        
        Returns: True if should ask
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                # Get feedback count for this activity
                cursor.execute('''
                    SELECT COUNT(*) as count
                    FROM activity_feedback
                    WHERE user_id = ? AND activity_id = ?
                ''', (user_id, activity_id))
                
                count = cursor.fetchone()['count']
                
                # Ask for feedback:
                # - First 3 times (to establish baseline)
                # - Then every 5th time (to track changes)
                if count < 3:
                    return True
                elif count % 5 == 0:
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking if should ask for feedback: {e}")
            return True  # Default to asking


# Global instance
_activity_feedback_service = None

def get_activity_feedback_service() -> ActivityFeedbackService:
    """Get or create global ActivityFeedbackService instance"""
    global _activity_feedback_service
    if _activity_feedback_service is None:
        _activity_feedback_service = ActivityFeedbackService()
    return _activity_feedback_service
