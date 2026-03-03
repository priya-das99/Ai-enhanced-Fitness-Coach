"""
Pattern Detector Service
Detects behavioral patterns from user data using rule-based logic
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class PatternDetector:
    """Detect behavioral patterns from user data"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mood_capture.db')
        self.db_path = db_path
    
    def detect_all_patterns(self, user_id: int) -> Dict:
        """
        Detect all patterns for a user
        
        Returns:
            Dictionary with detected patterns
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        patterns = {
            'mood_patterns': self._detect_mood_patterns(conn, user_id),
            'activity_patterns': self._detect_activity_patterns(conn, user_id),
            'health_patterns': self._detect_health_patterns(conn, user_id),
            'engagement_patterns': {
                'acceptance_rate': 0,
                'low_acceptance': False,
                'active_challenges': 0,
                'struggling_challenges': 0
            },
            'effectiveness_patterns': {
                'best_activity': None,
                'best_for_stress': None
            }
        }
        
        conn.close()
        return patterns
    
    def _detect_mood_patterns(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """Detect mood-related patterns"""
        cursor = conn.cursor()
        
        # Pattern 1: Consecutive negative mood days (look at last 30 days)
        cursor.execute("""
            SELECT 
                DATE(timestamp) as mood_date,
                mood_emoji,
                reason
            FROM mood_logs
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            ORDER BY timestamp DESC
        """, (user_id,))
        
        mood_logs = cursor.fetchall()
        
        # Count consecutive stressed/sad days
        negative_moods = ['😟', '😰', '😢', '😭', '😡', '😤']
        consecutive_negative = 0
        max_consecutive = 0
        
        for log in mood_logs:
            if log['mood_emoji'] in negative_moods:
                consecutive_negative += 1
                max_consecutive = max(max_consecutive, consecutive_negative)
            else:
                consecutive_negative = 0
        
        # Pattern 2: Recurring reason (look at last 30 days)
        cursor.execute("""
            SELECT reason, COUNT(*) as count
            FROM mood_logs
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            AND reason IS NOT NULL
            GROUP BY reason
            ORDER BY count DESC
            LIMIT 1
        """, (user_id,))
        
        recurring_reason = cursor.fetchone()
        
        return {
            'consecutive_negative_days': max_consecutive,
            'has_prolonged_stress': max_consecutive >= 3,
            'recurring_reason': recurring_reason['reason'] if recurring_reason else None,
            'recurring_reason_count': recurring_reason['count'] if recurring_reason else 0
        }
    
    def _detect_activity_patterns(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """Detect activity-related patterns"""
        cursor = conn.cursor()
        
        # Current week activity count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM health_activities
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-7 days')
        """, (user_id,))
        
        current_week = cursor.fetchone()['count']
        
        # Baseline (last 30 days average per week)
        cursor.execute("""
            SELECT COUNT(*) / 4.0 as avg_per_week
            FROM health_activities
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            AND timestamp < datetime('now', '-7 days')
        """, (user_id,))
        
        baseline_result = cursor.fetchone()
        baseline = baseline_result['avg_per_week'] if baseline_result['avg_per_week'] else 0
        
        # Streak calculation
        cursor.execute("""
            SELECT DISTINCT DATE(timestamp) as activity_date
            FROM health_activities
            WHERE user_id = ?
            ORDER BY activity_date DESC
        """, (user_id,))
        
        dates = [row['activity_date'] for row in cursor.fetchall()]
        streak = self._calculate_streak(dates)
        
        return {
            'current_week_count': current_week,
            'baseline_per_week': round(baseline, 1),
            'activity_drop': baseline > 0 and current_week < baseline * 0.5,
            'activity_drop_percentage': round((1 - current_week / baseline) * 100) if baseline > 0 else 0,
            'streak': streak,
            'has_streak': streak >= 3
        }
    
    def _detect_engagement_patterns(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """Detect engagement patterns"""
        cursor = conn.cursor()
        
        # Suggestion acceptance rate (last 7 days)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shown,
                SUM(CASE WHEN interaction_type = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM suggestion_history
            WHERE user_id = ?
            AND shown_at >= datetime('now', '-7 days')
        """, (user_id,))
        
        suggestion_stats = cursor.fetchone()
        total = suggestion_stats['total_shown']
        accepted = suggestion_stats['accepted']
        
        acceptance_rate = (accepted / total * 100) if total > 0 else 0
        
        # Challenge participation
        cursor.execute("""
            SELECT 
                COUNT(*) as active_challenges
            FROM user_challenges
            WHERE user_id = ?
            AND status = 'active'
        """, (user_id,))
        
        challenge_stats = cursor.fetchone()
        
        return {
            'acceptance_rate': round(acceptance_rate, 1),
            'low_acceptance': acceptance_rate < 30 and total > 0,
            'active_challenges': challenge_stats['active_challenges'] if challenge_stats else 0,
            'struggling_challenges': 0  # Simplified - would need challenge target data
        }
    
    def _detect_effectiveness_patterns(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """Detect what works for the user"""
        cursor = conn.cursor()
        
        # Best activity overall
        cursor.execute("""
            SELECT 
                activity_id,
                activity_name,
                COUNT(*) as times_done,
                AVG(user_rating) as avg_rating
            FROM user_activity_history
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            AND completed = 1
            AND user_rating IS NOT NULL
            GROUP BY activity_id
            HAVING times_done >= 3
            ORDER BY avg_rating DESC, times_done DESC
            LIMIT 1
        """, (user_id,))
        
        best_activity = cursor.fetchone()
        
        # Best activity for stress
        cursor.execute("""
            SELECT 
                activity_id,
                activity_name,
                COUNT(*) as times_done,
                AVG(user_rating) as avg_rating
            FROM user_activity_history
            WHERE user_id = ?
            AND timestamp >= datetime('now', '-30 days')
            AND completed = 1
            AND user_rating IS NOT NULL
            AND (reason LIKE '%stress%' OR reason LIKE '%anxious%' OR reason LIKE '%overwhelm%')
            GROUP BY activity_id
            HAVING times_done >= 2
            ORDER BY avg_rating DESC, times_done DESC
            LIMIT 1
        """, (user_id,))
        
        best_for_stress = cursor.fetchone()
        
        return {
            'best_activity': {
                'id': best_activity['activity_id'],
                'name': best_activity['activity_name'],
                'times_done': best_activity['times_done'],
                'avg_rating': round(best_activity['avg_rating'], 1)
            } if best_activity else None,
            'best_for_stress': {
                'id': best_for_stress['activity_id'],
                'name': best_for_stress['activity_name'],
                'times_done': best_for_stress['times_done'],
                'avg_rating': round(best_for_stress['avg_rating'], 1)
            } if best_for_stress else None
        }
    
    def _calculate_streak(self, dates: List[str]) -> int:
        """Calculate consecutive days streak"""
        if not dates:
            return 0
        
        streak = 0
        expected_date = datetime.now().date()
        
        for date_str in dates:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break
        
        return streak

    def _detect_health_patterns(self, conn: sqlite3.Connection, user_id: int) -> Dict:
        """Detect health-related patterns (water, sleep)"""
        cursor = conn.cursor()
        
        # Water intake - current week vs baseline
        cursor.execute("""
            SELECT AVG(value) as avg_water
            FROM health_activities
            WHERE user_id = ?
            AND activity_type = 'water'
            AND timestamp >= datetime('now', '-7 days')
        """, (user_id,))
        
        water_current = cursor.fetchone()
        water_current_avg = water_current['avg_water'] if water_current['avg_water'] else 0
        
        # Water baseline (previous 3 weeks)
        cursor.execute("""
            SELECT AVG(value) as avg_water
            FROM health_activities
            WHERE user_id = ?
            AND activity_type = 'water'
            AND timestamp >= datetime('now', '-28 days')
            AND timestamp < datetime('now', '-7 days')
        """, (user_id,))
        
        water_baseline = cursor.fetchone()
        water_baseline_avg = water_baseline['avg_water'] if water_baseline['avg_water'] else 0
        
        # Sleep - current week vs baseline
        cursor.execute("""
            SELECT AVG(value) as avg_sleep
            FROM health_activities
            WHERE user_id = ?
            AND activity_type = 'sleep'
            AND timestamp >= datetime('now', '-7 days')
        """, (user_id,))
        
        sleep_current = cursor.fetchone()
        sleep_current_avg = sleep_current['avg_sleep'] if sleep_current['avg_sleep'] else 0
        
        # Sleep baseline (previous 3 weeks)
        cursor.execute("""
            SELECT AVG(value) as avg_sleep
            FROM health_activities
            WHERE user_id = ?
            AND activity_type = 'sleep'
            AND timestamp >= datetime('now', '-28 days')
            AND timestamp < datetime('now', '-7 days')
        """, (user_id,))
        
        sleep_baseline = cursor.fetchone()
        sleep_baseline_avg = sleep_baseline['avg_sleep'] if sleep_baseline['avg_sleep'] else 0
        
        # Calculate declines
        water_decline = False
        water_decline_pct = 0
        if water_baseline_avg > 0:
            water_decline_pct = ((water_baseline_avg - water_current_avg) / water_baseline_avg) * 100
            water_decline = water_decline_pct >= 50  # 50% or more decline
        
        sleep_decline = False
        sleep_decline_pct = 0
        if sleep_baseline_avg > 0:
            sleep_decline_pct = ((sleep_baseline_avg - sleep_current_avg) / sleep_baseline_avg) * 100
            sleep_decline = sleep_decline_pct >= 15  # 15% or more decline
        
        return {
            'water_current_avg': round(water_current_avg, 1),
            'water_baseline_avg': round(water_baseline_avg, 1),
            'water_decline': water_decline,
            'water_decline_pct': round(water_decline_pct, 0),
            'sleep_current_avg': round(sleep_current_avg, 1),
            'sleep_baseline_avg': round(sleep_baseline_avg, 1),
            'sleep_decline': sleep_decline,
            'sleep_decline_pct': round(sleep_decline_pct, 0)
        }
