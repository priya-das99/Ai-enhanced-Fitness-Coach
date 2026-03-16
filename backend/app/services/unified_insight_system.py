"""
Unified Insight System
Merges Phase 2 and Prebuilt systems for the ultimate insight experience

Features:
- Pattern Detection (Phase 2) - Works with SQLite3
- LLM Messages (Prebuilt) - Natural, empathetic
- Context Analysis (Prebuilt) - Explains WHY
- Timing Control (Prebuilt) - Smart delivery
- Weekly Insights (Phase 2) - Comprehensive summaries
- Predictive Suggestions (Phase 2) - Proactive
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UnifiedInsightSystem:
    """
    Unified system combining best of Phase 2 and Prebuilt systems
    
    Architecture:
    - Pattern Detection: Phase 2 (SQLite3 compatible)
    - LLM Generation: Prebuilt (natural messages)
    - Context Analysis: Prebuilt (root cause analysis)
    - Timing Control: Prebuilt (smart delivery)
    - Weekly Insights: Phase 2 (comprehensive)
    - Predictive Suggestions: Phase 2 (proactive)
    """
    
    def __init__(self):
        # Phase 2 Components (SQLite3 compatible)
        from app.services.pattern_detector_sqlite import PatternDetector
        # Note: insight_generator, predictive_suggestion_service, and conversation_memory_service
        # will be imported when needed with database context
        
        # Prebuilt Components (adapted for SQLite3)
        from app.services.llm_insight_generator import LLMInsightGenerator
        from app.services.user_data_analyzer import UserDataAnalyzer
        from app.services.insight_timing_controller import InsightTimingController
        
        # Initialize components
        self.pattern_detector = PatternDetector()
        self.llm_generator = LLMInsightGenerator()
        self.context_analyzer = UserDataAnalyzer()
        self.timing_controller = InsightTimingController()
        
        logger.info("✅ Unified Insight System initialized")
    
    # ===== GREETING INSIGHTS (Real-time, LLM-powered) =====
    
    def get_greeting_insight(self, user_id: int) -> Optional[Dict]:
        """
        Get personalized greeting insight with LLM-generated message
        
        Combines:
        - Pattern detection (Phase 2)
        - Context analysis (Prebuilt)
        - Timing control (Prebuilt)
        - LLM generation (Prebuilt)
        
        Returns:
            Dict with message, pattern, and actions, or None
        """
        try:
            logger.info(f"Generating greeting insight for user {user_id}")
            
            # Step 1: Detect patterns (Phase 2)
            from app.core.database import get_db
            
            with get_db() as db:
                patterns = self.pattern_detector.detect_all_patterns(user_id, db)
            
            if not patterns or not any(patterns.values()):
                logger.info(f"No patterns detected for user {user_id}")
                return None
            
            # Step 2: Get actionable insights
            actionable = self._get_actionable_patterns(patterns)
            
            if not actionable:
                logger.info(f"No actionable patterns for user {user_id}")
                return None
            
            # Step 3: Prioritize patterns
            top_pattern = self._prioritize_patterns(actionable)[0]
            
            # Step 4: Check timing (Prebuilt)
            from app.services.insight_timing_controller import InsightTrigger
            
            should_show = self.timing_controller.should_show_insight(
                user_id=user_id,
                trigger=InsightTrigger.USER_ASKS_PROGRESS,
                conversation_context={},
                insight_priority=self._get_priority_level(top_pattern)
            )
            
            if not should_show:
                logger.info(f"Timing check failed for user {user_id}")
                return None
            
            # Step 5: Analyze context (Prebuilt)
            context = self._build_user_context(user_id, patterns)
            
            # Step 6: Generate natural message with LLM (Prebuilt)
            message = self.llm_generator.generate_insight_message(
                pattern_type=top_pattern['type'],
                pattern_data=top_pattern['data'],
                user_context=context,
                priority=top_pattern['priority']
            )
            
            # Step 7: Mark insight shown
            self.timing_controller.mark_insight_shown(user_id)
            
            logger.info(f"✅ Generated greeting insight for user {user_id}: {top_pattern['type']}")
            
            return {
                'message': message,
                'pattern': top_pattern,
                'action': self._determine_action(top_pattern),
                'type': 'greeting_insight'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate greeting insight for user {user_id}: {e}", exc_info=True)
            return None
    
    # ===== WEEKLY INSIGHTS (Comprehensive summaries) =====
    
    def generate_weekly_summary(self, user_id: int) -> Optional[Dict]:
        """
        Generate comprehensive weekly summary (Phase 2)
        
        Returns:
            Dict with weekly insights and recommendations
        """
        try:
            logger.info(f"Generating weekly summary for user {user_id}")
            
            # Import SQLite3-compatible version
            from app.services.insight_generator_sqlite import InsightGeneratorSQLite
            from app.core.database import get_db
            
            with get_db() as db:
                generator = InsightGeneratorSQLite()
                insight = generator.generate_weekly_insight(user_id, db)
            
            if not insight:
                logger.info(f"No weekly insight for user {user_id}")
                return None
            
            # Format as message
            message = generator.format_insight_message(insight)
            
            logger.info(f"✅ Generated weekly summary for user {user_id}")
            
            return {
                'message': message,
                'insight': insight,
                'type': 'weekly_summary'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate weekly summary for user {user_id}: {e}", exc_info=True)
            return None
    
    # ===== PREDICTIVE SUGGESTIONS (Proactive) =====
    
    def get_predictive_suggestion(self, user_id: int) -> Optional[Dict]:
        """
        Get proactive suggestion based on time/day patterns (Phase 2)
        
        Returns:
            Dict with suggestion message and activities
        """
        try:
            logger.info(f"Checking predictive suggestions for user {user_id}")
            
            # Import SQLite3-compatible version
            from app.services.predictive_suggestion_service_sqlite import PredictiveSuggestionServiceSQLite
            from app.core.database import get_db
            
            with get_db() as db:
                service = PredictiveSuggestionServiceSQLite()
                suggestion = service.should_suggest_proactively(user_id, db)
            
            if not suggestion:
                logger.info(f"No predictive suggestion for user {user_id}")
                return None
            
            logger.info(f"✅ Generated predictive suggestion for user {user_id}: {suggestion['trigger_type']}")
            
            return {
                'message': suggestion['message'],
                'suggested_activities': suggestion['suggested_activities'],
                'trigger_type': suggestion['trigger_type'],
                'type': 'predictive_suggestion'
            }
            
        except Exception as e:
            logger.error(f"Failed to get predictive suggestion for user {user_id}: {e}", exc_info=True)
            return None
    
    # ===== CONVERSATION MEMORY (Follow-ups) =====
    
    def check_follow_up(self, user_id: int) -> Optional[Dict]:
        """
        Check if there's a follow-up message to send (Phase 2)
        
        Returns:
            Dict with follow-up message
        """
        try:
            logger.info(f"Checking follow-ups for user {user_id}")
            
            # Import SQLite3-compatible version
            from app.services.conversation_memory_service_sqlite import ConversationMemoryServiceSQLite
            from app.core.database import get_db
            
            with get_db() as db:
                service = ConversationMemoryServiceSQLite()
                followup = service.should_follow_up(user_id, db)
            
            if not followup:
                logger.info(f"No follow-up for user {user_id}")
                return None
            
            logger.info(f"✅ Generated follow-up for user {user_id}: {followup['type']}")
            
            return {
                'message': followup['message'],
                'followup_type': followup['type'],
                'type': 'follow_up'
            }
            
        except Exception as e:
            logger.error(f"Failed to check follow-up for user {user_id}: {e}", exc_info=True)
            return None
    
    # ===== CONTEXT ANALYSIS (Root cause) =====
    
    def analyze_mood_context(self, user_id: int, mood_text: str, mood_emoji: str = None) -> Optional[Dict]:
        """
        Analyze context for user's mood (Prebuilt)
        
        Returns:
            Dict with context analysis and recommendations
        """
        try:
            logger.info(f"Analyzing mood context for user {user_id}: {mood_text}")
            
            insights = self.context_analyzer.analyze_for_mood(user_id, mood_text, mood_emoji)
            
            if not insights or not insights.get('has_pattern'):
                logger.info(f"No context patterns for user {user_id}")
                return None
            
            logger.info(f"✅ Analyzed mood context for user {user_id}: {insights['pattern_type']}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze mood context for user {user_id}: {e}", exc_info=True)
            return None
    
    # ===== HELPER METHODS =====
    
    def _get_actionable_patterns(self, patterns: Dict) -> List[Dict]:
        """Convert detected patterns to actionable insights"""
        actionable = []
        
        # Day patterns
        for pattern in patterns.get('day_patterns', []):
            if pattern.get('confidence', 0) >= 0.6:
                actionable.append({
                    'type': 'day_pattern',
                    'priority': 'medium',
                    'data': pattern,
                    'confidence': pattern['confidence']
                })
        
        # Time patterns
        for pattern in patterns.get('time_patterns', []):
            if pattern.get('confidence', 0) >= 0.5:
                actionable.append({
                    'type': 'time_pattern',
                    'priority': 'medium',
                    'data': pattern,
                    'confidence': pattern['confidence']
                })
        
        # Activity patterns
        for pattern in patterns.get('activity_patterns', []):
            if pattern.get('confidence', 0) >= 0.6:
                actionable.append({
                    'type': 'activity_pattern',
                    'priority': 'low',
                    'data': pattern,
                    'confidence': pattern['confidence']
                })
        
        # Mood improvement patterns
        for pattern in patterns.get('mood_improvement_patterns', []):
            if pattern.get('success_rate', 0) >= 0.75:
                actionable.append({
                    'type': 'mood_improvement',
                    'priority': 'low',
                    'data': pattern,
                    'confidence': pattern['success_rate']
                })
        
        # Absence pattern
        if patterns.get('absence_pattern'):
            absence = patterns['absence_pattern']
            if absence.get('days_absent', 0) >= 3:
                actionable.append({
                    'type': 'absence',
                    'priority': 'high',
                    'data': absence,
                    'confidence': 1.0
                })
        
        return actionable
    
    def _prioritize_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Sort patterns by priority and confidence"""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        
        return sorted(
            patterns,
            key=lambda p: (priority_order[p['priority']], -p['confidence'])
        )
    
    def _get_priority_level(self, pattern: Dict) -> int:
        """Convert priority string to numeric level"""
        priority_map = {'high': 1, 'medium': 2, 'low': 3}
        return priority_map.get(pattern['priority'], 2)
    
    def _build_user_context(self, user_id: int, patterns: Dict) -> Dict:
        """Build user context for LLM"""
        context = {}
        
        # Get activity baseline
        activity_patterns = patterns.get('activity_patterns', [])
        if activity_patterns:
            context['baseline_activities'] = len(activity_patterns)
        
        # Get best activity
        mood_improvements = patterns.get('mood_improvement_patterns', [])
        if mood_improvements:
            best = mood_improvements[0]
            context['best_activity'] = {
                'name': best.get('activity', 'unknown'),
                'avg_rating': best.get('success_rate', 0) * 5  # Convert to 1-5 scale
            }
        
        return context
    
    def _determine_action(self, pattern: Dict) -> Dict:
        """Determine recommended action for pattern"""
        pattern_type = pattern['type']
        
        action_map = {
            'day_pattern': {
                'type': 'suggest_routine',
                'label': 'Create routine',
                'description': f"Create a {pattern['data'].get('day', 'daily')} routine"
            },
            'time_pattern': {
                'type': 'schedule_activity',
                'label': 'Schedule activity',
                'description': f"Schedule activity before {pattern['data'].get('hour', 0)}:00"
            },
            'activity_pattern': {
                'type': 'prioritize_activity',
                'label': 'Make it your go-to',
                'description': f"Prioritize {pattern['data'].get('activity', 'this')} for {pattern['data'].get('reason', 'this situation')}"
            },
            'mood_improvement': {
                'type': 'suggest_activity',
                'label': 'Try this again',
                'description': f"Try {pattern['data'].get('activity', 'this')} - it works {int(pattern['data'].get('success_rate', 0)*100)}% of the time"
            },
            'absence': {
                'type': 'welcome_back',
                'label': 'Welcome back',
                'description': 'Good to see you again!'
            }
        }
        
        return action_map.get(pattern_type, {'type': 'none'})


# Global instance
_unified_system = None

def get_unified_insight_system() -> UnifiedInsightSystem:
    """Get or create global UnifiedInsightSystem instance"""
    global _unified_system
    if _unified_system is None:
        _unified_system = UnifiedInsightSystem()
    return _unified_system
