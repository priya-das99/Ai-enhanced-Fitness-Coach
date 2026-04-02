# user_history.py
# User activity history management

from db import get_connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def save_activity_to_history(user_id: int, activity_id: str, activity_name: str, 
                             mood_emoji: str = None, reason: str = None, 
                             completed: bool = True, duration_minutes: int = None,
                             user_rating: int = None, energy_before: int = None,
                             energy_after: int = None, satisfaction_score: int = None,
                             would_repeat: bool = None, completion_percentage: int = 100):
    """
    Save completed activity to user history with quality metrics
    
    Args:
        user_id: User ID
        activity_id: Activity identifier
        activity_name: Activity name
        mood_emoji: User's mood emoji
        reason: Mood reason
        completed: Whether activity was completed
        duration_minutes: How long activity took
        user_rating: User rating (1-5 stars)
        energy_before: Energy level before (1-10)
        energy_after: Energy level after (1-10)
        satisfaction_score: Satisfaction score (1-10)
        would_repeat: Whether user would repeat
        completion_percentage: Completion percentage (0-100)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        day_of_week = now.strftime('%A')  # Monday, Tuesday, etc.
        hour = now.hour
        
        # Determine time of day
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        
        # Use local timestamp
        local_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_activity_history 
            (user_id, activity_id, activity_name, mood_emoji, reason, 
             completed, completion_percentage, duration_minutes,
             user_rating, energy_before, energy_after, 
             satisfaction_score, would_repeat,
             timestamp, day_of_week, time_of_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_id, activity_name, mood_emoji, reason, 
              completed, completion_percentage, duration_minutes,
              user_rating, energy_before, energy_after,
              satisfaction_score, would_repeat,
              local_timestamp, day_of_week, time_of_day))
        
        conn.commit()
        logger.info(f"✅ Saved activity to history: {activity_name} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving activity history: {e}")
        return False
    finally:
        conn.close()

def get_user_activity_history(user_id: int, days: int = 30, limit: int = 50):
    """Get user's activity history"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT activity_id, activity_name, mood_emoji, reason, 
                   completed, timestamp, day_of_week, time_of_day
            FROM user_activity_history
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, since_date, limit))
        
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                'activity_id': row[0],
                'activity_name': row[1],
                'mood_emoji': row[2],
                'reason': row[3],
                'completed': bool(row[4]),
                'timestamp': row[5],
                'day_of_week': row[6],
                'time_of_day': row[7]
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting activity history: {e}")
        return []
    finally:
        conn.close()

def get_activity_stats(user_id: int, days: int = 30):
    """Get statistics about user's activities"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Most completed activities
        cursor.execute('''
            SELECT activity_id, activity_name, COUNT(*) as count
            FROM user_activity_history
            WHERE user_id = ? AND timestamp >= ? AND completed = 1
            GROUP BY activity_id
            ORDER BY count DESC
        ''', (user_id, since_date))
        
        activity_counts = {}
        for row in cursor.fetchall():
            activity_counts[row[0]] = {
                'name': row[1],
                'count': row[2]
            }
        
        # Activities by time of day
        cursor.execute('''
            SELECT time_of_day, activity_id, COUNT(*) as count
            FROM user_activity_history
            WHERE user_id = ? AND timestamp >= ? AND completed = 1
            GROUP BY time_of_day, activity_id
            ORDER BY count DESC
        ''', (user_id, since_date))
        
        time_preferences = {}
        for row in cursor.fetchall():
            time_of_day = row[0]
            activity_id = row[1]
            count = row[2]
            
            if time_of_day not in time_preferences:
                time_preferences[time_of_day] = {}
            time_preferences[time_of_day][activity_id] = count
        
        # Activities by day of week
        cursor.execute('''
            SELECT day_of_week, activity_id, COUNT(*) as count
            FROM user_activity_history
            WHERE user_id = ? AND timestamp >= ? AND completed = 1
            GROUP BY day_of_week, activity_id
            ORDER BY count DESC
        ''', (user_id, since_date))
        
        day_preferences = {}
        for row in cursor.fetchall():
            day = row[0]
            activity_id = row[1]
            count = row[2]
            
            if day not in day_preferences:
                day_preferences[day] = {}
            day_preferences[day][activity_id] = count
        
        # Activities by reason
        cursor.execute('''
            SELECT reason, activity_id, COUNT(*) as count
            FROM user_activity_history
            WHERE user_id = ? AND timestamp >= ? AND completed = 1 AND reason IS NOT NULL
            GROUP BY reason, activity_id
            ORDER BY count DESC
        ''', (user_id, since_date))
        
        reason_preferences = {}
        for row in cursor.fetchall():
            reason = row[0]
            activity_id = row[1]
            count = row[2]
            
            if reason not in reason_preferences:
                reason_preferences[reason] = {}
            reason_preferences[reason][activity_id] = count
        
        return {
            'activity_counts': activity_counts,
            'time_preferences': time_preferences,
            'day_preferences': day_preferences,
            'reason_preferences': reason_preferences
        }
        
    except Exception as e:
        logger.error(f"Error getting activity stats: {e}")
        return {
            'activity_counts': {},
            'time_preferences': {},
            'day_preferences': {},
            'reason_preferences': {}
        }
    finally:
        conn.close()

def get_recent_activities(user_id: int, limit: int = 5):
    """Get user's most recent activities"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT activity_id, activity_name, timestamp
            FROM user_activity_history
            WHERE user_id = ? AND completed = 1
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'activity_id': row[0],
                'activity_name': row[1],
                'timestamp': row[2]
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        return []
    finally:
        conn.close()
