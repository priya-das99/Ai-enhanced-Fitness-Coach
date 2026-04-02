# app/api/v1/endpoints/analytics.py
# Analytics dashboard API endpoints

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/events/summary")
def get_events_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get summary of analytics events.
    
    Returns event counts by type for the specified time period.
    """
    try:
        user_id = str(current_user['id'])
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get event counts by type
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM analytics_events
                WHERE user_id = ? AND created_at >= ?
                GROUP BY event_type
                ORDER BY count DESC
            """, (user_id, cutoff_date))
            
            event_counts = {}
            total_events = 0
            for row in cursor.fetchall():
                event_type = row[0]
                count = row[1]
                event_counts[event_type] = count
                total_events += count
            
            # Get daily event counts
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM analytics_events
                WHERE user_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (user_id, cutoff_date))
            
            daily_counts = []
            for row in cursor.fetchall():
                daily_counts.append({
                    'date': row[0],
                    'count': row[1]
                })
        
        return {
            'period_days': days,
            'total_events': total_events,
            'event_counts': event_counts,
            'daily_counts': daily_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get events summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@router.get("/mood/trends")
def get_mood_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get mood trends over time.
    
    Returns mood statistics and trends.
    """
    try:
        user_id = str(current_user['id'])
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get mood distribution
            cursor.execute("""
                SELECT mood_emoji, COUNT(*) as count
                FROM mood_logs
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY mood_emoji
                ORDER BY count DESC
            """, (user_id, cutoff_date))
            
            mood_distribution = {}
            for row in cursor.fetchall():
                mood_distribution[row[0]] = row[1]
            
            # Get average mood score
            cursor.execute("""
                SELECT AVG(CAST(mood AS REAL)) as avg_mood
                FROM mood_logs
                WHERE user_id = ? AND timestamp >= ?
            """, (user_id, cutoff_date))
            
            avg_mood = cursor.fetchone()[0] or 0
            
            # Get daily mood averages
            cursor.execute("""
                SELECT DATE(timestamp) as date, AVG(CAST(mood AS REAL)) as avg_mood
                FROM mood_logs
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (user_id, cutoff_date))
            
            daily_moods = []
            for row in cursor.fetchall():
                daily_moods.append({
                    'date': row[0],
                    'avg_mood': round(row[1], 2) if row[1] else 0
                })
            
            # Get most common reasons
            cursor.execute("""
                SELECT reason, COUNT(*) as count
                FROM mood_logs
                WHERE user_id = ? AND timestamp >= ? AND reason IS NOT NULL
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 5
            """, (user_id, cutoff_date))
            
            top_reasons = []
            for row in cursor.fetchall():
                top_reasons.append({
                    'reason': row[0],
                    'count': row[1]
                })
        
        return {
            'period_days': days,
            'avg_mood_score': round(avg_mood, 2),
            'mood_distribution': mood_distribution,
            'daily_moods': daily_moods,
            'top_reasons': top_reasons
        }
        
    except Exception as e:
        logger.error(f"Failed to get mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mood trends")

