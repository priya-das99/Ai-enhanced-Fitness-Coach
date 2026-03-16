"""
Predictive Suggestion Service - SQLite3 Compatible
Suggests activities before user asks

Predicts when user might need help based on:
- Time patterns (3 PM fatigue)
- Day patterns (Monday stress)
- Activity patterns (hasn't exercised in 3 days)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class PredictiveSuggestionServiceSQLite:
    """Predicts when user might need activity suggestions (SQLite3 compatible)"""
    
    def __init__(self):
        pass
    
    def should_suggest_proactively(self, user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
        """Check if we should proactively suggest activities"""
        try:
            now = datetime.now()
            current_hour = now.hour
            current_day = now.weekday()  # 0=Monday
            
            # Get all patterns
            from app.services.pattern_detector_sqlite import PatternDetector
            pattern_detector = PatternDetector()
            patterns = pattern_detector.detect_all_patterns(user_id, db)
            
            # Check time-based patterns
            for pattern in patterns.get('time_patterns', []):
                if pattern['hour'] == current_hour and pattern['confidence'] >= 0.5:
                    return {
                        'trigger_type': 'time_pattern',
                        'pattern': pattern,
                        'message': self._create_time_based_message(pattern),
                        'suggested_activities': self._get_activities_for_pattern(pattern)
                    }
            
            # Check day-based patterns (morning only, 6-10 AM)
            if 6 <= current_hour <= 10:
                for pattern in patterns.get('day_patterns', []):
                    if pattern['day'].lower() == self._get_day_name(current_day).lower():
                        if pattern['confidence'] >= 0.6:
                            return {
                                'trigger_type': 'day_pattern',
                                'pattern': pattern,
                                'message': self._create_day_based_message(pattern),
                                'suggested_activities': self._get_activities_for_pattern(pattern)
                            }
            
            # Check absence pattern
            absence = patterns.get('absence_pattern')
            if absence and absence['days_absent'] >= 3:
                return {
                    'trigger_type': 'absence',
                    'pattern': absence,
                    'message': self._create_absence_message(absence),
                    'suggested_activities': []
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to check predictive suggestions for user {user_id}: {e}", exc_info=True)
            return None
    
    def _create_time_based_message(self, pattern: Dict) -> str:
        """Create message for time-based pattern"""
        hour = pattern['hour']
        
        if 'tired' in pattern['pattern']:
            return (
                f"Hey! It's {hour}:00 - I noticed you often feel tired around this time. 😴\n\n"
                f"Want to try a quick energy boost before the slump hits?"
            )
        elif 'stressed' in pattern['pattern']:
            return (
                f"Hi! It's {hour}:00 - you tend to feel stressed around this time. 😟\n\n"
                f"How about a preventive activity to stay calm?"
            )
        else:
            return (
                f"Hey! Based on your patterns, this is usually a challenging time for you.\n\n"
                f"Want to try something that might help?"
            )
    
    def _create_day_based_message(self, pattern: Dict) -> str:
        """Create message for day-based pattern"""
        day = pattern['day']
        reason = pattern.get('reason', 'challenging')
        
        return (
            f"Good morning! 🌅\n\n"
            f"I noticed {day}s can be {reason} for you. "
            f"Want to start the day with a preventive activity?\n\n"
            f"A quick routine now might help you feel better throughout the day."
        )
    
    def _create_absence_message(self, pattern: Dict) -> str:
        """Create message for absence pattern"""
        days = pattern['days_absent']
        
        return (
            f"Hey! I haven't heard from you in {days} days. 👋\n\n"
            f"I hope everything is okay! How have you been feeling?"
        )
    
    def _get_activities_for_pattern(self, pattern: Dict) -> List[str]:
        """Get suggested activities for a pattern"""
        pattern_type = pattern.get('pattern', '')
        
        # Map patterns to activities
        if 'tired' in pattern_type:
            return ['short_walk', 'stretching', 'breathing']
        elif 'stressed' in pattern_type or 'stress' in pattern_type:
            return ['breathing', 'meditation', 'short_walk']
        elif 'anxious' in pattern_type or 'anxiety' in pattern_type:
            return ['meditation', 'breathing', 'journaling']
        else:
            return ['breathing', 'meditation', 'short_walk']
    
    def _get_day_name(self, day_num: int) -> str:
        """Convert day number to name"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[day_num]
    
    def get_preventive_suggestion(self, user_id: int, context: str, db: sqlite3.Connection) -> Optional[Dict]:
        """Get preventive suggestion based on context"""
        try:
            from app.services.pattern_detector_sqlite import PatternDetector
            pattern_detector = PatternDetector()
            patterns = pattern_detector.detect_all_patterns(user_id, db)
            
            # Find relevant patterns
            relevant_patterns = []
            
            for pattern in patterns.get('day_patterns', []):
                if context.lower() in pattern.get('reason', '').lower():
                    relevant_patterns.append(pattern)
            
            for pattern in patterns.get('activity_patterns', []):
                if context.lower() in pattern.get('reason', '').lower():
                    relevant_patterns.append(pattern)
            
            if not relevant_patterns:
                return None
            
            # Get most confident pattern
            best_pattern = max(relevant_patterns, key=lambda p: p.get('confidence', 0))
            
            return {
                'pattern': best_pattern,
                'suggestion': f"Based on your history, {best_pattern['description']}",
                'activities': self._get_activities_for_pattern(best_pattern)
            }
        
        except Exception as e:
            logger.error(f"Failed to get preventive suggestion for user {user_id}: {e}", exc_info=True)
            return None
