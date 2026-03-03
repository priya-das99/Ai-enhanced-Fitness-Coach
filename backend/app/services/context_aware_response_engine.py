"""
Context-Aware Response Engine
Orchestrates all context signals to make intelligent response decisions
"""

import logging
from typing import Dict, Optional, List
from .intent_analyzer import get_intent_analyzer
from .session_tracker import get_session_tracker
from .user_data_analyzer import get_user_data_analyzer
from .insight_generator import get_insight_generator
from .insight_timing_controller import get_timing_controller, InsightTrigger

logger = logging.getLogger(__name__)


class ContextAwareResponseEngine:
    """
    Main engine that combines all context signals to decide:
    - What to say
    - Whether to show buttons
    - Whether to show insights
    - What tone to use
    """
    
    def __init__(self):
        self.intent_analyzer = get_intent_analyzer()
        self.session_tracker = get_session_tracker()
        self.user_data_analyzer = get_user_data_analyzer()
        self.insight_generator = get_insight_generator()
        self.timing_controller = get_timing_controller()
    
    def analyze_and_decide(
        self,
        user_id: int,
        message: str,
        mood_emoji: str = None,
        workflow_context: Dict = None
    ) -> Dict:
        """
        Analyze all context and make response decisions
        
        Args:
            user_id: User ID
            message: User's message
            mood_emoji: Detected mood emoji (if any)
            
        Returns:
            {
                'show_buttons': bool,
                'show_insight': bool,
                'tone': str,
                'response_strategy': str,
                'context_summary': dict,
                'recommendations': list,
                'triggered_insights': list  # NEW: Structured insight objects
            }
        """
        logger.info(f"Analyzing context for user {user_id}: '{message[:50]}...'")
        
        # Step 1: Detect insight trigger
        workflow_context = workflow_context or {}
        trigger = self.timing_controller.detect_trigger(
            workflow_name=workflow_context.get('workflow_name', ''),
            workflow_step=workflow_context.get('workflow_step', ''),
            message=message,
            just_completed_activity=workflow_context.get('just_completed_activity', False)
        )
        
        # Step 2: Generate deterministic insights
        current_context = self._extract_context_from_message(message)
        top_insight = self.insight_generator.get_top_insight(
            user_id=user_id,
            current_mood=mood_emoji,
            current_context=current_context
        )
        
        # Step 3: Check if insight should be shown (timing discipline)
        show_insight_allowed = False
        if top_insight:
            # Build conversation context for timing check
            conversation_context = {
                'intent': intent_analysis.get('intent_type') if 'intent_analysis' in locals() else 'unknown',
                'intensity': intensity_analysis.get('intensity') if 'intensity_analysis' in locals() else 'medium',
                'state': workflow_context.get('workflow_step', ''),
                'mood_emoji': mood_emoji,
                'reason': workflow_context.get('reason'),
                'activity_type': workflow_context.get('activity_type'),
                'acceptance_rate': workflow_context.get('acceptance_rate', 100)
            }
            
            show_insight_allowed = self.timing_controller.should_show_insight(
                user_id=user_id,
                trigger=trigger,
                conversation_context=conversation_context,
                insight_priority=top_insight.priority
            )
            
            if show_insight_allowed:
                logger.info(f"✅ Insight timing approved: {top_insight.insight_type}")
            else:
                logger.info(f"❌ Insight timing blocked: {top_insight.insight_type}")
                top_insight = None  # Don't use insight if timing not right
        
        # Step 4: Analyze user data patterns (legacy - for backward compatibility)
        user_insights = self.user_data_analyzer.analyze_for_mood(user_id, message, mood_emoji)
        
        # Step 5: Detect intent and intensity
        intent_analysis = self.intent_analyzer.analyze_user_intent(
            message,
            context={
                'recurring_pattern': user_insights.get('has_pattern', False),
                'recent_activity': False
            }
        )
        
        intensity_analysis = self.intent_analyzer.detect_intensity(
            message,
            history={'frequency': user_insights.get('tired_frequency', 0)}
        )
        
        # Step 6: Check session fatigue
        session_fatigue = self.session_tracker.get_session_fatigue(user_id)
        time_context = self.session_tracker.check_time_context(user_id)
        
        # Step 7: Make decisions based on all signals
        decision = self._make_decision(
            intent_analysis=intent_analysis,
            intensity_analysis=intensity_analysis,
            user_insights=user_insights,
            session_fatigue=session_fatigue,
            time_context=time_context,
            top_insight=top_insight  # NEW: Pass structured insight
        )
        
        # Step 8: Add structured insights to decision (only if timing approved)
        decision['triggered_insights'] = [top_insight.to_dict()] if top_insight else []
        
        # Step 9: Mark insight as shown if included
        if top_insight and decision['show_insight']:
            self.insight_generator.mark_insight_shown(user_id, top_insight.insight_type)
            self.timing_controller.mark_insight_shown(user_id)
        
        # Step 10: Track mood log for frequency limiting
        if workflow_context.get('workflow_name') == 'mood_logging':
            self.timing_controller.mark_mood_logged(user_id)
        
        # Step 11: Track this interaction
        self.session_tracker.track_interaction(user_id, 'message_sent')
        
        logger.info(f"Decision: buttons={decision['show_buttons']}, "
                   f"insight={decision['show_insight']}, "
                   f"strategy={decision['response_strategy']}, "
                   f"insights={len(decision['triggered_insights'])}")
        
        return decision
    
    def _make_decision(self, intent_analysis: Dict, intensity_analysis: Dict,
                      user_insights: Dict, session_fatigue: Dict, time_context: Dict,
                      top_insight: Optional[object] = None) -> Dict:
        """
        Core decision logic combining all signals
        
        Decision Priority:
        1. Session fatigue (override everything if high)
        2. Intent type (venting vs action-seeking)
        3. Intensity (severe needs immediate support)
        4. User patterns (recurring issues)
        5. Time context (energy levels)
        """
        
        # Initialize decision
        decision = {
            'show_buttons': False,
            'show_insight': False,
            'tone': 'neutral',
            'response_strategy': 'acknowledge',
            'context_summary': {
                'intent': intent_analysis['intent_type'],
                'intensity': intensity_analysis['intensity'],
                'fatigue': session_fatigue['fatigue_level'],
                'time': time_context['time_of_day'],
                'has_pattern': user_insights.get('has_pattern', False),
                'has_insight': top_insight is not None  # NEW
            },
            'recommendations': []
        }
        
        # NEW: If high-priority insight exists, adjust decision
        if top_insight and top_insight.priority <= 2:
            decision['show_insight'] = True
            decision['recommendations'].append(f'High-priority insight: {top_insight.insight_type}')
        
        # Rule 1: High session fatigue - stay silent or minimal
        if session_fatigue['should_stay_silent']:
            decision['response_strategy'] = 'minimal'
            decision['tone'] = 'supportive'
            decision['recommendations'].append('Session fatigue high - minimal response')
            return decision
        
        # Rule 2: Venting - empathize, don't push actions
        if intent_analysis['intent_type'] == 'venting':
            decision['show_insight'] = user_insights.get('has_pattern', False)
            decision['show_buttons'] = False  # No buttons when venting
            decision['tone'] = 'empathetic'
            decision['response_strategy'] = 'empathize_and_validate'
            decision['recommendations'].append('User is venting - acknowledge without pushing')
            return decision
        
        # Rule 3: Severe intensity - immediate support
        if intensity_analysis['intensity'] == 'severe':
            decision['show_insight'] = True
            decision['show_buttons'] = True  # Offer help
            decision['tone'] = 'caring'
            decision['response_strategy'] = 'immediate_support'
            decision['recommendations'].append('Severe intensity - offer immediate support')
            return decision
        
        # Rule 4: Action-seeking - provide options
        if intent_analysis['intent_type'] == 'action_seeking':
            decision['show_buttons'] = not session_fatigue['should_reduce_prompts']
            decision['show_insight'] = user_insights.get('has_pattern', False)
            decision['tone'] = 'helpful'
            decision['response_strategy'] = 'provide_options'
            decision['recommendations'].append('User seeking action - provide options')
            return decision
        
        # Rule 5: Logging - encourage and offer more
        if intent_analysis['intent_type'] == 'logging':
            decision['show_buttons'] = not session_fatigue['should_reduce_prompts']
            decision['show_insight'] = False  # Don't overwhelm during logging
            decision['tone'] = 'encouraging'
            decision['response_strategy'] = 'encourage_and_offer'
            decision['recommendations'].append('User logging - encourage continuation')
            return decision
        
        # Rule 6: Recurring pattern - address pattern
        if intensity_analysis['intensity'] == 'recurring':
            decision['show_insight'] = True
            decision['show_buttons'] = True
            decision['tone'] = 'concerned'
            decision['response_strategy'] = 'address_pattern'
            decision['recommendations'].append('Recurring pattern detected - address it')
            return decision
        
        # Rule 7: Low energy time - simplify
        if time_context['energy_level'] == 'low':
            decision['show_buttons'] = intent_analysis['show_buttons']
            decision['show_insight'] = False  # Don't add cognitive load
            decision['tone'] = 'gentle'
            decision['response_strategy'] = 'simplify'
            decision['recommendations'].append('Low energy time - keep it simple')
            return decision
        
        # Default: Balanced response
        decision['show_buttons'] = intent_analysis['show_buttons']
        decision['show_insight'] = user_insights.get('has_pattern', False)
        decision['tone'] = intent_analysis['tone']
        decision['response_strategy'] = 'balanced'
        decision['recommendations'].append('Default balanced response')
        
        return decision
    
    def track_button_interaction(self, user_id: int, button_clicked: bool):
        """Track whether user clicked a button or ignored it"""
        if button_clicked:
            self.session_tracker.track_interaction(user_id, 'button_clicked')
        else:
            self.session_tracker.track_interaction(user_id, 'prompt_ignored')
    
    def _extract_context_from_message(self, message: str) -> Optional[str]:
        """Extract context from user message for insight filtering"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['stress', 'anxious', 'overwhelm', 'pressure']):
            return 'stressed'
        elif any(word in message_lower for word in ['tired', 'exhaust', 'drain', 'fatigue']):
            return 'tired'
        elif any(word in message_lower for word in ['bored', 'boring', 'nothing to do']):
            return 'bored'
        
        return None


# Global instance
_response_engine = None

def get_response_engine() -> ContextAwareResponseEngine:
    """Get or create global ContextAwareResponseEngine instance"""
    global _response_engine
    if _response_engine is None:
        _response_engine = ContextAwareResponseEngine()
    return _response_engine
