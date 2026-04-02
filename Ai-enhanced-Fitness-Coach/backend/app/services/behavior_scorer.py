# app/services/behavior_scorer.py
# Deterministic behavior-based scoring for suggestions

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import get_db

logger = logging.getLogger(__name__)

class BehaviorScorer:
    """
    Deterministic scoring system for wellness suggestions.
    
    Scoring factors:
    1. Reason relevance (keyword matching)
    2. Time of day appropriateness
    3. User history preferences
    4. Fatigue penalty (recently shown suggestions)
    5. Acceptance rate boost
    """
    
    def __init__(self):
        # Reason-to-suggestion mapping
        self.reason_mappings = {
            'work': ['breathing', 'take_break', 'stretching', 'short_walk'],
            'relationship': ['meditation', 'call_friend', 'journaling', 'short_walk'],
            'family': ['meditation', 'call_friend', 'short_walk', 'breathing'],
            'friend': ['call_friend', 'short_walk', 'meditation'],
            'education': ['take_break', 'short_walk', 'stretching', 'breathing'],
            'exercise': ['stretching', 'hydrate', 'power_nap', 'breathing'],
            'food': ['short_walk', 'hydrate', 'stretching'],
            'travel': ['breathing', 'meditation', 'stretching'],
            'tired': ['power_nap', 'hydrate', 'short_walk', 'breathing'],
            'stress': ['breathing', 'meditation', 'short_walk', 'stretching'],
            'anxiety': ['breathing', 'meditation', 'journaling'],
        }
        
        # Time-based preferences
        self.time_preferences = {
            'morning': ['stretching', 'breathing', 'short_walk', 'hydrate'],
            'afternoon': ['take_break', 'short_walk', 'breathing', 'stretching'],
            'evening': ['meditation', 'breathing', 'stretching', 'journaling'],
            'night': ['breathing', 'meditation', 'journaling'],
        }
    
    def score_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        mood_emoji: str,
        reason: Optional[str],
        user_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score and rank suggestions based on multiple factors.
        
        Args:
            suggestions: List of suggestion dicts with 'id', 'name', etc.
            mood_emoji: User's mood emoji
            reason: Reason for mood (optional)
            user_id: User identifier
            context: Context dict with time_period, is_work_hours, etc.
            
        Returns:
            List of suggestions with 'score' field added, sorted by score (descending)
        """
        scored_suggestions = []
        
        # Get user behavior metrics
        user_metrics = self._get_user_metrics(user_id)
        
        # Get recent suggestion history (for fatigue penalty)
        recent_suggestions = self._get_recent_suggestions(user_id, days=7)
        
        for suggestion in suggestions:
            suggestion_id = suggestion.get('id') or suggestion.get('suggestion_key')
            score = 0
            
            # 1. Reason relevance (0-10 points)
            if reason:
                score += self._score_reason_relevance(suggestion_id, reason)
            
            # 2. Time of day appropriateness (0-5 points)
            score += self._score_time_appropriateness(suggestion_id, context)
            
            # 3. User history preferences (0-8 points)
            score += self._score_user_history(suggestion_id, user_metrics, reason)
            
            # 4. Fatigue penalty (-5 to 0 points)
            score += self._score_fatigue_penalty(suggestion_id, recent_suggestions)
            
            # 5. Acceptance rate boost (0-5 points)
            score += self._score_acceptance_rate(suggestion_id, user_metrics)
            
            # Add score to suggestion
            suggestion_with_score = suggestion.copy()
            suggestion_with_score['score'] = score
            scored_suggestions.append(suggestion_with_score)
            
            logger.debug(f"  {suggestion_id}: score={score}")
        
        # Sort by score (descending)
        scored_suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_suggestions
    
    def _score_reason_relevance(self, suggestion_id: str, reason: str) -> float:
        """Score based on reason-to-suggestion mapping (0-10 points)"""
        reason_lower = reason.lower()
        score = 0
        
        for keyword, suggestions in self.reason_mappings.items():
            if keyword in reason_lower:
                if suggestion_id in suggestions:
                    # Position in list determines score
                    position = suggestions.index(suggestion_id)
                    score = max(score, 10 - (position * 2))
        
        return score
    
    def _score_time_appropriateness(self, suggestion_id: str, context: Dict[str, Any]) -> float:
        """Score based on time of day (0-5 points)"""
        time_period = context.get('time_period', 'day')
        is_work_hours = context.get('is_work_hours', False)
        
        score = 0
        
        # Time period matching
        if time_period in self.time_preferences:
            if suggestion_id in self.time_preferences[time_period]:
                position = self.time_preferences[time_period].index(suggestion_id)
                score = 5 - position
        
        # Work hours constraint (penalize non-work-friendly activities)
        if is_work_hours:
            work_friendly = ['breathing', 'stretching', 'take_break', 'hydrate', 'meditation']
            if suggestion_id not in work_friendly:
                score -= 2
        
        return max(0, score)
    
    def _score_user_history(self, suggestion_id: str, user_metrics: Dict, reason: Optional[str]) -> float:
        """Score based on user's historical preferences (0-8 points)"""
        # This will be enhanced once we have more user history data
        # For now, use acceptance rate as a proxy
        acceptance_rate = user_metrics.get('suggestion_acceptance_rate', 0)
        
        # If user has good acceptance rate, slightly boost all suggestions
        if acceptance_rate > 0.5:
            return 2
        
        return 0
    
    def _score_fatigue_penalty(self, suggestion_id: str, recent_suggestions: List[Dict]) -> float:
        """Apply fatigue penalty for recently shown suggestions (-5 to 0 points)"""
        # Count how many times this suggestion was shown recently
        count = sum(1 for s in recent_suggestions if s['suggestion_key'] == suggestion_id)
        
        if count == 0:
            return 0
        elif count == 1:
            return -1
        elif count == 2:
            return -3
        else:
            return -5
    
    def _score_acceptance_rate(self, suggestion_id: str, user_metrics: Dict) -> float:
        """Boost score based on overall acceptance rate (0-5 points)"""
        acceptance_rate = user_metrics.get('suggestion_acceptance_rate', 0)
        
        # Higher acceptance rate = more willing to try suggestions
        return acceptance_rate * 5
    
    def _get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior metrics from database"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT avg_sleep_7d, avg_water_7d, avg_exercise_7d,
                           hydration_score, stress_score, suggestion_acceptance_rate,
                           total_suggestions_shown, total_suggestions_accepted
                    FROM user_behavior_metrics
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'avg_sleep_7d': row[0] or 0,
                        'avg_water_7d': row[1] or 0,
                        'avg_exercise_7d': row[2] or 0,
                        'hydration_score': row[3] or 0,
                        'stress_score': row[4] or 0,
                        'suggestion_acceptance_rate': row[5] or 0,
                        'total_suggestions_shown': row[6] or 0,
                        'total_suggestions_accepted': row[7] or 0,
                    }
        
        except Exception as e:
            logger.error(f"Failed to get user metrics: {e}")
        
        return {}
    
    def _get_recent_suggestions(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get recently shown suggestions for fatigue calculation"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT suggestion_key, shown_at, accepted
                    FROM suggestion_history
                    WHERE user_id = ? AND shown_at >= ?
                    ORDER BY shown_at DESC
                """, (user_id, cutoff_date))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'suggestion_key': row[0],
                        'shown_at': row[1],
                        'accepted': row[2]
                    }
                    for row in rows
                ]
        
        except Exception as e:
            logger.error(f"Failed to get recent suggestions: {e}")
        
        return []


# Global instance
_behavior_scorer = None

def get_behavior_scorer() -> BehaviorScorer:
    """Get or create global BehaviorScorer instance"""
    global _behavior_scorer
    if _behavior_scorer is None:
        _behavior_scorer = BehaviorScorer()
    return _behavior_scorer


# Phase 2: Event handlers for behavior metrics updates
class BehaviorMetricsUpdater:
    """Updates user behavior metrics based on events (Phase 2)"""
    
    def update_mood_metrics(self, user_id: str, event: dict):
        """Update mood-related metrics"""
        try:
            mood_emoji = event.get('mood')
            mood_value = event.get('mood_value', 5)
            
            logger.info(f"[Phase 2] Updating mood metrics for user {user_id}")
            
            # This would update mood frequency, patterns, etc.
            # For now, just log it
            logger.info(f"[Phase 2] Mood logged: {mood_emoji} (value: {mood_value})")
            
        except Exception as e:
            logger.error(f"Failed to update mood metrics: {e}")
    
    def update_activity_metrics(self, user_id: str, event: dict):
        """Update activity-related metrics"""
        try:
            activity_type = event.get('activity_type')
            value = event.get('value')
            unit = event.get('unit')
            
            logger.info(f"[Phase 2] Updating activity metrics for user {user_id}")
            logger.info(f"[Phase 2] Activity logged: {activity_type} = {value} {unit}")
            
            # Update relevant metrics in user_behavior_metrics table
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Update based on activity type
                if activity_type == 'water':
                    cursor.execute("""
                        UPDATE user_behavior_metrics
                        SET avg_water_7d = (
                            SELECT AVG(value)
                            FROM health_activities
                            WHERE user_id = ? AND activity_type = 'water'
                            AND logged_at >= datetime('now', '-7 days')
                        ),
                        hydration_score = CASE
                            WHEN avg_water_7d >= 2000 THEN 100
                            WHEN avg_water_7d >= 1500 THEN 75
                            WHEN avg_water_7d >= 1000 THEN 50
                            ELSE 25
                        END,
                        updated_at = datetime('now')
                        WHERE user_id = ?
                    """, (user_id, user_id))
                    
                elif activity_type == 'sleep':
                    cursor.execute("""
                        UPDATE user_behavior_metrics
                        SET avg_sleep_7d = (
                            SELECT AVG(value)
                            FROM health_activities
                            WHERE user_id = ? AND activity_type = 'sleep'
                            AND logged_at >= datetime('now', '-7 days')
                        ),
                        updated_at = datetime('now')
                        WHERE user_id = ?
                    """, (user_id, user_id))
                    
                elif activity_type == 'exercise':
                    cursor.execute("""
                        UPDATE user_behavior_metrics
                        SET avg_exercise_7d = (
                            SELECT AVG(value)
                            FROM health_activities
                            WHERE user_id = ? AND activity_type = 'exercise'
                            AND logged_at >= datetime('now', '-7 days')
                        ),
                        updated_at = datetime('now')
                        WHERE user_id = ?
                    """, (user_id, user_id))
                
                logger.info(f"[Phase 2] Behavior metrics updated successfully")
                
        except Exception as e:
            logger.error(f"Failed to update activity metrics: {e}")


# Add methods to BehaviorScorer for Phase 2 compatibility
BehaviorScorer.update_mood_metrics = BehaviorMetricsUpdater().update_mood_metrics
BehaviorScorer.update_activity_metrics = BehaviorMetricsUpdater().update_activity_metrics
