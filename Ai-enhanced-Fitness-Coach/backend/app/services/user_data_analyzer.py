"""
User Data Analyzer Service
Analyzes user's historical data to provide context-aware insights
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class UserDataAnalyzer:
    """Analyzes user data to provide contextual insights"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mood_capture.db')
        self.db_path = db_path
    
    def analyze_for_mood(self, user_id: int, mood_text: str, mood_emoji: str = None) -> Dict:
        """
        Analyze user data relevant to current mood/feeling
        
        Args:
            user_id: User ID
            mood_text: What user said (e.g., "I am tired")
            mood_emoji: Detected mood emoji
            
        Returns:
            Dictionary with insights and patterns
        """
        mood_lower = mood_text.lower()
        
        # Detect what type of analysis is needed
        if any(word in mood_lower for word in ['tired', 'exhausted', 'sleepy', 'fatigue']):
            return self._analyze_tiredness_pattern(user_id)
        elif any(word in mood_lower for word in ['stressed', 'stress', 'anxious', 'overwhelmed']):
            return self._analyze_stress_pattern(user_id)
        elif any(word in mood_lower for word in ['sad', 'down', 'depressed', 'lonely']):
            return self._analyze_sadness_pattern(user_id)
        else:
            return self._analyze_general_pattern(user_id, mood_emoji)
    
    def _analyze_tiredness_pattern(self, user_id: int) -> Dict:
        """Analyze patterns related to tiredness - considers sleep, hydration, exercise"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        insights = {
            'pattern_type': 'tiredness',
            'has_pattern': False,
            'insight_text': None,
            'recommendations': [],
            'contributing_factors': []
        }
        
        try:
            # Factor 1: Get sleep data from last 7 days
            cursor.execute("""
                SELECT value, unit, timestamp
                FROM health_activities
                WHERE user_id = ? 
                AND activity_type = 'sleep'
                AND timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            """, (user_id,))
            
            sleep_data = cursor.fetchall()
            
            if sleep_data:
                # Calculate average sleep
                sleep_hours = [float(row['value']) for row in sleep_data]
                avg_sleep = sum(sleep_hours) / len(sleep_hours)
                
                insights['avg_sleep'] = round(avg_sleep, 1)
                insights['sleep_count'] = len(sleep_hours)
                insights['min_sleep'] = min(sleep_hours)
                insights['max_sleep'] = max(sleep_hours)
                
                # Check if sleep is consistently low
                if avg_sleep < 6.5:
                    insights['has_pattern'] = True
                    insights['pattern_severity'] = 'high' if avg_sleep < 6 else 'medium'
                    insights['insight_text'] = f"averaging {avg_sleep:.1f} hours of sleep this week"
                    insights['contributing_factors'].append('insufficient_sleep')
                    insights['recommendations'].append('improve_sleep_hygiene')
                
                # Check for declining sleep trend
                if len(sleep_hours) >= 3:
                    recent_avg = sum(sleep_hours[:3]) / 3
                    older_avg = sum(sleep_hours[3:]) / len(sleep_hours[3:]) if len(sleep_hours) > 3 else recent_avg
                    
                    if recent_avg < older_avg - 0.5:
                        insights['declining_sleep'] = True
                        insights['contributing_factors'].append('declining_sleep_trend')
                        insights['recommendations'].append('address_sleep_decline')
            
            # Factor 2: Check hydration levels
            cursor.execute("""
                SELECT AVG(value) as avg_water, COUNT(*) as days_logged
                FROM health_activities
                WHERE user_id = ? 
                AND activity_type = 'water'
                AND timestamp >= datetime('now', '-7 days')
            """, (user_id,))
            
            water_data = cursor.fetchone()
            if water_data and water_data['days_logged'] > 0:
                avg_water = water_data['avg_water']
                insights['avg_water'] = round(avg_water, 1)
                
                if avg_water < 4:  # Less than 4 glasses daily
                    insights['has_pattern'] = True
                    insights['contributing_factors'].append('low_hydration')
                    insights['recommendations'].append('increase_water_intake')
            
            # Factor 3: Check exercise patterns
            cursor.execute("""
                SELECT COUNT(*) as exercise_days, AVG(value) as avg_duration
                FROM health_activities
                WHERE user_id = ? 
                AND activity_type = 'exercise'
                AND timestamp >= datetime('now', '-7 days')
            """, (user_id,))
            
            exercise_data = cursor.fetchone()
            if exercise_data:
                exercise_days = exercise_data['exercise_days']
                insights['exercise_days'] = exercise_days
                
                if exercise_days == 0:
                    insights['has_pattern'] = True
                    insights['contributing_factors'].append('no_exercise')
                    insights['recommendations'].append('add_light_movement')
                elif exercise_days < 2:
                    insights['contributing_factors'].append('low_exercise')
            
            # Factor 4: Check how often user felt tired recently
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-7 days')
                AND (reason LIKE '%tired%' OR reason LIKE '%exhausted%')
            """, (user_id,))
            
            tired_count = cursor.fetchone()['count']
            insights['tired_frequency'] = tired_count
            
            if tired_count >= 3:
                insights['has_pattern'] = True
                insights['contributing_factors'].append('recurring_tiredness')
                if not insights['insight_text']:
                    insights['insight_text'] = f"feeling tired {tired_count} times this week"
                insights['recommendations'].append('energy_management')
            
            # Factor 5: Check correlation between sleep and mood
            if 'avg_sleep' in insights and insights['avg_sleep'] < 7:
                cursor.execute("""
                    SELECT 
                        DATE(ml.timestamp) as mood_date,
                        ml.mood_emoji,
                        ha.value as sleep_hours
                    FROM mood_logs ml
                    LEFT JOIN health_activities ha ON 
                        DATE(ha.timestamp) = DATE(ml.timestamp, '-1 day')
                        AND ha.user_id = ml.user_id
                        AND ha.activity_type = 'sleep'
                    WHERE ml.user_id = ?
                    AND ml.timestamp >= datetime('now', '-7 days')
                    AND ml.mood_emoji IN ('😟', '😢', '😐')
                """, (user_id,))
                
                mood_sleep_correlation = cursor.fetchall()
                if len(mood_sleep_correlation) >= 3:
                    insights['sleep_mood_correlation'] = True
                    insights['contributing_factors'].append('sleep_affects_mood')
            
            # Get activities that helped with tiredness before
            cursor.execute("""
                SELECT uah.activity_id, uah.activity_name, COUNT(*) as times_used,
                       AVG(CASE WHEN uah.rating >= 4 THEN 1 ELSE 0 END) as success_rate
                FROM user_activity_history uah
                WHERE uah.user_id = ?
                AND uah.reason LIKE '%tired%'
                AND uah.completed = 1
                AND uah.timestamp >= datetime('now', '-30 days')
                GROUP BY uah.activity_id
                HAVING times_used >= 2
                ORDER BY success_rate DESC, times_used DESC
                LIMIT 3
            """, (user_id,))
            
            effective_activities = cursor.fetchall()
            if effective_activities:
                insights['effective_activities'] = [
                    {
                        'name': row['activity_name'],
                        'times_used': row['times_used'],
                        'success_rate': round(row['success_rate'] * 100)
                    }
                    for row in effective_activities
                ]
        
        except Exception as e:
            logger.error(f"Error analyzing tiredness pattern: {e}")
        
        finally:
            conn.close()
        
        return insights
    
    def _analyze_stress_pattern(self, user_id: int) -> Dict:
        """Analyze patterns related to stress"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        insights = {
            'pattern_type': 'stress',
            'has_pattern': False,
            'insight_text': None,
            'recommendations': []
        }
        
        try:
            # Check stress frequency and reasons
            cursor.execute("""
                SELECT reason, COUNT(*) as count
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-7 days')
                AND mood_emoji IN ('😟', '😰', '😢')
                AND reason IS NOT NULL
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 1
            """, (user_id,))
            
            top_reason = cursor.fetchone()
            
            if top_reason and top_reason['count'] >= 3:
                insights['has_pattern'] = True
                insights['recurring_reason'] = top_reason['reason']
                insights['frequency'] = top_reason['count']
                insights['insight_text'] = f"{top_reason['reason']} stress {top_reason['count']} times this week"
                insights['recommendations'].append('address_root_cause')
            
            # Get activities that helped with stress before
            cursor.execute("""
                SELECT activity_name, COUNT(*) as times_used
                FROM user_activity_history
                WHERE user_id = ?
                AND reason LIKE '%stress%'
                AND rating >= 4
                AND timestamp >= datetime('now', '-30 days')
                GROUP BY activity_name
                ORDER BY times_used DESC
                LIMIT 2
            """, (user_id,))
            
            effective_activities = cursor.fetchall()
            if effective_activities:
                insights['effective_activities'] = [row['activity_name'] for row in effective_activities]
        
        except Exception as e:
            logger.error(f"Error analyzing stress pattern: {e}")
        
        finally:
            conn.close()
        
        return insights
    
    def _analyze_sadness_pattern(self, user_id: int) -> Dict:
        """Analyze patterns related to sadness"""
        insights = {
            'pattern_type': 'sadness',
            'has_pattern': False,
            'insight_text': None,
            'recommendations': ['emotional_support', 'social_connection']
        }
        
        # Check for prolonged sadness
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-7 days')
                AND mood_emoji IN ('😢', '😭')
            """, (user_id,))
            
            sad_count = cursor.fetchone()['count']
            
            if sad_count >= 3:
                insights['has_pattern'] = True
                insights['frequency'] = sad_count
                insights['insight_text'] = f"feeling down {sad_count} times this week"
                insights['pattern_severity'] = 'high'
        
        except Exception as e:
            logger.error(f"Error analyzing sadness pattern: {e}")
        
        finally:
            conn.close()
        
        return insights
    
    def _analyze_general_pattern(self, user_id: int, mood_emoji: str = None) -> Dict:
        """General pattern analysis"""
        insights = {
            'pattern_type': 'general',
            'has_pattern': False,
            'insight_text': None,
            'recommendations': []
        }
        
        # Just return basic insights
        return insights


def get_user_data_analyzer() -> UserDataAnalyzer:
    """Get or create UserDataAnalyzer instance"""
    return UserDataAnalyzer()
