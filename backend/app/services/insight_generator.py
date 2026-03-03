# app/services/insight_generator.py
"""
Deterministic Insight Generator
Converts behavior metrics → structured insight objects
NO LLM. Pure rule-based logic.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .pattern_detector import PatternDetector
from .behavior_scorer import get_behavior_scorer

logger = logging.getLogger(__name__)


class InsightObject:
    """Structured insight object - deterministic, not LLM-generated"""
    
    def __init__(
        self,
        insight_type: str,
        severity: str,
        priority: int,
        data: Dict,
        context: str
    ):
        self.insight_type = insight_type
        self.severity = severity  # 'low', 'moderate', 'high'
        self.priority = priority  # 1 (highest) to 5 (lowest)
        self.data = data
        self.context = context  # 'stress', 'activity', 'engagement', 'celebration'
    
    def to_dict(self) -> Dict:
        return {
            'insight_type': self.insight_type,
            'severity': self.severity,
            'priority': self.priority,
            'data': self.data,
            'context': self.context
        }


class InsightGenerator:
    """
    Deterministic insight generation from behavior patterns.
    
    Rules:
    1. Max 1 insight per response (avoid overload)
    2. Priority-based selection
    3. Rate limiting (don't repeat same insight within 24h)
    4. Context-aware (only relevant insights)
    """
    
    # Insight type definitions with thresholds
    INSIGHT_RULES = {
        'prolonged_stress_pattern': {
            'threshold': {'consecutive_stressed_days': 3},
            'severity_levels': {
                'moderate': 3,
                'high': 5
            },
            'priority': 1,  # Highest
            'context': 'stress'
        },
        'activity_decline': {
            'threshold': {'activity_drop_percentage': 50},
            'severity_levels': {
                'moderate': 50,
                'high': 75
            },
            'priority': 2,
            'context': 'activity'
        },
        'proven_solution_available': {
            'threshold': {'best_activity_exists': True, 'current_stressed': True},
            'severity_levels': {
                'moderate': 1
            },
            'priority': 1,  # High priority - we know what works
            'context': 'stress'
        },
        'low_engagement': {
            'threshold': {'acceptance_rate': 30, 'min_shown': 10},
            'severity_levels': {
                'moderate': 30,
                'high': 15
            },
            'priority': 3,
            'context': 'engagement'
        },
        'activity_streak': {
            'threshold': {'streak_days': 7},
            'severity_levels': {
                'low': 7,
                'moderate': 14
            },
            'priority': 4,  # Lower priority - celebration
            'context': 'celebration'
        },
        'stress_inactivity_cycle': {
            'threshold': {'consecutive_stressed_days': 3, 'activity_drop_percentage': 40},
            'severity_levels': {
                'high': 1  # Always high if detected
            },
            'priority': 1,  # Highest - dangerous pattern
            'context': 'stress'
        }
    }
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.behavior_scorer = get_behavior_scorer()
        self._insight_cache = {}  # user_id -> {insight_type: last_shown_timestamp}
    
    def generate_insights(
        self,
        user_id: int,
        current_mood: Optional[str] = None,
        current_context: Optional[str] = None
    ) -> List[InsightObject]:
        """
        Generate prioritized insights for user.
        
        Args:
            user_id: User ID
            current_mood: Current mood emoji (optional)
            current_context: Current context ('stress', 'tired', etc.)
            
        Returns:
            List of InsightObjects, sorted by priority
        """
        logger.info(f"Generating insights for user {user_id}")
        
        # Step 1: Detect all patterns (rule-based)
        patterns = self.pattern_detector.detect_all_patterns(user_id)
        
        # Step 2: Convert patterns to insight objects
        insights = []
        
        # Check each insight rule
        if self._check_prolonged_stress(patterns):
            insights.append(self._create_prolonged_stress_insight(patterns))
        
        if self._check_activity_decline(patterns):
            insights.append(self._create_activity_decline_insight(patterns))
        
        if self._check_proven_solution(patterns, current_mood):
            insights.append(self._create_proven_solution_insight(patterns))
        
        if self._check_low_engagement(patterns):
            insights.append(self._create_low_engagement_insight(patterns))
        
        if self._check_activity_streak(patterns):
            insights.append(self._create_activity_streak_insight(patterns))
        
        if self._check_stress_inactivity_cycle(patterns):
            insights.append(self._create_stress_inactivity_cycle_insight(patterns))
        
        # Check for improvements (positive insights)
        improvement_insight = self._create_improvement_insight(patterns)
        if improvement_insight:
            insights.append(improvement_insight)
        
        # Step 3: Filter by rate limiting
        insights = self._apply_rate_limiting(user_id, insights)
        
        # Step 4: Filter by context relevance
        if current_context:
            insights = self._filter_by_context(insights, current_context)
        
        # Step 5: Sort by priority
        insights.sort(key=lambda x: x.priority)
        
        logger.info(f"Generated {len(insights)} insights for user {user_id}")
        
        return insights
    
    def get_top_insight(
        self,
        user_id: int,
        current_mood: Optional[str] = None,
        current_context: Optional[str] = None
    ) -> Optional[InsightObject]:
        """Get single highest priority insight"""
        insights = self.generate_insights(user_id, current_mood, current_context)
        return insights[0] if insights else None
    
    # ===== INSIGHT CHECKERS (Deterministic Rules) =====
    
    def _check_prolonged_stress(self, patterns: Dict) -> bool:
        """Check if user has prolonged stress pattern"""
        mood_patterns = patterns['mood_patterns']
        threshold = self.INSIGHT_RULES['prolonged_stress_pattern']['threshold']
        return mood_patterns['consecutive_negative_days'] >= threshold['consecutive_stressed_days']
    
    def _check_activity_decline(self, patterns: Dict) -> bool:
        """Check if user has activity decline"""
        activity_patterns = patterns['activity_patterns']
        threshold = self.INSIGHT_RULES['activity_decline']['threshold']
        return activity_patterns['activity_drop_percentage'] >= threshold['activity_drop_percentage']
    
    def _check_proven_solution(self, patterns: Dict, current_mood: Optional[str]) -> bool:
        """Check if proven solution exists for current state"""
        effectiveness = patterns['effectiveness_patterns']
        is_stressed = current_mood in ['😟', '😰', '😢'] if current_mood else False
        return effectiveness['best_for_stress'] is not None and is_stressed
    
    def _check_low_engagement(self, patterns: Dict) -> bool:
        """Check if user has low engagement"""
        engagement = patterns['engagement_patterns']
        rule = self.INSIGHT_RULES['low_engagement']
        return (
            engagement['acceptance_rate'] < rule['threshold']['acceptance_rate'] and
            engagement.get('total_shown', 0) >= rule['threshold']['min_shown']
        )
    
    def _check_activity_streak(self, patterns: Dict) -> bool:
        """Check if user has activity streak"""
        activity_patterns = patterns['activity_patterns']
        threshold = self.INSIGHT_RULES['activity_streak']['threshold']
        return activity_patterns['streak'] >= threshold['streak_days']
    
    def _check_stress_inactivity_cycle(self, patterns: Dict) -> bool:
        """Check for dangerous stress + inactivity cycle"""
        mood_patterns = patterns['mood_patterns']
        activity_patterns = patterns['activity_patterns']
        rule = self.INSIGHT_RULES['stress_inactivity_cycle']['threshold']
        
        return (
            mood_patterns['consecutive_negative_days'] >= rule['consecutive_stressed_days'] and
            activity_patterns['activity_drop_percentage'] >= rule['activity_drop_percentage']
        )
    
    # ===== INSIGHT CREATORS (Structured Objects) =====
    
    def _create_prolonged_stress_insight(self, patterns: Dict) -> InsightObject:
        """Create prolonged stress insight object"""
        days = patterns['mood_patterns']['consecutive_negative_days']
        reason = patterns['mood_patterns']['recurring_reason']
        
        severity = 'high' if days >= 5 else 'moderate'
        
        return InsightObject(
            insight_type='prolonged_stress_pattern',
            severity=severity,
            priority=1,
            data={
                'consecutive_days': days,
                'recurring_reason': reason
            },
            context='stress'
        )
    
    def _create_activity_decline_insight(self, patterns: Dict) -> InsightObject:
        """Create activity decline insight object"""
        drop_pct = patterns['activity_patterns']['activity_drop_percentage']
        current = patterns['activity_patterns']['current_week_count']
        baseline = patterns['activity_patterns']['baseline_per_week']
        
        severity = 'high' if drop_pct >= 75 else 'moderate'
        
        return InsightObject(
            insight_type='activity_decline',
            severity=severity,
            priority=2,
            data={
                'drop_percentage': drop_pct,
                'current_week': current,
                'baseline': baseline
            },
            context='activity'
        )
    
    def _create_proven_solution_insight(self, patterns: Dict) -> InsightObject:
        """Create proven solution insight object"""
        best = patterns['effectiveness_patterns']['best_for_stress']
        
        return InsightObject(
            insight_type='proven_solution_available',
            severity='moderate',
            priority=1,
            data={
                'activity_name': best['name'],
                'activity_id': best['id'],
                'times_done': best['times_done'],
                'avg_rating': best['avg_rating']
            },
            context='stress'
        )
    
    def _create_low_engagement_insight(self, patterns: Dict) -> InsightObject:
        """Create low engagement insight object"""
        rate = patterns['engagement_patterns']['acceptance_rate']
        
        severity = 'high' if rate < 15 else 'moderate'
        
        return InsightObject(
            insight_type='low_engagement',
            severity=severity,
            priority=3,
            data={
                'acceptance_rate': rate
            },
            context='engagement'
        )
    
    def _create_activity_streak_insight(self, patterns: Dict) -> InsightObject:
        """Create activity streak insight object"""
        streak = patterns['activity_patterns']['streak']
        
        severity = 'moderate' if streak >= 14 else 'low'
        
        return InsightObject(
            insight_type='activity_streak',
            severity=severity,
            priority=4,
            data={
                'streak_days': streak
            },
            context='celebration'
        )
    
    def _create_improvement_insight(self, patterns: Dict) -> InsightObject:
        """Create improvement trend insight"""
        activity_patterns = patterns['activity_patterns']
        health_patterns = patterns.get('health_patterns', {})
        
        improvements = []
        
        # Check activity improvement
        current = activity_patterns['current_week_count']
        baseline = activity_patterns['baseline_per_week']
        if baseline > 0 and current > baseline * 1.2:  # 20% improvement
            improvement_pct = ((current - baseline) / baseline) * 100
            improvements.append({
                'type': 'activity',
                'percentage': improvement_pct,
                'current': current,
                'baseline': baseline
            })
        
        # Check sleep improvement
        sleep_current = health_patterns.get('sleep_current_avg', 0)
        sleep_baseline = health_patterns.get('sleep_baseline_avg', 0)
        if sleep_baseline > 0 and sleep_current > sleep_baseline * 1.1:  # 10% improvement
            improvement_pct = ((sleep_current - sleep_baseline) / sleep_baseline) * 100
            improvements.append({
                'type': 'sleep',
                'percentage': improvement_pct,
                'current': sleep_current,
                'baseline': sleep_baseline
            })
        
        # Check water improvement
        water_current = health_patterns.get('water_current_avg', 0)
        water_baseline = health_patterns.get('water_baseline_avg', 0)
        if water_baseline > 0 and water_current > water_baseline * 1.2:  # 20% improvement
            improvement_pct = ((water_current - water_baseline) / water_baseline) * 100
            improvements.append({
                'type': 'water',
                'percentage': improvement_pct,
                'current': water_current,
                'baseline': water_baseline
            })
        
        if improvements:
            return InsightObject(
                insight_type='improvement_trend',
                severity='low',
                priority=4,
                data={
                    'improvements': improvements
                },
                context='celebration'
            )
        
        return None
    
    def _create_stress_inactivity_cycle_insight(self, patterns: Dict) -> InsightObject:
        """Create stress-inactivity cycle insight object"""
        days = patterns['mood_patterns']['consecutive_negative_days']
        drop_pct = patterns['activity_patterns']['activity_drop_percentage']
        
        return InsightObject(
            insight_type='stress_inactivity_cycle',
            severity='high',
            priority=1,
            data={
                'stressed_days': days,
                'activity_drop': drop_pct
            },
            context='stress'
        )
    
    # ===== FILTERING & RATE LIMITING =====
    
    def _apply_rate_limiting(self, user_id: int, insights: List[InsightObject]) -> List[InsightObject]:
        """
        Filter out insights shown recently (within 24h).
        Prevents repetitive insights.
        """
        if user_id not in self._insight_cache:
            self._insight_cache[user_id] = {}
        
        cache = self._insight_cache[user_id]
        now = datetime.now()
        filtered = []
        
        for insight in insights:
            last_shown = cache.get(insight.insight_type)
            
            if last_shown:
                time_since = now - last_shown
                if time_since < timedelta(hours=24):
                    logger.debug(f"Rate limiting: {insight.insight_type} shown {time_since.seconds/3600:.1f}h ago")
                    continue
            
            filtered.append(insight)
        
        return filtered
    
    def _filter_by_context(self, insights: List[InsightObject], current_context: str) -> List[InsightObject]:
        """Filter insights by relevance to current context"""
        # Map contexts
        context_map = {
            'stressed': 'stress',
            'tired': 'activity',
            'bored': 'engagement'
        }
        
        target_context = context_map.get(current_context, current_context)
        
        # Prioritize matching context, but don't exclude others
        matching = [i for i in insights if i.context == target_context]
        others = [i for i in insights if i.context != target_context]
        
        return matching + others
    
    def mark_insight_shown(self, user_id: int, insight_type: str):
        """Mark insight as shown (for rate limiting)"""
        if user_id not in self._insight_cache:
            self._insight_cache[user_id] = {}
        
        self._insight_cache[user_id][insight_type] = datetime.now()
        logger.info(f"Marked insight '{insight_type}' as shown for user {user_id}")


# Global instance
_insight_generator = None

def get_insight_generator() -> InsightGenerator:
    """Get or create global InsightGenerator instance"""
    global _insight_generator
    if _insight_generator is None:
        _insight_generator = InsightGenerator()
    return _insight_generator
