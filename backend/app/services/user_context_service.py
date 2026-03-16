# app/services/user_context_service.py
# Centralized service for user context and activity data

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class UserContextService:
    """
    Centralized service for retrieving user activity data and context.
    Used by: Workflows, Scheduler, Notifications
    """
    
    # Define how different activities should be aggregated
    ACTIVITY_AGGREGATION_RULES = {
        'sleep': 'latest',      # Use most recent entry (not additive)
        'weight': 'latest',     # Use most recent entry (not additive)
        'water': 'sum',         # Sum all entries for the day
        'exercise': 'sum',      # Sum all entries for the day
        'steps': 'sum',         # Sum all entries for the day
        'calories': 'sum',      # Sum all entries for the day
        'meal': 'sum',          # Sum all entries for the day
    }
    
    def get_daily_summary(self, user_id: int, target_date: str = None) -> Dict:
        """
        Get complete daily summary for user with proper aggregation rules.
        
        Returns:
            {
                'water': {'value': 2.0, 'unit': 'glasses', 'target': 8.0},
                'sleep': {'value': 7.0, 'unit': 'hours', 'target': 8.0},
                'exercise': {'value': 30.0, 'unit': 'minutes', 'target': 30.0},
                'mood': {'emoji': '😊', 'logged': True},
                'total_activities': 4
            }
        """
        if not target_date:
            target_date = date.today().isoformat()
        
        with get_db() as db:
            cursor = db.cursor()
            
            # Get challenge targets first
            cursor.execute('''
                SELECT c.challenge_type, c.target_value, c.target_unit
                FROM challenges c
                JOIN user_challenges uc ON c.id = uc.challenge_id
                WHERE uc.user_id = ? AND uc.status = 'active'
            ''', (user_id,))
            
            targets = {row['challenge_type']: {
                'target': row['target_value'],
                'unit': row['target_unit']
            } for row in cursor.fetchall()}
            
            # Build summary with defaults - include ALL supported activity types
            summary = {
                'water': {'value': 0, 'unit': 'glasses', 'target': targets.get('water', {}).get('target', 8)},
                'sleep': {'value': 0, 'unit': 'hours', 'target': targets.get('sleep', {}).get('target', 8)},
                'exercise': {'value': 0, 'unit': 'minutes', 'target': targets.get('exercise', {}).get('target', 30)},
                'weight': {'value': 0, 'unit': 'kg', 'target': targets.get('weight', {}).get('target', 70)},
                'steps': {'value': 0, 'unit': 'steps', 'target': targets.get('steps', {}).get('target', 10000)},  # Add steps
                'calories': {'value': 0, 'unit': 'calories', 'target': targets.get('calories', {}).get('target', 2000)},  # Add calories
                'meal': {'value': 0, 'unit': 'servings', 'target': targets.get('meal', {}).get('target', 3)},  # Add meal
                'mood': {'emoji': None, 'logged': False},
                'total_activities': 0
            }
            
            # Get activities using proper aggregation rules
            for activity_type, aggregation_rule in self.ACTIVITY_AGGREGATION_RULES.items():
                if activity_type in summary:  # Only process activities we track in summary
                    
                    if aggregation_rule == 'latest':
                        # Get the most recent entry for this activity type
                        # Use rowid as secondary sort to handle identical timestamps
                        cursor.execute('''
                            SELECT value, unit, timestamp
                            FROM health_activities
                            WHERE user_id = ? AND activity_type = ? AND DATE(timestamp) = ?
                            ORDER BY timestamp DESC, rowid DESC
                            LIMIT 1
                        ''', (user_id, activity_type, target_date))
                        
                        result = cursor.fetchone()
                        if result:
                            summary[activity_type]['value'] = result['value']
                            summary[activity_type]['unit'] = result['unit']
                            summary['total_activities'] += 1
                            logger.info(f"Latest {activity_type}: {result['value']} {result['unit']} at {result['timestamp']}")
                    
                    elif aggregation_rule == 'sum':
                        # Sum all entries for this activity type
                        cursor.execute('''
                            SELECT SUM(value) as total, unit
                            FROM health_activities
                            WHERE user_id = ? AND activity_type = ? AND DATE(timestamp) = ?
                            GROUP BY unit
                        ''', (user_id, activity_type, target_date))
                        
                        result = cursor.fetchone()
                        if result and result['total']:
                            summary[activity_type]['value'] = result['total']
                            summary[activity_type]['unit'] = result['unit']
                            summary['total_activities'] += 1
                            logger.info(f"Sum {activity_type}: {result['total']} {result['unit']}")
            
            # Get mood for the day
            cursor.execute('''
                SELECT mood_emoji, timestamp
                FROM mood_logs
                WHERE user_id = ? AND DATE(timestamp) = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, target_date))
            
            mood = cursor.fetchone()
            if mood:
                summary['mood'] = {
                    'emoji': mood['mood_emoji'],
                    'logged': True,
                    'time': mood['timestamp']
                }
                summary['total_activities'] += 1
        
        logger.info(f"Daily summary for user {user_id} on {target_date}: {summary}")
        return summary
    
    def get_challenge_progress_today(self, user_id: int, challenge_type: str) -> Optional[Dict]:
        """
        Get today's progress for specific challenge type.
        
        Returns:
            {
                'challenge_id': 1,
                'challenge_title': '7-Day Hydration Challenge',
                'challenge_type': 'water',
                'current': 2.0,
                'target': 8.0,
                'unit': 'glasses',
                'remaining': 6.0,
                'percentage': 25.0,
                'completed': False
            }
        """
        with get_db() as db:
            cursor = db.cursor()
            
            # Get active challenge using correct table structure
            cursor.execute('''
                SELECT c.id, c.title, c.challenge_type, c.target_value, c.target_unit, uc.progress
                FROM challenges c
                JOIN user_challenges uc ON c.id = uc.challenge_id
                WHERE uc.user_id = ? AND c.challenge_type = ? AND uc.status = 'active'
                LIMIT 1
            ''', (user_id, challenge_type))
            
            challenge = cursor.fetchone()
            if not challenge:
                return None
            
            # Use the progress from user_challenges table
            current_value = challenge['progress'] if challenge['progress'] else 0.0
            target_value = challenge['target_value']
            
            return {
                'challenge_id': challenge['id'],
                'challenge_title': challenge['title'],
                'challenge_type': challenge['challenge_type'],
                'current': current_value,
                'target': target_value,
                'unit': challenge['target_unit'],
                'remaining': max(0, target_value - current_value),
                'percentage': (current_value / target_value * 100) if target_value > 0 else 0,
                'completed': current_value >= target_value
            }
    
    def get_today_water_intake(self, user_id: int) -> float:
        """Get today's water intake in glasses"""
        progress = self.get_challenge_progress_today(user_id, 'water')
        return progress['current'] if progress else 0.0
    
    def get_all_challenges_progress(self, user_id: int) -> List[Dict]:
        """Get progress for all active challenges"""
        with get_db() as db:
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT DISTINCT c.challenge_type
                FROM challenges c
                JOIN user_challenges uc ON c.id = uc.challenge_id
                WHERE uc.user_id = ? AND uc.status = 'active'
            ''', (user_id,))
            
            challenge_types = [row['challenge_type'] for row in cursor.fetchall()]
        
        return [
            self.get_challenge_progress_today(user_id, ct)
            for ct in challenge_types
            if self.get_challenge_progress_today(user_id, ct)
        ]
    
    def should_send_reminder(self, user_id: int, reminder_type: str) -> Dict:
        """
        Determine if reminder should be sent.
        
        Returns:
            {
                'should_send': bool,
                'reason': str,
                'data': dict
            }
        """
        current_hour = datetime.now().hour
        
        if reminder_type == 'water_reminder':
            progress = self.get_challenge_progress_today(user_id, 'water')
            if not progress:
                return {'should_send': False, 'reason': 'No active water challenge'}
            
            # Send if: less than 50% complete AND after 3:00 PM (mid-afternoon)
            if progress['percentage'] < 50 and current_hour >= 15:
                return {
                    'should_send': True,
                    'reason': 'Low progress, mid-afternoon check',
                    'data': progress
                }
            
            return {'should_send': False, 'reason': 'Progress OK or too early'}
        
        elif reminder_type == 'sleep_reminder':
            progress = self.get_challenge_progress_today(user_id, 'sleep')
            if not progress:
                return {'should_send': False, 'reason': 'No active sleep challenge'}
            
            # Send if: not logged AND after 10 AM (morning check)
            if progress['current'] == 0 and current_hour >= 10:
                return {
                    'should_send': True,
                    'reason': 'No sleep logged, morning',
                    'data': progress
                }
            
            return {'should_send': False, 'reason': 'Already logged'}
        
        elif reminder_type == 'exercise_reminder':
            progress = self.get_challenge_progress_today(user_id, 'exercise')
            if not progress:
                return {'should_send': False, 'reason': 'No active exercise challenge'}
            
            # Send if: not completed AND after 6 PM (evening)
            if not progress['completed'] and current_hour >= 18:
                return {
                    'should_send': True,
                    'reason': 'Not completed, evening',
                    'data': progress
                }
            
            return {'should_send': False, 'reason': 'Already completed'}
        
        elif reminder_type == 'mood_reminder':
            summary = self.get_daily_summary(user_id)
            
            # Send if: no mood logged AND after 4 PM (evening reflection)
            if not summary['mood']['logged'] and current_hour >= 16:
                return {
                    'should_send': True,
                    'reason': 'No mood logged, evening reflection time',
                    'data': summary['mood']
                }
            
            return {'should_send': False, 'reason': 'Mood already logged or too early'}
        
        elif reminder_type == 'evening_challenges':
            # Send if: any incomplete challenges AND after 8 PM
            if current_hour >= 20:
                all_progress = self.get_all_challenges_progress(user_id)
                incomplete = [p for p in all_progress if not p['completed']]
                
                if incomplete:
                    return {
                        'should_send': True,
                        'reason': 'Incomplete challenges, evening',
                        'data': {'incomplete_challenges': incomplete}
                    }
            
            return {'should_send': False, 'reason': 'All complete or too early'}
        
        return {'should_send': False, 'reason': 'Unknown reminder type'}
    
    def get_active_users(self) -> List[int]:
        """Get list of active user IDs"""
        with get_db() as db:
            cursor = db.cursor()
            
            # Users who have logged in within last 7 days
            cursor.execute('''
                SELECT DISTINCT user_id
                FROM health_activities
                WHERE timestamp >= datetime('now', '-7 days')
                UNION
                SELECT DISTINCT user_id
                FROM mood_logs
                WHERE timestamp >= datetime('now', '-7 days')
            ''')
            
            return [row['user_id'] for row in cursor.fetchall()]


# Global instance
_context_service = None

def get_context_service() -> UserContextService:
    """Get or create global UserContextService instance"""
    global _context_service
    if _context_service is None:
        _context_service = UserContextService()
    return _context_service
