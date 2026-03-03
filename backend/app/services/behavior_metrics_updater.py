# app/services/behavior_metrics_updater.py
# Updates user_behavior_metrics based on analytics events

import logging
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db

logger = logging.getLogger(__name__)

class BehaviorMetricsUpdater:
    """
    Updates user_behavior_metrics table based on user activity.
    
    Metrics calculated:
    - avg_sleep_7d: Average sleep hours over last 7 days
    - avg_water_7d: Average water intake over last 7 days
    - avg_exercise_7d: Average exercise minutes over last 7 days
    - hydration_score: Hydration health score (0-1)
    - stress_score: Stress level based on mood logs (0-1)
    - suggestion_acceptance_rate: % of suggestions accepted
    """
    
    def update_metrics(self, user_id: str) -> bool:
        """
        Update all behavior metrics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate metrics
            avg_sleep_7d = self._calculate_avg_sleep(user_id, days=7)
            avg_water_7d = self._calculate_avg_water(user_id, days=7)
            avg_exercise_7d = self._calculate_avg_exercise(user_id, days=7)
            hydration_score = self._calculate_hydration_score(avg_water_7d)
            stress_score = self._calculate_stress_score(user_id, days=7)
            acceptance_rate, total_shown, total_accepted = self._calculate_suggestion_acceptance(user_id)
            
            # Upsert metrics
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_behavior_metrics (
                        user_id, avg_sleep_7d, avg_water_7d, avg_exercise_7d,
                        hydration_score, stress_score, suggestion_acceptance_rate,
                        total_suggestions_shown, total_suggestions_accepted, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        avg_sleep_7d = excluded.avg_sleep_7d,
                        avg_water_7d = excluded.avg_water_7d,
                        avg_exercise_7d = excluded.avg_exercise_7d,
                        hydration_score = excluded.hydration_score,
                        stress_score = excluded.stress_score,
                        suggestion_acceptance_rate = excluded.suggestion_acceptance_rate,
                        total_suggestions_shown = excluded.total_suggestions_shown,
                        total_suggestions_accepted = excluded.total_suggestions_accepted,
                        last_updated = excluded.last_updated
                """, (
                    user_id, avg_sleep_7d, avg_water_7d, avg_exercise_7d,
                    hydration_score, stress_score, acceptance_rate,
                    total_shown, total_accepted, datetime.now().isoformat()
                ))
            
            logger.info(f"✅ Updated behavior metrics for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update behavior metrics for user {user_id}: {e}")
            return False
    
    def _calculate_avg_sleep(self, user_id: str, days: int) -> float:
        """Calculate average sleep hours over last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(value) FROM health_activities
                    WHERE user_id = ? AND activity_type = 'sleep'
                    AND timestamp >= ?
                """, (user_id, cutoff_date))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0.0
        
        except Exception as e:
            logger.error(f"Failed to calculate avg_sleep: {e}")
            return 0.0
    
    def _calculate_avg_water(self, user_id: str, days: int) -> float:
        """Calculate average water intake over last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(value) FROM health_activities
                    WHERE user_id = ? AND activity_type = 'water'
                    AND timestamp >= ?
                """, (user_id, cutoff_date))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0.0
        
        except Exception as e:
            logger.error(f"Failed to calculate avg_water: {e}")
            return 0.0
    
    def _calculate_avg_exercise(self, user_id: str, days: int) -> float:
        """Calculate average exercise minutes over last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(value) FROM health_activities
                    WHERE user_id = ? AND activity_type = 'exercise'
                    AND timestamp >= ?
                """, (user_id, cutoff_date))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0.0
        
        except Exception as e:
            logger.error(f"Failed to calculate avg_exercise: {e}")
            return 0.0
    
    def _calculate_hydration_score(self, avg_water: float) -> float:
        """
        Calculate hydration health score (0-1).
        Assumes target is 8 glasses per day.
        """
        target = 8.0
        score = min(avg_water / target, 1.0)
        return round(score, 2)
    
    def _calculate_stress_score(self, user_id: str, days: int) -> float:
        """
        Calculate stress score based on mood logs (0-1).
        Higher score = more stressed (more negative moods).
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(CAST(mood AS REAL)) FROM mood_logs
                    WHERE user_id = ? AND timestamp >= ?
                """, (user_id, cutoff_date))
                
                result = cursor.fetchone()
                
                if result and result[0]:
                    avg_mood = result[0]
                    # Convert mood (1-5 scale) to stress (0-1 scale, inverted)
                    # mood=1 (bad) → stress=1.0
                    # mood=5 (great) → stress=0.0
                    stress = (5 - avg_mood) / 4
                    return round(max(0, min(stress, 1)), 2)
        
        except Exception as e:
            logger.error(f"Failed to calculate stress_score: {e}")
        
        return 0.0
    
    def _calculate_suggestion_acceptance(self, user_id: str) -> tuple:
        """
        Calculate suggestion acceptance rate.
        
        Returns:
            (acceptance_rate, total_shown, total_accepted)
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Total shown
                cursor.execute("""
                    SELECT COUNT(*) FROM suggestion_history
                    WHERE user_id = ?
                """, (user_id,))
                total_shown = cursor.fetchone()[0] or 0
                
                # Total accepted
                cursor.execute("""
                    SELECT COUNT(*) FROM suggestion_history
                    WHERE user_id = ? AND accepted = 1
                """, (user_id,))
                total_accepted = cursor.fetchone()[0] or 0
                
                # Calculate rate
                acceptance_rate = total_accepted / total_shown if total_shown > 0 else 0.0
                
                return round(acceptance_rate, 2), total_shown, total_accepted
        
        except Exception as e:
            logger.error(f"Failed to calculate suggestion acceptance: {e}")
            return 0.0, 0, 0


# Global instance
_metrics_updater = None

def get_metrics_updater() -> BehaviorMetricsUpdater:
    """Get or create global BehaviorMetricsUpdater instance"""
    global _metrics_updater
    if _metrics_updater is None:
        _metrics_updater = BehaviorMetricsUpdater()
    return _metrics_updater