@router.get("/suggestions/performance")
def get_suggestion_performance(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get suggestion performance metrics.
    
    Returns acceptance rates and popular suggestions.
    """
    try:
        user_id = str(current_user['id'])
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get overall acceptance rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_shown,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as total_accepted
                FROM suggestion_history
                WHERE user_id = ? AND shown_at >= ?
            """, (user_id, cutoff_date))
            
            row = cursor.fetchone()
            total_shown = row[0] or 0
            total_accepted = row[1] or 0
            acceptance_rate = (total_accepted / total_shown * 100) if total_shown > 0 else 0
            
            # Get acceptance rate by suggestion
            cursor.execute("""
                SELECT 
                    suggestion_key,
                    COUNT(*) as shown_count,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted_count
                FROM suggestion_history
                WHERE user_id = ? AND shown_at >= ?
                GROUP BY suggestion_key
                ORDER BY accepted_count DESC
            """, (user_id, cutoff_date))
            
            suggestion_stats = []
            for row in cursor.fetchall():
                suggestion_key = row[0]
                shown_count = row[1]
                accepted_count = row[2]
                rate = (accepted_count / shown_count * 100) if shown_count > 0 else 0
                
                suggestion_stats.append({
                    'suggestion_key': suggestion_key,
                    'shown_count': shown_count,
                    'accepted_count': accepted_count,
                    'acceptance_rate': round(rate, 1)
                })
            
            # Get most accepted suggestions
            top_suggestions = sorted(suggestion_stats, key=lambda x: x['accepted_count'], reverse=True)[:5]
            
            # Get daily acceptance rates
            cursor.execute("""
                SELECT 
                    DATE(shown_at) as date,
                    COUNT(*) as shown,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted
                FROM suggestion_history
                WHERE user_id = ? AND shown_at >= ?
                GROUP BY DATE(shown_at)
                ORDER BY date DESC
            """, (user_id, cutoff_date))
            
            daily_rates = []
            for row in cursor.fetchall():
                date = row[0]
                shown = row[1]
                accepted = row[2]
                rate = (accepted / shown * 100) if shown > 0 else 0
                
                daily_rates.append({
                    'date': date,
                    'shown': shown,
                    'accepted': accepted,
                    'acceptance_rate': round(rate, 1)
                })
        
        return {
            'period_days': days,
            'total_shown': total_shown,
            'total_accepted': total_accepted,
            'overall_acceptance_rate': round(acceptance_rate, 1),
            'top_suggestions': top_suggestions,
            'all_suggestions': suggestion_stats,
            'daily_rates': daily_rates
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestion performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve suggestion performance")

@router.get("/behavior/metrics")
def get_behavior_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current behavior metrics for user.
    
    Returns precomputed behavior metrics.
    """
    try:
        user_id = str(current_user['id'])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    avg_sleep_7d, avg_water_7d, avg_exercise_7d,
                    hydration_score, stress_score, suggestion_acceptance_rate,
                    total_suggestions_shown, total_suggestions_accepted,
                    last_updated
                FROM user_behavior_metrics
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    'user_id': user_id,
                    'metrics_available': False,
                    'message': 'No behavior metrics available yet'
                }
            
            return {
                'user_id': user_id,
                'metrics_available': True,
                'avg_sleep_7d': round(row[0], 2) if row[0] else 0,
                'avg_water_7d': round(row[1], 2) if row[1] else 0,
                'avg_exercise_7d': round(row[2], 2) if row[2] else 0,
                'hydration_score': round(row[3], 2) if row[3] else 0,
                'stress_score': round(row[4], 2) if row[4] else 0,
                'suggestion_acceptance_rate': round(row[5], 2) if row[5] else 0,
                'total_suggestions_shown': row[6] or 0,
                'total_suggestions_accepted': row[7] or 0,
                'last_updated': row[8]
            }
        
    except Exception as e:
        logger.error(f"Failed to get behavior metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve behavior metrics")

@router.get("/activity/summary")
def get_activity_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get activity logging summary.
    
    Returns activity statistics.
    """
    try:
        user_id = current_user['id']
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get activity counts by type
            cursor.execute("""
                SELECT activity_type, COUNT(*) as count, AVG(value) as avg_value
                FROM health_activities
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY activity_type
                ORDER BY count DESC
            """, (user_id, cutoff_date))
            
            activity_stats = []
            for row in cursor.fetchall():
                activity_stats.append({
                    'activity_type': row[0],
                    'count': row[1],
                    'avg_value': round(row[2], 2) if row[2] else 0
                })
            
            # Get daily activity counts
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM health_activities
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (user_id, cutoff_date))
            
            daily_counts = []
            for row in cursor.fetchall():
                daily_counts.append({
                    'date': row[0],
                    'count': row[1]
                })
        
        return {
            'period_days': days,
            'activity_stats': activity_stats,
            'daily_counts': daily_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get activity summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity summary")
