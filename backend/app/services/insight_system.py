"""
Hybrid Insight System
Combines rule-based pattern detection with LLM message generation
"""

from .pattern_detector import PatternDetector
from .llm_insight_generator import LLMInsightGenerator
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class InsightSystem:
    """Hybrid system: Fast pattern detection + Natural LLM messages"""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.llm_generator = LLMInsightGenerator()
    
    def generate_insights(self, user_id: int) -> List[Dict]:
        """
        Generate prioritized insights for user
        
        Returns:
            List of insights with messages and actions
        """
        
        # Step 1: Detect all patterns (rule-based, fast)
        logger.info(f"Detecting patterns for user {user_id}")
        patterns = self.pattern_detector.detect_all_patterns(user_id)
        
        # Step 2: Identify actionable patterns
        actionable_patterns = self._identify_actionable_patterns(patterns)
        
        if not actionable_patterns:
            logger.info(f"No actionable patterns for user {user_id}")
            return []
        
        # Step 3: Prioritize patterns
        prioritized = self._prioritize_patterns(actionable_patterns)
        
        # Step 4: Generate natural messages with LLM (top 3 only)
        insights = []
        for pattern in prioritized[:3]:
            try:
                # Get user context for LLM
                user_context = self._build_user_context(patterns)
                
                # Generate natural message with LLM
                message = self.llm_generator.generate_insight_message(
                    pattern_type=pattern['type'],
                    pattern_data=pattern['data'],
                    user_context=user_context,
                    priority=pattern['priority']
                )
                
                # Determine action
                action = self._determine_action(pattern)
                
                insights.append({
                    'type': pattern['type'],
                    'priority': pattern['priority'],
                    'message': message,
                    'action': action,
                    'pattern_data': pattern['data']
                })
                
                logger.info(f"Generated insight: {pattern['type']} (priority: {pattern['priority']})")
                
            except Exception as e:
                logger.error(f"Failed to generate insight for pattern {pattern['type']}: {e}")
                continue
        
        return insights
    
    def get_greeting_insight(self, user_id: int) -> Optional[Dict]:
        """
        Get top priority insight for greeting
        
        Returns:
            Single insight or None
        """
        insights = self.generate_insights(user_id)
        return insights[0] if insights else None
    
    def _identify_actionable_patterns(self, patterns: Dict) -> List[Dict]:
        """Identify patterns that warrant user communication"""
        actionable = []
        
        mood_patterns = patterns['mood_patterns']
        activity_patterns = patterns['activity_patterns']
        engagement_patterns = patterns['engagement_patterns']
        effectiveness_patterns = patterns['effectiveness_patterns']
        
        # Pattern 1: Stress-inactivity cycle (HIGH PRIORITY)
        if mood_patterns['has_prolonged_stress'] and activity_patterns['activity_drop']:
            actionable.append({
                'type': 'stress_inactivity_cycle',
                'priority': 'high',
                'data': {
                    'stressed_days': mood_patterns['consecutive_negative_days'],
                    'reason': mood_patterns['recurring_reason'],
                    'current_activities': activity_patterns['current_week_count'],
                    'baseline_activities': activity_patterns['baseline_per_week'],
                    'drop_percentage': activity_patterns['activity_drop_percentage']
                }
            })
        
        # Pattern 2: Activity streak (LOW PRIORITY - celebration)
        elif activity_patterns['has_streak']:
            actionable.append({
                'type': 'activity_streak',
                'priority': 'low',
                'data': {
                    'streak': activity_patterns['streak'],
                    'total_activities': activity_patterns['current_week_count']
                }
            })
        
        # Pattern 3: Low activity without stress (MEDIUM PRIORITY)
        elif activity_patterns['activity_drop'] and not mood_patterns['has_prolonged_stress']:
            actionable.append({
                'type': 'low_activity',
                'priority': 'medium',
                'data': {
                    'current_week': activity_patterns['current_week_count'],
                    'baseline': activity_patterns['baseline_per_week'],
                    'drop_percentage': activity_patterns['activity_drop_percentage']
                }
            })
        
        # Pattern 4: Proven solution available (MEDIUM PRIORITY)
        if mood_patterns['has_prolonged_stress'] and effectiveness_patterns['best_for_stress']:
            actionable.append({
                'type': 'proven_solution',
                'priority': 'medium',
                'data': {
                    'activity_name': effectiveness_patterns['best_for_stress']['name'],
                    'activity_id': effectiveness_patterns['best_for_stress']['id'],
                    'times_done': effectiveness_patterns['best_for_stress']['times_done'],
                    'avg_rating': effectiveness_patterns['best_for_stress']['avg_rating'],
                    'context': 'stress'
                }
            })
        
        # Pattern 5: Low engagement (MEDIUM PRIORITY)
        if engagement_patterns['low_acceptance'] and engagement_patterns['acceptance_rate'] > 0:
            actionable.append({
                'type': 'low_engagement',
                'priority': 'medium',
                'data': {
                    'acceptance_rate': engagement_patterns['acceptance_rate']
                }
            })
        
        return actionable
    
    def _prioritize_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Sort patterns by priority"""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(patterns, key=lambda p: priority_order[p['priority']])
    
    def _build_user_context(self, patterns: Dict) -> Dict:
        """Build user context for LLM"""
        activity_patterns = patterns['activity_patterns']
        effectiveness_patterns = patterns['effectiveness_patterns']
        
        context = {
            'baseline_activities': activity_patterns['baseline_per_week'],
            'current_activities': activity_patterns['current_week_count']
        }
        
        if effectiveness_patterns['best_activity']:
            context['best_activity'] = effectiveness_patterns['best_activity']
        
        return context
    
    def _determine_action(self, pattern: Dict) -> Dict:
        """Determine recommended action for pattern"""
        
        action_map = {
            'stress_inactivity_cycle': {
                'type': 'suggest_activity',
                'label': 'Try a quick activity',
                'activity_type': 'low_effort'
            },
            'activity_streak': {
                'type': 'celebrate',
                'label': 'Keep it going!',
                'show_streak_badge': True
            },
            'low_activity': {
                'type': 'suggest_activity',
                'label': 'Start small',
                'activity_type': 'easy'
            },
            'proven_solution': {
                'type': 'suggest_specific_activity',
                'label': f"Try {pattern['data'].get('activity_name', 'this')} again",
                'activity_id': pattern['data'].get('activity_id')
            },
            'low_engagement': {
                'type': 'ask_feedback',
                'label': 'Help us improve',
                'show_feedback_form': True
            }
        }
        
        return action_map.get(pattern['type'], {'type': 'none'})
