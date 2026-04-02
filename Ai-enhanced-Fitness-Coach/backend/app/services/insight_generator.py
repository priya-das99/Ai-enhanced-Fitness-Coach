"""
Insight Generator Service - Creates weekly insights and recommendations

Generates:
- Weekly mood summaries
- Activity effectiveness reports
- Pattern-based recommendations
- Personalized tips
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.user import MoodLog, ActivityCompletion
from app.models.activity import ActivityFeedback
from app.services.pattern_detector import PatternDetector


class InsightGenerator:
    """Generates insights from user data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pattern_detector = PatternDetector(db)
    
    def generate_weekly_insight(self, user_id: int) -> Dict:
        """Generate comprehensive weekly insight"""
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        # Get this week's data
        this_week_moods = self.db.query(MoodLog).filter(
            and_(
                MoodLog.user_id == user_id,
                MoodLog.created_at >= one_week_ago
            )
        ).all()
        
        this_week_activities = self.db.query(ActivityCompletion).filter(
            and_(
                ActivityCompletion.user_id == user_id,
                ActivityCompletion.completed_at >= one_week_ago
            )
        ).all()
        
        # Get last week's data for comparison
        last_week_moods = self.db.query(MoodLog).filter(
            and_(
                MoodLog.user_id == user_id,
                MoodLog.created_at >= two_weeks_ago,
                MoodLog.created_at < one_week_ago
            )
        ).all()
        
        last_week_activities = self.db.query(ActivityCompletion).filter(
            and_(
                ActivityCompletion.user_id == user_id,
                ActivityCompletion.completed_at >= two_weeks_ago,
                ActivityCompletion.completed_at < one_week_ago
            )
        ).all()
        
        # Calculate metrics
        mood_summary = self._calculate_mood_summary(this_week_moods)
        activity_summary = self._calculate_activity_summary(this_week_activities)
        comparison = self._compare_weeks(this_week_moods, last_week_moods, 
                                        this_week_activities, last_week_activities)
        
        # Get patterns
        patterns = self.pattern_detector.get_actionable_insights(user_id)
        
        # Get top activities
        top_activities = self._get_top_activities(user_id)
        
        return {
            'period': 'This Week',
            'mood_summary': mood_summary,
            'activity_summary': activity_summary,
            'comparison': comparison,
            'patterns': patterns[:3],  # Top 3 patterns
            'top_activities': top_activities[:3],  # Top 3 activities
            'recommendations': self._generate_recommendations(patterns, mood_summary)
        }
    
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
            mood_counts[log.mood_emoji] = mood_counts.get(log.mood_emoji, 0) + 1
            if log.reason:
                reasons.append(log.reason)
            if log.intensity:
                intensities.append(log.intensity)
        
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
            activity_counts[activity.activity_id] = activity_counts.get(activity.activity_id, 0) + 1
        
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
        this_week_intensity = sum(m.intensity or 5 for m in this_week_moods) / len(this_week_moods) if this_week_moods else 5
        last_week_intensity = sum(m.intensity or 5 for m in last_week_moods) / len(last_week_moods) if last_week_moods else 5
        intensity_change = this_week_intensity - last_week_intensity
        
        return {
            'mood_logs_change': mood_change,
            'activity_completions_change': activity_change,
            'intensity_change': round(intensity_change, 1),
            'trend': 'improving' if intensity_change < 0 else 'stable' if abs(intensity_change) < 1 else 'declining'
        }
    
    def _get_top_activities(self, user_id: int) -> List[Dict]:
        """Get top performing activities based on feedback"""
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        
        feedback_records = self.db.query(ActivityFeedback).filter(
            and_(
                ActivityFeedback.user_id == user_id,
                ActivityFeedback.created_at >= four_weeks_ago
            )
        ).all()
        
        # Calculate success rates
        activity_stats = {}
        
        for feedback in feedback_records:
            activity_id = feedback.activity_id
            if activity_id not in activity_stats:
                activity_stats[activity_id] = {'helpful': 0, 'total': 0}
            
            activity_stats[activity_id]['total'] += 1
            if feedback.helpful:
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
    
    def _generate_recommendations(self, patterns: List[Dict], mood_summary: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Pattern-based recommendations
        for pattern in patterns[:2]:  # Top 2 patterns
            recommendations.append(pattern['suggestion'])
        
        # Mood-based recommendations
        if mood_summary['most_common_reason']:
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
