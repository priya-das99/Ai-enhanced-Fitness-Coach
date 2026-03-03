# health_activity_logger.py
# Log health activities like water intake, sleep, weight

from db import get_connection
from datetime import datetime

class HealthActivityLogger:
    """Log and retrieve health activities"""
    
    ACTIVITY_TYPES = {
        'water': {'unit': 'glasses', 'aliases': ['water', 'drink', 'hydration', 'glass']},
        'sleep': {'unit': 'hours', 'aliases': ['sleep', 'slept', 'rest', 'nap']},
        'weight': {'unit': 'kg', 'aliases': ['weight', 'weigh']},
        'exercise': {'unit': 'minutes', 'aliases': ['exercise', 'workout', 'gym', 'run', 'walk']},
        'meal': {'unit': 'servings', 'aliases': ['meal', 'eat', 'ate', 'food', 'breakfast', 'lunch', 'dinner']}
    }
    
    def __init__(self):
        pass
    
    def check_recent_sleep(self, user_id, target_date):
        """Check if sleep was already logged for a specific date"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT value, unit, timestamp
                FROM health_activities
                WHERE user_id = ? 
                AND activity_type = 'sleep'
                AND DATE(timestamp) = DATE(?)
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, target_date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'value': result[0],
                    'unit': result[1],
                    'timestamp': result[2]
                }
            
            return None
            
        except Exception as e:
            conn.close()
            return None
    
    def log_activity(self, user_id, activity_type, value, unit=None, notes=None):
        """Log a health activity with smart date attribution for sleep"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Use default unit if not provided
        if not unit and activity_type in self.ACTIVITY_TYPES:
            unit = self.ACTIVITY_TYPES[activity_type]['unit']
        
        # Smart timestamp for sleep: attribute to the night it started
        now = datetime.now()
        
        if activity_type == 'sleep':
            # Determine if this is nighttime sleep or a nap based on duration and time
            is_nighttime_sleep = value >= 5  # 5+ hours is likely nighttime sleep
            is_morning = now.hour < 12
            is_early_afternoon = 12 <= now.hour < 15
            
            # Decision logic:
            # 1. Morning (before noon) + any sleep duration → previous night
            # 2. Early afternoon (12-3 PM) + long sleep (5+ hours) → previous night (late logging)
            # 3. Early afternoon + short sleep (< 5 hours) → today (nap)
            # 4. Late afternoon/evening → today (nap or very late logging)
            
            if is_morning or (is_early_afternoon and is_nighttime_sleep):
                # Attribute to previous night
                from datetime import timedelta
                log_date = (now - timedelta(days=1)).date()
                local_timestamp = f"{log_date} {now.strftime('%H:%M:%S')}"
            else:
                # Attribute to today (nap or very late logging)
                local_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Regular logging - use current timestamp
            local_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO health_activities (user_id, activity_type, value, unit, notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, value, unit, notes, local_timestamp))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update challenge progress
        try:
            from app.repositories.challenge_repository import ChallengeRepository
            challenge_repo = ChallengeRepository()
            challenge_repo.update_challenge_progress(user_id, activity_type, value)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to update challenge progress: {e}")
        
        return activity_id
    
    def get_today_activities(self, user_id):
        """Get today's activities for a user"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT activity_type, value, unit, notes, timestamp
            FROM health_activities
            WHERE user_id = ? AND DATE(timestamp) = DATE('now')
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        activities = cursor.fetchall()
        conn.close()
        
        return [
            {
                'activity_type': row[0],
                'value': row[1],
                'unit': row[2],
                'notes': row[3],
                'timestamp': row[4]
            }
            for row in activities
        ]
    
    def get_activity_summary(self, user_id, activity_type, days=7):
        """Get summary of specific activity over last N days"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, SUM(value) as total, unit
            FROM health_activities
            WHERE user_id = ? AND activity_type = ?
            AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp), unit
            ORDER BY date DESC
        ''', (user_id, activity_type, days))
        
        summary = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'total': row[1],
                'unit': row[2]
            }
            for row in summary
        ]
    
    def normalize_activity_type(self, text):
        """Detect activity type from text using word boundaries"""
        import re
        text_lower = text.lower()
        
        for activity_type, config in self.ACTIVITY_TYPES.items():
            for alias in config['aliases']:
                # Use word boundaries to avoid substring matches
                # e.g., "eat" won't match in "weather"
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, text_lower):
                    return activity_type
        
        return None
