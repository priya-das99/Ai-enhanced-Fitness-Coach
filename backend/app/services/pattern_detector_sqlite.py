"""
Pattern Detection Service - SQLite3 Compatible
Identifies recurring patterns in user behavior using raw SQL

Detects:
- Day patterns (Monday stress, Friday fatigue)
- Time patterns (3 PM tired, 9 AM anxious)
- Activity patterns (meditation for stress)
- Mood improvement patterns (what works)
- Absence patterns (inactive users)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects behavioral patterns from user data (SQLite3 compatible)"""
    
    def __init__(self):
        pass
    
    def detect_all_patterns(self, user_id: int, db: sqlite3.Connection) -> Dict:
        """Detect all patterns for a user"""
        try:
            return {
                'day_patterns': self.detect_day_patterns(user_id, db),
                'time_patterns': self.detect_time_patterns(user_id, db),
                'activity_patterns': self.detect_activity_patterns(user_id, db),
                'mood_improvement_patterns': self.detect_mood_improvement_patterns(user_id, db),
                'absence_pattern': self.detect_absence_pattern(user_id, db)
            }
        except Exception as e:
            logger.error(f"Error detecting patterns for user {user_id}: {e}", exc_info=True)
            return {
                'day_patterns': [],
                'time_patterns': [],
                'activity_patterns': [],
                'mood_improvement_patterns': [],
                'absence_pattern': None
            }
    
    def detect_day_patterns(self, user_id: int, db: sqlite3.Connection) -> List[Dict]:
        """Detect patterns by day of week (e.g., stressed every Monday)"""
        patterns = []
        
        try:
            cursor = db.cursor()
            
            # Get mood logs from last 4 weeks with day of week
            cursor.execute("""
                SELECT 
                    mood_emoji,
                    reason,
                    mood_intensity,
                    CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
                    timestamp
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-28 days')
                ORDER BY timestamp DESC
            """, (user_id,))
            
            mood_logs = cursor.fetchall()
            
            if not mood_logs:
                return []
            
            # Group by day of week (0=Sunday in SQLite, convert to 0=Monday)
            day_moods = {i: [] for i in range(7)}
            
            for log in mood_logs:
                mood_emoji, reason, intensity, day_of_week_sqlite, timestamp = log
                # Convert SQLite day (0=Sunday) to Python day (0=Monday)
                day_of_week = (day_of_week_sqlite + 6) % 7
                
                day_moods[day_of_week].append({
                    'emoji': mood_emoji,
                    'reason': reason,
                    'intensity': intensity or 5
                })
            
            # Analyze each day
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            negative_emojis = ['😟', '😢', '😠', '😰', '😞', '😭', '😤', '😔']
            
            for day_num, moods in day_moods.items():
                if len(moods) >= 3:  # Need at least 3 occurrences
                    # Check for negative mood pattern
                    negative_count = sum(1 for m in moods if m['emoji'] in negative_emojis)
                    
                    if negative_count >= 3:
                        # Find most common reason
                        reasons = [m['reason'] for m in moods if m['reason']]
                        most_common_reason = max(set(reasons), key=reasons.count) if reasons else None
                        
                        patterns.append({
                            'type': 'day_pattern',
                            'day': day_names[day_num],
                            'pattern': f"negative_mood_on_{day_names[day_num].lower()}",
                            'description': f"You tend to feel negative on {day_names[day_num]}s",
                            'reason': most_common_reason,
                            'occurrences': negative_count,
                            'confidence': negative_count / len(moods)
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting day patterns: {e}", exc_info=True)
            return []
    
    def detect_time_patterns(self, user_id: int, db: sqlite3.Connection) -> List[Dict]:
        """Detect patterns by time of day (e.g., tired at 3 PM)"""
        patterns = []
        
        try:
            cursor = db.cursor()
            
            # Get mood logs from last 2 weeks with hour
            cursor.execute("""
                SELECT 
                    mood_emoji,
                    reason,
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-14 days')
            """, (user_id,))
            
            mood_logs = cursor.fetchall()
            
            if not mood_logs:
                return []
            
            # Group by hour
            hour_moods = {i: [] for i in range(24)}
            
            for log in mood_logs:
                mood_emoji, reason, hour = log
                hour_moods[hour].append({
                    'emoji': mood_emoji,
                    'reason': reason
                })
            
            # Analyze each hour
            for hour, moods in hour_moods.items():
                if len(moods) >= 3:  # Need at least 3 occurrences
                    # Check for specific patterns
                    tired_count = sum(1 for m in moods if m['reason'] and 'tired' in m['reason'].lower())
                    stressed_count = sum(1 for m in moods if m['reason'] and 'stress' in m['reason'].lower())
                    
                    if tired_count >= 2:
                        patterns.append({
                            'type': 'time_pattern',
                            'hour': hour,
                            'pattern': f"tired_at_{hour}",
                            'description': f"You often feel tired around {hour}:00",
                            'occurrences': tired_count,
                            'confidence': tired_count / len(moods)
                        })
                    
                    if stressed_count >= 2:
                        patterns.append({
                            'type': 'time_pattern',
                            'hour': hour,
                            'pattern': f"stressed_at_{hour}",
                            'description': f"You often feel stressed around {hour}:00",
                            'occurrences': stressed_count,
                            'confidence': stressed_count / len(moods)
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting time patterns: {e}", exc_info=True)
            return []
    
    def detect_activity_patterns(self, user_id: int, db: sqlite3.Connection) -> List[Dict]:
        """Detect which activities user prefers for specific situations"""
        patterns = []
        
        try:
            cursor = db.cursor()
            
            # Get activities from last 4 weeks
            cursor.execute("""
                SELECT activity_id, activity_name, reason
                FROM user_activity_history
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-28 days')
                AND completed = 1
            """, (user_id,))
            
            activities = cursor.fetchall()
            
            if not activities:
                return []
            
            # Group by reason
            reason_activities = {}
            
            for activity_id, activity_name, reason in activities:
                reason_key = reason or 'general'
                if reason_key not in reason_activities:
                    reason_activities[reason_key] = []
                reason_activities[reason_key].append((activity_id, activity_name))
            
            # Find patterns
            for reason, activity_list in reason_activities.items():
                if len(activity_list) >= 3:
                    # Count activities
                    activity_counts = {}
                    for activity_id, activity_name in activity_list:
                        key = (activity_id, activity_name)
                        activity_counts[key] = activity_counts.get(key, 0) + 1
                    
                    # Find most common
                    if activity_counts:
                        most_common = max(activity_counts.items(), key=lambda x: x[1])
                        (activity_id, activity_name), count = most_common
                        
                        if count >= 3:
                            patterns.append({
                                'type': 'activity_pattern',
                                'reason': reason,
                                'activity': activity_name,
                                'activity_id': activity_id,
                                'pattern': f"{activity_name}_for_{reason}",
                                'description': f"You often choose {activity_name} when feeling {reason}",
                                'occurrences': count,
                                'confidence': count / len(activity_list)
                            })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting activity patterns: {e}", exc_info=True)
            return []
    
    def detect_mood_improvement_patterns(self, user_id: int, db: sqlite3.Connection) -> List[Dict]:
        """Detect which activities consistently improve mood"""
        patterns = []
        
        try:
            cursor = db.cursor()
            
            # Get feedback from last 4 weeks
            cursor.execute("""
                SELECT activity_id, helpful
                FROM activity_feedback
                WHERE user_id = ?
                AND created_at >= datetime('now', '-28 days')
            """, (user_id,))
            
            feedback_records = cursor.fetchall()
            
            if not feedback_records:
                return []
            
            # Group by activity
            activity_feedback = {}
            
            for activity_id, helpful in feedback_records:
                if activity_id not in activity_feedback:
                    activity_feedback[activity_id] = {'helpful': 0, 'total': 0}
                
                activity_feedback[activity_id]['total'] += 1
                if helpful:
                    activity_feedback[activity_id]['helpful'] += 1
            
            # Find high-success activities
            for activity_id, stats in activity_feedback.items():
                if stats['total'] >= 3:  # At least 3 tries
                    success_rate = stats['helpful'] / stats['total']
                    
                    if success_rate >= 0.75:  # 75% or higher
                        patterns.append({
                            'type': 'mood_improvement',
                            'activity': activity_id,
                            'pattern': f"{activity_id}_improves_mood",
                            'description': f"{activity_id} consistently improves your mood",
                            'success_rate': success_rate,
                            'occurrences': stats['total'],
                            'confidence': success_rate
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting mood improvement patterns: {e}", exc_info=True)
            return []
    
    def detect_absence_pattern(self, user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
        """Detect if user hasn't logged in recently"""
        try:
            cursor = db.cursor()
            
            # Get last mood log
            cursor.execute("""
                SELECT timestamp
                FROM mood_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
            
            last_log_str = result[0]
            last_log = datetime.fromisoformat(last_log_str)
            days_since_last = (datetime.now() - last_log).days
            
            if days_since_last >= 3:
                return {
                    'type': 'absence',
                    'days_absent': days_since_last,
                    'last_activity': last_log_str,
                    'description': f"You haven't logged mood in {days_since_last} days"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting absence pattern: {e}", exc_info=True)
            return None
