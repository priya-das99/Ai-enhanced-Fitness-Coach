"""
Insight Generator Service - SQLite3 Compatible
Creates weekly insights and recommendations

Generates:
- Weekly mood summaries
- Activity effectiveness reports
- Pattern-based recommendations
- Personalized tips
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class InsightGeneratorSQLite:
    """Generates insights from user data (SQLite3 compatible)"""
    
    def __init__(self):
        pass
    
    def generate_weekly_insight(self, user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
        """Generate comprehensive weekly insight"""
        try:
            cursor = db.cursor()
            
            # Calculate date ranges
            now = datetime.now()
            one_week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)
            
            # Get this week's mood data
            cursor.execute("""
                SELECT mood_emoji, reason, mood_intensity, timestamp
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (user_id, one_week_ago.isoformat()))
            
            this_week_moods = cursor.fetchall()
            
            # Get last week's mood data
            cursor.execute("""
                SELECT mood_emoji, reason, mood_intensity, timestamp
                FROM mood_logs
                WHERE user_id = ?
                AND timestamp >= ?
                AND timestamp < ?
                ORDER BY timestamp DESC
            """, (user_id, two_weeks_ago.isoformat(), one_week_ago.isoformat()))
            
            last_week_moods = cursor.fetchall()
            
            # Get this week's activity data
            cursor.execute("""
                SELECT activity_id, activity_name, timestamp
                FROM user_activity_history
                WHERE user_id = ?
                AND timestamp >= ?
                AND completed = 1
                ORDER BY timestamp DESC
            """, (user_id, one_week_ago.isoformat()))
            
            this_week_activities = cursor.fetchall()
            
            # Get last week's activity data
            cursor.execute("""
                SELECT activity_id, activity_name, timestamp
                FROM user_activity_history
                WHERE user_id = ?
                AND timestamp >= ?
                AND timestamp < ?
                AND completed = 1
                ORDER BY timestamp DESC
            """, (user_id, two_weeks_ago.isoformat(), one_week_ago.isoformat()))
            
            last_week_activities = cursor.fetchall()
            
            # Calculate metrics
            mood_summary = self._calculate_mood_summary(this_week_moods)
            activity_summary = self._calculate_activity_summary(this_week_activities)
            comparison = self._compare_weeks(
                this_week_moods, last_week_moods,
                this_week_activities, last_week_activities
            )
            
            # Get top activities
            top_activities = self._get_top_activities(user_id, db)
            
            # Get patterns (using pattern_detector_sqlite)
            from app.services.pattern_detector_sqlite import PatternDetector
            pattern_detector = PatternDetector()
            patterns = pattern_detector.detect_all_patterns(user_id, db)
            
            # Convert patterns to actionable insights
            actionable_patterns = self._convert_patterns_to_insights(patterns)
            
            return {
                'period': 'This Week',
                'mood_summary': mood_summary,
                'activity_summary': activity_summary,
                'comparison': comparison,
                'patterns': actionable_patterns[:3],  # Top 3 patterns
                'top_activities': top_activities[:3],  # Top 3 activities
                'recommendations': self._generate_recommendations(actionable_patterns, mood_summary)
            }
        
        except Exception as e:
            logger.error(f"Failed to generate weekly insight for user {user_id}: {e}", exc_info=True)
            return None
    
    def _calculate_mood_summary(self, mood_logs: List) -> Dict:
        """Calculate mood statistics"""
        if not mood_logs:
            return {
                'total_logs': 0,
                'avg_intensity': 0,
                'most_common_mood': None,
                'most_common_reason': None
            }
        
        # Count moods
        mood_counts = {}
        reasons = []
        intensities = []
        
        for log in mood_logs:
            mood_emoji, reason, intensity, timestamp = log
            mood_counts[mood_emoji] = mood_counts.get(mood_emoji, 0) + 1
            if reason:
                reasons.append(reason)
            if intensity:
                intensities.append(intensity)
        
        most_common_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else None
        most_common_reason = max(set(reasons), key=reasons.count) if reasons else None
        avg_intensity = sum(intensities) / len(intensities) if intensities else 5
        
        return {
            'total_logs': len(mood_logs),
            'avg_intensity': round(avg_intensity, 1),
            'most_common_mood': most_common_mood,
            'most_common_reason': most_common_reason,
            'mood_distribution': mood_counts
        }
    
    def _calculate_activity_summary(self, activities: List) -> Dict:
        """Calculate activity statistics"""
        if not activities:
            return {
                'total_completions': 0,
                'unique_activities': 0,
                'most_completed': None
            }
        
        activity_counts = {}
        for activity in activities:
            activity_id, activity_name, timestamp = activity
            activity_counts[activity_name] = activity_counts.get(activity_name, 0) + 1
        
        most_completed = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else None
        
        return {
            'total_completions': len(activities),
            'unique_activities': len(activity_counts),
            'most_completed': most_completed,
            'activity_distribution': activity_counts
        }
    
    def _compare_weeks(self, this_week_moods, last_week_moods,
                      this_week_activities, last_week_activities) -> Dict:
        """Compare this week to last week"""
        mood_change = len(this_week_moods) - len(last_week_moods)
        activity_change = len(this_week_activities) - len(last_week_activities)
        
        # Calculate average intensity change
        this_week_intensity = sum(m[2] or 5 for m in this_week_moods) / len(this_week_moods) if this_week_moods else 5
        last_week_intensity = sum(m[2] or 5 for m in last_week_moods) / len(last_week_moods) if last_week_moods else 5
        intensity_change = this_week_intensity - last_week_intensity
        
        return {
            'mood_logs_change': mood_change,
            'activity_completions_change': activity_change,
            'intensity_change': round(intensity_change, 1),
            'trend': 'improving' if intensity_change < 0 else 'stable' if abs(intensity_change) < 1 else 'declining'
        }
    
    def _get_top_activities(self, user_id: int, db: sqlite3.Connection) -> List[Dict]:
        """Get top performing activities based on feedback"""
        try:
            cursor = db.cursor()
            four_weeks_ago = datetime.now() - timedelta(days=28)
            
            cursor.execute("""
                SELECT activity_id, helpful
                FROM activity_feedback
                WHERE user_id = ?
                AND created_at >= ?
            """, (user_id, four_weeks_ago.isoformat()))
            
            feedback_records = cursor.fetchall()
            
            if not feedback_records:
                return []
            
            # Calculate success rates
            activity_stats = {}
            
            for record in feedback_records:
                activity_id, helpful = record
                if activity_id not in activity_stats:
                    activity_stats[activity_id] = {'helpful': 0, 'total': 0}
                
                activity_stats[activity_id]['total'] += 1
                if helpful:
                    activity_stats[activity_id]['helpful'] += 1
            
            # Calculate success rates and sort
            top_activities = []
            for activity_id, stats in activity_stats.items():
                if stats['total'] >= 2:  # At least 2 tries
                    success_rate = stats['helpful'] / stats['total']
                    top_activities.append({
                        'activity': activity_id,
                        'success_rate': success_rate,
                        'total_tries': stats['total'],
                        'helpful_count': stats['helpful']
                    })
            
            # Sort by success rate, then by total tries
            top_activities.sort(key=lambda x: (x['success_rate'], x['total_tries']), reverse=True)
            
            return top_activities
        
        except Exception as e:
            logger.error(f"Failed to get top activities: {e}")
            return []
    
    def _convert_patterns_to_insights(self, patterns: Dict) -> List[Dict]:
        """Convert detected patterns to actionable insights"""
        insights = []
        
        # Day patterns
        for pattern in patterns.get('day_patterns', []):
            insights.append({
                'type': 'day_pattern',
                'insight': pattern['description'],
                'suggestion': f"Create a {pattern['day']} routine to manage this better",
                'confidence': pattern['confidence']
            })
        
        # Activity patterns
        for pattern in patterns.get('activity_patterns', []):
            insights.append({
                'type': 'activity_pattern',
                'insight': pattern['description'],
                'suggestion': f"Keep using {pattern['activity']} when feeling {pattern['reason']}",
                'confidence': pattern['confidence']
            })
        
        # Mood improvement patterns
        for pattern in patterns.get('mood_improvement_patterns', []):
            insights.append({
                'type': 'mood_improvement',
                'insight': pattern['description'],
                'suggestion': f"Try {pattern['activity']} more often - it works {int(pattern['success_rate']*100)}% of the time",
                'confidence': pattern['confidence']
            })
        
        # Sort by confidence
        insights.sort(key=lambda x: x['confidence'], reverse=True)
        
        return insights
    
    def _generate_recommendations(self, patterns: List[Dict], mood_summary: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Pattern-based recommendations
        for pattern in patterns[:2]:  # Top 2 patterns
            recommendations.append(pattern['suggestion'])
        
        # Mood-based recommendations
        if mood_summary.get('most_common_reason'):
            reason = mood_summary['most_common_reason']
            recommendations.append(f"Focus on activities that help with {reason}")
        
        # Consistency recommendation
        if mood_summary['total_logs'] < 5:
            recommendations.append("Try logging your mood daily to track patterns better")
        
        return recommendations[:3]  # Max 3 recommendations
    
    def format_insight_message(self, insight: Dict) -> str:
        """Format insight as a friendly message"""
        lines = []
        
        lines.append(f"📊 {insight['period']} Summary:")
        lines.append("")
        
        # Mood summary
        mood = insight['mood_summary']
        if mood['total_logs'] > 0:
            lines.append(f"🎭 Mood Tracking:")
            lines.append(f"  • Logged {mood['total_logs']} times")
            if mood['most_common_mood']:
                lines.append(f"  • Most common: {mood['most_common_mood']}")
            if mood['most_common_reason']:
                lines.append(f"  • Main reason: {mood['most_common_reason']}")
        
        lines.append("")
        
        # Activity summary
        activity = insight['activity_summary']
        if activity['total_completions'] > 0:
            lines.append(f"💪 Activities:")
            lines.append(f"  • Completed {activity['total_completions']} activities")
            if activity['most_completed']:
                lines.append(f"  • Favorite: {activity['most_completed']}")
        
        lines.append("")
        
        # Comparison
        comp = insight['comparison']
        if comp['mood_logs_change'] != 0:
            change = "up" if comp['mood_logs_change'] > 0 else "down"
            lines.append(f"📈 Compared to last week:")
            lines.append(f"  • Mood logs: {change} by {abs(comp['mood_logs_change'])}")
            lines.append(f"  • Trend: {comp['trend']}")
            lines.append("")
        
        # Top activities
        if insight['top_activities']:
            lines.append("🌟 What's Working:")
            for i, activity in enumerate(insight['top_activities'][:2], 1):
                rate = int(activity['success_rate'] * 100)
                lines.append(f"  {i}. {activity['activity']} ({rate}% success rate)")
            lines.append("")
        
        # Patterns
        if insight['patterns']:
            lines.append("🔍 Insights I Noticed:")
            for i, pattern in enumerate(insight['patterns'], 1):
                lines.append(f"  {i}. {pattern['insight']}")
            lines.append("")
        
        # Recommendations
        if insight['recommendations']:
            lines.append("💡 Recommendations:")
            for i, rec in enumerate(insight['recommendations'], 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)
