# app/services/streak_service.py
# Service for tracking user streaks and celebrating achievements

from datetime import datetime, timedelta
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class StreakService:
    """
    Tracks user streaks for various activities:
    - Mood logging streak
    - Activity completion streak
    - Daily check-in streak
    """
    
    def get_mood_logging_streak(self, user_id: int) -> int:
        """
        Get current mood logging streak (consecutive days with at least 1 mood log)
        
        Returns: Number of consecutive days
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                # Get all mood log dates for user (distinct days)
                cursor.execute('''
                    SELECT DISTINCT DATE(timestamp) as log_date
                    FROM mood_logs
                    WHERE user_id = ?
                    ORDER BY log_date DESC
                    LIMIT 365
                ''', (user_id,))
                
                dates = [row['log_date'] for row in cursor.fetchall()]
                
                if not dates:
                    return 0
                
                # Calculate streak
                streak = 0
                today = datetime.now().date()
                
                # Check if logged today or yesterday (streak is still active)
                most_recent = datetime.strptime(dates[0], '%Y-%m-%d').date()
                days_since_last = (today - most_recent).days
                
                if days_since_last > 1:
                    # Streak broken
                    return 0
                
                # Count consecutive days
                expected_date = most_recent
                for date_str in dates:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    if date == expected_date:
                        streak += 1
                        expected_date = date - timedelta(days=1)
                    else:
                        break
                
                return streak
                
        except Exception as e:
            logger.error(f"Error getting mood logging streak: {e}")
            return 0
    
    def get_activity_completion_streak(self, user_id: int) -> int:
        """
        Get current activity completion streak (consecutive days with at least 1 completed activity)
        
        Returns: Number of consecutive days
        """
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                # Get all activity completion dates
                cursor.execute('''
                    SELECT DISTINCT DATE(completed_at) as completion_date
                    FROM activity_completions
                    WHERE user_id = ?
                    ORDER BY completion_date DESC
                    LIMIT 365
                ''', (user_id,))
                
                dates = [row['completion_date'] for row in cursor.fetchall()]
                
                if not dates:
                    return 0
                
                # Calculate streak
                streak = 0
                today = datetime.now().date()
                
                most_recent = datetime.strptime(dates[0], '%Y-%m-%d').date()
                days_since_last = (today - most_recent).days
                
                if days_since_last > 1:
                    return 0
                
                expected_date = most_recent
                for date_str in dates:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    if date == expected_date:
                        streak += 1
                        expected_date = date - timedelta(days=1)
                    else:
                        break
                
                return streak
                
        except Exception as e:
            logger.error(f"Error getting activity completion streak: {e}")
            return 0
    
    def should_celebrate_streak(self, user_id: int, streak_type: str, current_streak: int) -> bool:
        """
        Check if we should celebrate this streak (avoid celebrating same milestone multiple times)
        
        Args:
            user_id: User ID
            streak_type: 'mood_logging' or 'activity_completion'
            current_streak: Current streak count
            
        Returns: True if should celebrate
        """
        # Celebrate at milestones: 3, 7, 14, 30, 60, 90, 180, 365
        milestones = [3, 7, 14, 30, 60, 90, 180, 365]
        
        if current_streak not in milestones:
            return False
        
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                # Check if we already celebrated this milestone today
                cursor.execute('''
                    SELECT id FROM streak_celebrations
                    WHERE user_id = ? 
                    AND streak_type = ? 
                    AND milestone = ?
                    AND DATE(celebrated_at) = DATE('now')
                ''', (user_id, streak_type, current_streak))
                
                already_celebrated = cursor.fetchone() is not None
                
                if not already_celebrated:
                    # Record celebration
                    cursor.execute('''
                        INSERT INTO streak_celebrations 
                        (user_id, streak_type, milestone, celebrated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, streak_type, current_streak, datetime.now()))
                    
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking streak celebration: {e}")
            return False
    
    def get_celebration_message(self, streak_type: str, streak_count: int) -> str:
        """
        Get celebration message for streak milestone
        
        Args:
            streak_type: 'mood_logging' or 'activity_completion'
            streak_count: Number of days in streak
            
        Returns: Celebration message
        """
        messages = {
            'mood_logging': {
                3: "🎉 Awesome! You've logged your mood 3 days in a row!\n\nConsistency is key to understanding your patterns. Keep it up!",
                7: "🔥 Amazing! 7-day mood logging streak!\n\nYou're building a great habit. Users who log for a week report 40% better mood awareness!",
                14: "⭐ Incredible! 2 weeks of daily mood logging!\n\nYou're really committed to understanding yourself better. That's powerful!",
                30: "🏆 WOW! 30-day streak!\n\nYou're a mood logging champion! This level of consistency is rare and valuable.",
                60: "💎 60 days! You're unstoppable!\n\nYour dedication to self-awareness is truly inspiring.",
                90: "🌟 90-day streak! That's 3 months!\n\nYou've built a rock-solid habit. Amazing work!",
                180: "👑 Half a year! 180 days!\n\nYou're in the top 1% of users. Incredible commitment!",
                365: "🎊 ONE FULL YEAR! 365 days!\n\nYou've achieved something extraordinary. Congratulations!"
            },
            'activity_completion': {
                3: "💪 Nice! 3 days of completing activities!\n\nYou're taking action on your wellness. Keep going!",
                7: "🔥 7-day activity streak!\n\nYou're not just tracking - you're doing! That's what makes the difference.",
                14: "⭐ 2 weeks of daily activities!\n\nYou're building real wellness habits. Proud of you!",
                30: "🏆 30 days of action!\n\nYou've proven that consistency beats intensity. Amazing!",
                60: "💎 60 days! You're a wellness warrior!\n\nYour commitment is paying off.",
                90: "🌟 90 days of daily wellness!\n\nYou've transformed your routine. Incredible!",
                180: "👑 Half a year of daily action!\n\nYou're living proof that small steps lead to big changes.",
                365: "🎊 365 days! A full year!\n\nYou've achieved mastery. Congratulations!"
            }
        }
        
        return messages.get(streak_type, {}).get(streak_count, f"🎉 {streak_count}-day streak! Keep it up!")


# Global instance
_streak_service = None

def get_streak_service() -> StreakService:
    """Get or create global StreakService instance"""
    global _streak_service
    if _streak_service is None:
        _streak_service = StreakService()
    return _streak_service
