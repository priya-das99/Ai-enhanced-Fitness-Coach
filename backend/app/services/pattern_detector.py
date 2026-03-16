"""
Pattern Detection Service - Identifies recurring patterns in user behavior

Detects:
- Time-based patterns (Monday stress, 3 PM fatigue)
- Activity patterns (always chooses meditation when anxious)
- Mood patterns (better mood after exercise)
- Frequency patterns (hasn't logged in 3 days)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.user import MoodLog, ActivityCompletion
from app.models.activity import ActivityFeedback


class PatternDetector:
    """Detects behavioral patterns from user data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_all_patterns(self, user_id: int) -> Dict:
        """Detect all patterns for a user"""
        return {
            'time_patterns': self.detect_time_patterns(user_id),
            'day_patterns': self.detect_day_patterns(user_id),
            'activity_patterns': self.detect_activity_patterns(user_id),
            'mood_improvement_patterns': self.detect_mood_improvement_patterns(user_id),
            'absence_pattern': self.detect_absence_pattern(user_id)
        }
    
    def detect_day_patterns(self, user_id: int) -> List[Dict]:
        """Detect patterns by day of week (e.g., stressed every Monday)"""
        patterns = []
        
        # Look at last 4 weeks
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        
        mood_logs = self.db.query(MoodLog).filter(
            and_(
                MoodLog.user_id == user_id,
                MoodLog.created_at >= four_weeks_ago
            )
        ).all()
        
        # Group by day of week
        day_moods = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
        
        for log in mood_logs:
            day_of_week = log.created_at.weekday()
            day_moods[day_of_week].append({
                'emoji': log.mood_emoji,
                'reason': log.reason,
                'intensity': log.intensity or 5
            })
        
        # Analyze each day
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_num, moods in day_moods.items():
            if len(moods) >= 3:  # Need at least 3 occurrences
                # Check for negative mood pattern
                negative_count = sum(1 for m in moods if m['emoji'] in ['😟', '😢', '😠', '😰', '😞'])
                
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
    
    def detect_time_patterns(self, user_id: int) -> List[Dict]:
        """Detect patterns by time of day (e.g., tired at 3 PM)"""
        patterns = []
        
        # Look at last 2 weeks
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        mood_logs = self.db.query(MoodLog).filter(
            and_(
                MoodLog.user_id == user_id,
                MoodLog.created_at >= two_weeks_ago
            )
        ).all()
        
        # Group by hour
        hour_moods = {i: [] for i in range(24)}
        
        for log in mood_logs:
            hour = log.created_at.hour
            hour_moods[hour].append({
                'emoji': log.mood_emoji,
                'reason': log.reason
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
    
    def detect_activity_patterns(self, user_id: int) -> List[Dict]:
        """Detect which activities user prefers for specific situations"""
        patterns = []
        
        # Look at last 4 weeks
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        
        completions = self.db.query(ActivityCompletion).filter(
            and_(
                ActivityCompletion.user_id == user_id,
                ActivityCompletion.completed_at >= four_weeks_ago
            )
        ).all()
        
        # Group by reason
        reason_activities = {}
        
        for completion in completions:
            reason = completion.reason or 'general'
            if reason not in reason_activities:
                reason_activities[reason] = []
            reason_activities[reason].append(completion.activity_id)
        
        # Find patterns
        for reason, activities in reason_activities.items():
            if len(activities) >= 3:
                # Find most common activity
                activity_counts = {}
                for activity in activities:
                    activity_counts[activity] = activity_counts.get(activity, 0) + 1
                
                most_common = max(activity_counts.items(), key=lambda x: x[1])
                
                if most_common[1] >= 3:  # Activity used at least 3 times
                    patterns.append({
                        'type': 'activity_pattern',
                        'reason': reason,
                        'activity': most_common[0],
                        'pattern': f"{most_common[0]}_for_{reason}",
                        'description': f"You often choose {most_common[0]} when feeling {reason}",
                        'occurrences': most_common[1],
                        'confidence': most_common[1] / len(activities)
                    })
        
        return patterns
    
    def detect_mood_improvement_patterns(self, user_id: int) -> List[Dict]:
        """Detect which activities consistently improve mood"""
        patterns = []
        
        # Get feedback from last 4 weeks
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        
        feedback_records = self.db.query(ActivityFeedback).filter(
            and_(
                ActivityFeedback.user_id == user_id,
                ActivityFeedback.created_at >= four_weeks_ago
            )
        ).all()
        
        # Group by activity
        activity_feedback = {}
        
        for feedback in feedback_records:
            activity_id = feedback.activity_id
            if activity_id not in activity_feedback:
                activity_feedback[activity_id] = {'helpful': 0, 'total': 0}
            
            activity_feedback[activity_id]['total'] += 1
            if feedback.helpful:
                activity_feedback[activity_id]['helpful'] += 1
        
        # Find high-success activities
        for activity_id, stats in activity_feedback.items():
            if stats['total'] >= 3:  # At least 3 tries
                success_rate = stats['helpful'] / stats['total']
                
                if success_rate >= 0.75:  # 75% or higher success rate
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
    
    def detect_absence_pattern(self, user_id: int) -> Optional[Dict]:
        """Detect if user hasn't logged in recently"""
        # Get last mood log
        last_log = self.db.query(MoodLog).filter(
            MoodLog.user_id == user_id
        ).order_by(MoodLog.created_at.desc()).first()
        
        if not last_log:
            return None
        
        days_since_last = (datetime.utcnow() - last_log.created_at).days
        
        if days_since_last >= 3:
            return {
                'type': 'absence',
                'days_absent': days_since_last,
                'last_activity': last_log.created_at,
                'description': f"You haven't logged mood in {days_since_last} days"
            }
        
        return None
    
    def get_actionable_insights(self, user_id: int) -> List[Dict]:
        """Get patterns that can be acted upon with suggestions"""
        all_patterns = self.detect_all_patterns(user_id)
        actionable = []
        
        # Day patterns → Suggest preventive routine
        for pattern in all_patterns['day_patterns']:
            if pattern['confidence'] >= 0.6:  # 60% confidence
                actionable.append({
                    'insight': pattern['description'],
                    'action': f"Create a {pattern['day']} morning routine",
                    'suggestion': f"Try a preventive activity on {pattern['day']} mornings",
                    'pattern': pattern
                })
        
        # Time patterns → Suggest scheduled activity
        for pattern in all_patterns['time_patterns']:
            if pattern['confidence'] >= 0.5:  # 50% confidence
                hour = pattern['hour']
                actionable.append({
                    'insight': pattern['description'],
                    'action': f"Schedule activity at {hour-1}:00",
                    'suggestion': f"Try a quick activity before {hour}:00 to prevent this",
                    'pattern': pattern
                })
        
        # Activity patterns → Reinforce successful choices
        for pattern in all_patterns['activity_patterns']:
            if pattern['confidence'] >= 0.6:
                actionable.append({
                    'insight': pattern['description'],
                    'action': f"Prioritize {pattern['activity']} for {pattern['reason']}",
                    'suggestion': f"Make {pattern['activity']} your go-to for {pattern['reason']}",
                    'pattern': pattern
                })
        
        # Mood improvement patterns → Highlight what works
        for pattern in all_patterns['mood_improvement_patterns']:
            if pattern['success_rate'] >= 0.8:  # 80% success
                actionable.append({
                    'insight': pattern['description'],
                    'action': f"Suggest {pattern['activity']} more often",
                    'suggestion': f"{pattern['activity']} works {int(pattern['success_rate']*100)}% of the time for you!",
                    'pattern': pattern
                })
        
        return actionable
