# mood_workflow.py
# Mood logging workflow - state-driven implementation
# Phase 2: Integrated with EventPublisher for analytics

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .mood_handler import (
    validate_mood_emoji, save_mood_log, has_logged_mood_today,
    is_positive_mood, get_mood_value
)
from .action_suggestions import get_mood_reasons
from .llm_service import get_llm_service
from .smart_suggestions import get_smart_suggestions
from .content_suggestions import get_content_suggestions
from .context_builder_simple import build_context
from .intelligent_suggestions import get_enhanced_suggestion_engine
from .domain.llm.response_phraser import (
    phrase_activity_suggestion,
    phrase_contextual_suggestion,
    phrase_empathetic_response
)
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class MoodWorkflow(BaseWorkflow):
    """
    Mood logging workflow - Phase 1 Refactored
    
    Flow:
    1. Ask mood (if not logged today)
    2. If positive → log and complete
    3. If negative → ask reason
    4. After reason → suggest ONE activity
    5. After suggestion → complete
    
    Phase 1: No longer uses can_handle() - intent detection via LLM
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="mood_logging",
            handled_intents=['mood_logging', 'mood_check', 'feeling', 'emotion', 'log_mood']
        )
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start mood logging workflow"""
        logger.info(f"Starting mood workflow for user {user_id}")
        
        # Check current workflow state
        current_step = state.get_workflow_data('step', '')
        logger.info(f"Current workflow step: {current_step}")
        
        # If we're in asking_mood state and user sends an emoji, handle it
        if current_step == 'asking_mood' and validate_mood_emoji(message.strip()):
            mood_emoji = message.strip()
            logger.info(f"User selected emoji from selector: {mood_emoji}")
            
            # Update workflow state
            state.update_workflow_data({'mood_emoji': mood_emoji, 'step': 'mood_selected'})
            
            # Check if positive or negative
            if is_positive_mood(mood_emoji):
                # Positive mood - log and complete immediately
                save_mood_log(user_id, mood_emoji, reason=None)
                
                # Emit event
                try:
                    from app.services.event_publisher import get_event_publisher
                    publisher = get_event_publisher()
                    publisher.publish_mood_logged(
                        user_id=str(user_id),
                        mood_emoji=mood_emoji,
                        reason=None,
                        mood_value=get_mood_value(mood_emoji)
                    )
                    logger.info(f"📊 Published mood_logged event for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish mood_logged event: {e}")
                
                state.complete_workflow()
                return self._create_positive_mood_response(mood_emoji, user_id=user_id)
            else:
                # Negative mood - ask for reason
                reasons = get_mood_reasons()
                return self._ask_clarification(
                    message="I am here for you. Would you like to share what's been causing it?",
                    ui_elements=['reason_selector'],
                    reasons=reasons
                )
        
        # Check if this is a button click (log_mood) - normalize and check
        message_normalized = message.lower().strip().replace(' ', '_')
        is_button_click = message_normalized in ['log_mood', 'log_my_mood', 'logmood','log again'] or \
                         message.lower().strip() in ['log mood', 'log my mood', 'track mood']
        
        logger.info(f"Message: '{message}', Normalized: '{message_normalized}', Is button click: {is_button_click}")
        
        # Check if user is requesting to log MOOD again (override)
        # Be specific to avoid catching "I want to log water" etc.
        message_lower = message.lower().strip()
        is_log_again_request = any(phrase in message_lower for phrase in [
            'log again', 'log my mood again', 'log mood again',
            'log it again', 'track again', 'log another mood',
            'want to log again', 'want to log my mood'
        ]) and not any(activity in message_lower for activity in [
            'water', 'exercise', 'sleep', 'weight', 'meal', 'workout'
        ])
        
        # If button click, check if mood already logged today (unless override requested)
        if is_button_click and has_logged_mood_today(user_id) and not is_log_again_request:
            logger.info(f"User {user_id} already logged mood today")
            # Start workflow first, then update data
            state.start_workflow(self.workflow_name, {'step': 'asking_mood'})
            return WorkflowResponse(
                message="You already logged your mood today! Want to log it again anyway?",
                completed=False,  # Keep workflow active to handle emoji selection
                next_state=ConversationState.WORKFLOW_ACTIVE,
                ui_elements=['emoji_selector'],
                extra_data={}
            )
        
        # If user explicitly requests to log again, allow it
        if is_log_again_request:
            logger.info(f"User {user_id} requested to log mood again - allowing override")
            # Show mood selector to let them log again
            # Start workflow first, then update data
            state.start_workflow(self.workflow_name, {'step': 'asking_mood'})
            return WorkflowResponse(
                message="Sure! How are you feeling now? 😊",
                completed=False,  # Keep workflow active to handle emoji selection
                next_state=ConversationState.WORKFLOW_ACTIVE,
                ui_elements=['emoji_selector'],
                extra_data={}
            )
        
        # PRIORITY: Check for engagement states (bored, tired, restless, lonely)
        # Skip this for button clicks
        detected_state = None
        if not is_button_click:
            # Use old engine for detection only (it has detect_state method)
            from .intelligent_suggestions import IntelligentSuggestionEngine
            old_engine = IntelligentSuggestionEngine()
            detected_state = old_engine.detect_state(message)
        
            if detected_state:
                logger.info(f"🎯 Detected engagement state: {detected_state}")
                
                # Get user context for personalization
                context = build_context(user_id)
                
                # ===== ENHANCED SUGGESTION SYSTEM =====
                # Use enhanced suggestion engine (DB-driven with smart ranking)
                suggestion_engine = get_enhanced_suggestion_engine()
                suggestions_data = suggestion_engine.get_suggestions(
                    state=detected_state,
                    user_id=user_id, 
                    context=context
                )
                
                # Validate we have activities
                if not suggestions_data.get('activities'):
                    logger.warning("⚠️  No activities from suggestion engine, using generic prompt")
                    return self._ask_clarification(
                        message="I hear you. What would help you feel better?",
                        ui_elements=['text_input']
                    )
                
                # Extract activity titles for matched response generation
                activity_titles = [act.get('title') or act.get('name') for act in suggestions_data['activities']]
                
                # Generate response that mentions exact activities
                try:
                    matched_message = phrase_activity_suggestion(
                        state=detected_state,
                        activity_titles=activity_titles
                    )
                    logger.info(f"✅ Generated matched response: {matched_message[:50]}...")
                except Exception as e:
                    logger.error(f"❌ Response phrasing failed: {e}")
                    matched_message = f"I hear you. Here are some activities that might help:"
                
                # Map state to appropriate mood emoji
                state_to_emoji = {
                    'bored': '😑',
                    'tired': '😴',
                    'restless': '😤',
                    'lonely': '😔'
                }
                mood_emoji = state_to_emoji.get(detected_state, '😐')
                
                # Save mood with detected state as reason
                save_mood_log(user_id, mood_emoji, reason=detected_state)
                
                # Emit event
                try:
                    from app.services.event_publisher import get_event_publisher
                    publisher = get_event_publisher()
                    publisher.publish_mood_logged(
                        user_id=str(user_id),
                        mood_emoji=mood_emoji,
                        reason=detected_state,
                        mood_value=get_mood_value(mood_emoji)
                    )
                    logger.info(f"📊 Published mood_logged event for engagement state: {detected_state}")
                except Exception as e:
                    logger.warning(f"Failed to publish mood_logged event: {e}")
                
                # Start workflow with suggestions
                state.start_workflow(self.workflow_name, {
                    'mood_emoji': mood_emoji,
                    'state': detected_state,
                    'step': 'suggesting_action',
                    'suggestions': suggestions_data['activities'][:3],  # Store suggestions!
                    'reason': detected_state
                })
                
                # Return with matched message and activity buttons
                return self._ask_confirmation(
                    message=matched_message,  # Now matches the activity buttons!
                    ui_elements=['action_buttons_multiple'],
                    actions=suggestions_data['activities'][:3],  # Top 3 activities
                    events=[{'type': 'mood_logged', 'mood': mood_emoji, 'reason': detected_state}]
                )
        
        # Check if intent extractor already provided entities
        intent_entities = state.get_workflow_data('intent_entities', {})
        mood_from_intent = intent_entities.get('mood_emoji', '')
        
        logger.info(f"Intent entities: {intent_entities}")
        logger.info(f"Mood from intent: {mood_from_intent}")
        
        # Check if message is a direct emoji selection
        if validate_mood_emoji(message.strip()):
            mood_emoji = message.strip()
            logger.info(f"Direct emoji selection: {mood_emoji}")
            
            # Start workflow with selected emoji
            state.start_workflow(self.workflow_name, {
                'mood_emoji': mood_emoji,
                'step': 'mood_selected'
            })
            
            # Check if positive or negative
            if is_positive_mood(mood_emoji):
                # Positive mood - log and complete immediately
                mood_log = save_mood_log(user_id, mood_emoji, reason=None)
                
                # Phase 2: Emit event after successful save
                try:
                    from app.services.event_publisher import get_event_publisher
                    publisher = get_event_publisher()
                    publisher.publish_mood_logged(
                        user_id=str(user_id),
                        mood_emoji=mood_emoji,
                        reason=None,
                        mood_value=get_mood_value(mood_emoji)
                    )
                    logger.info(f"📊 Published mood_logged event for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish mood_logged event: {e}")
                
                state.complete_workflow()
                return self._create_positive_mood_response(mood_emoji, user_id=user_id)
            else:
                # Negative mood - ask for reason
                reasons = get_mood_reasons()
                return self._ask_clarification(
                    message="What's contributing to this feeling?",
                    ui_elements=['reason_selector'],
                    reasons=reasons
                )
        
        # Try to extract mood from message using LLM or keywords
        from .mood_extractor import extract_mood_from_message
        from .mood_categories import should_ask_reason, get_suggested_activity_types
        
        # First, check if intent extractor already provided mood
        mood_emoji = None
        confidence = 'low'
        
        if mood_from_intent and validate_mood_emoji(mood_from_intent):
            mood_emoji = mood_from_intent
            confidence = 'high'
            logger.info(f"Using mood from intent extractor: {mood_emoji}")
        elif not is_button_click:
            # Only extract mood from message if it's NOT a button click
            # Fallback to extracting mood from message
            mood_emoji, confidence = extract_mood_from_message(message)
            logger.info(f"Extracted mood from message: {mood_emoji} (confidence: {confidence})")
        
        # If user just said "I want to log mood" or clicked button without expressing emotion, ask for mood
        intent_keywords = ['want to log', 'log mood', 'log my mood', 'track mood', 'record mood']
        is_intent_only = is_button_click or any(keyword in message.lower() for keyword in intent_keywords)
        
        if is_intent_only and not mood_emoji:
            # User wants to log mood but hasn't expressed how they feel
            logger.info("User wants to log mood but hasn't expressed emotion - asking for mood")
            state.start_workflow(self.workflow_name, {'step': 'asking_mood'})
            return self._ask_clarification(
                message="How are you feeling right now?",
                ui_elements=['emoji_selector']
            )
        
        # If we're in asking_mood state and user responded, try to extract mood again
        if current_step == 'asking_mood' and not mood_emoji:
            # User responded to mood question but we couldn't extract emoji
            # Try extracting again with lower confidence threshold
            from .mood_extractor import extract_mood_from_message
            mood_emoji, confidence = extract_mood_from_message(message)
            logger.info(f"Re-extracted mood after asking: {mood_emoji} (confidence: {confidence})")
            
            if not mood_emoji:
                # Still no mood detected, ask again
                logger.warning(f"Could not extract mood from: {message}")
                return self._ask_clarification(
                    message="I didn't catch that. Please select how you're feeling:",
                    ui_elements=['emoji_selector']
                )
        
        # Accept both high and low confidence extractions
        if mood_emoji:
            logger.info(f"Extracted mood from message: {mood_emoji} (confidence: {confidence})")
            
            # NEW: Try to extract reason from the same message
            extracted_reason = None
            if not is_button_click and not is_intent_only:
                # Try to extract both mood and reason together
                from .mood_reason_extractor import extract_mood_and_reason
                combined = extract_mood_and_reason(message)
                
                if combined['reason'] and combined['confidence'] == 'high':
                    extracted_reason = combined['reason']
                    logger.info(f"✅ Extracted reason from message: '{extracted_reason}'")
            
            # Start workflow with extracted mood
            state.start_workflow(self.workflow_name, {
                'mood_emoji': mood_emoji,
                'step': 'mood_selected',
                'original_message': message,
                'extracted_reason': extracted_reason  # Store extracted reason
            })
            
            # Check if positive or negative
            if is_positive_mood(mood_emoji):
                # Positive mood - log and complete immediately
                mood_log = save_mood_log(user_id, mood_emoji, reason=extracted_reason)
                
                # Phase 2: Emit event after successful save
                try:
                    from app.services.event_publisher import get_event_publisher
                    publisher = get_event_publisher()
                    publisher.publish_mood_logged(
                        user_id=str(user_id),
                        mood_emoji=mood_emoji,
                        reason=extracted_reason,
                        mood_value=get_mood_value(mood_emoji)
                    )
                    logger.info(f"📊 Published mood_logged event for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish mood_logged event: {e}")
                
                # Don't update state, just complete
                state.complete_workflow()
                return self._create_positive_mood_response(mood_emoji, user_id=user_id)
            else:
                # Negative mood - check if we already have a reason
                if extracted_reason:
                    # We have both mood and reason! Skip asking and show suggestions directly
                    logger.info(f"✅ Have both mood and reason, showing suggestions directly")
                    
                    # Save mood with reason
                    mood_log = save_mood_log(user_id, mood_emoji, reason=extracted_reason)
                    
                    # Emit event
                    try:
                        from app.services.event_publisher import get_event_publisher
                        publisher = get_event_publisher()
                        publisher.publish_mood_logged(
                            user_id=str(user_id),
                            mood_emoji=mood_emoji,
                            reason=extracted_reason,
                            mood_value=get_mood_value(mood_emoji)
                        )
                        logger.info(f"📊 Published mood_logged event for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to publish mood_logged event: {e}")
                    
                    # Get suggestions based on the extracted reason
                    context = build_context(user_id)
                    suggestions = get_smart_suggestions(mood_emoji, extracted_reason, context, count=3)
                    
                    if suggestions:
                        # MULTI-INTENT FIX: Complete workflow immediately to allow secondary workflows
                        # Don't update workflow step since we're completing
                        state.complete_workflow()
                        
                        # Show suggestions with completed=True
                        return WorkflowResponse(
                            message=f"Here are some activities that might help with {extracted_reason}:",
                            ui_elements=['action_buttons_multiple'],
                            completed=True,  # ✅ Allow secondary workflows to execute
                            next_state=ConversationState.IDLE,
                            extra_data={
                                'actions': suggestions,
                                'events': [{'type': 'mood_logged', 'mood': mood_emoji, 'reason': extracted_reason}],
                                'ranking_context_id': context.get('ranking_context_id')
                            }
                        )
                    else:
                        # No suggestions, just acknowledge
                        state.complete_workflow()
                        return WorkflowResponse(
                            message="I understand. I'm here if you need anything.",
                            completed=True,
                            next_state=ConversationState.IDLE
                        )
                
                # No extracted reason - check if we should ask for reason
                if should_ask_reason(mood_emoji=mood_emoji, mood_text=message):
                    # Ask for reason (emotional negative)
                    reasons = get_mood_reasons()
                    return self._ask_clarification(
                        message="What's contributing to this feeling?",
                        ui_elements=['reason_selector'],
                        reasons=reasons
                    )
                else:
                    # Skip reason, directly suggest activities (mild physical)
                    logger.info(f"Skipping reason for mild physical mood: {mood_emoji}")
                    
                    # Save mood without reason
                    mood_log = save_mood_log(user_id, mood_emoji, reason="physical_state")
                    
                    # Emit event
                    try:
                        from app.services.event_publisher import get_event_publisher
                        publisher = get_event_publisher()
                        publisher.publish_mood_logged(
                            user_id=str(user_id),
                            mood_emoji=mood_emoji,
                            reason="physical_state",
                            mood_value=get_mood_value(mood_emoji)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to publish mood_logged event: {e}")
                    
                    # Get targeted suggestions for physical states
                    context = build_context(user_id)
                    # Don't filter by activity types - let smart_suggestions handle it
                    suggestions = get_smart_suggestions(mood_emoji, "tired", context, count=3)
                    
                    # ===== CONTEXT-AWARE RESPONSE ENGINE =====
                    # Use the response engine to decide how to respond
                    from app.services.context_aware_response_engine import get_response_engine
                    response_engine = get_response_engine()
                    
                    # Build workflow context for timing controller
                    workflow_context = {
                        'workflow_name': self.workflow_name,
                        'workflow_step': 'suggesting_action',
                        'mood_emoji': mood_emoji,
                        'reason': 'physical_state',
                        'activity_type': None
                    }
                    
                    decision = response_engine.analyze_and_decide(
                        user_id=user_id,
                        message=message,
                        mood_emoji=mood_emoji,
                        workflow_context=workflow_context
                    )
                    
                    logger.info(f"Response decision: {decision['response_strategy']}, "
                               f"show_buttons={decision['show_buttons']}, "
                               f"show_insight={decision['show_insight']}")
                    # ==========================================
                    
                    if suggestions and decision['show_buttons']:
                        # Store ranking_context_id for later selection tracking
                        ranking_context_id = context.get('ranking_context_id')
                        
                        state.update_workflow_step('suggesting_action', {
                            'reason': 'physical_state',
                            'suggestions': suggestions,
                            'ranking_context_id': ranking_context_id
                        })
                        
                        # Use LLM to create empathetic, contextual message
                        # Extract what user said (tired, exhausted, etc.)
                        user_feeling = message.lower().replace("i am", "").replace("i'm", "").replace("feeling", "").strip()
                        
                        # Build context for LLM including insights
                        context_summary = decision['context_summary']
                        
                        # NEW: Get structured insights from decision (deterministic)
                        triggered_insights = decision.get('triggered_insights', [])
                        
                        # Use response phraser with structured insights (no inline prompts!)
                        msg = phrase_contextual_suggestion(
                            user_message=message,
                            feeling=user_feeling,
                            activities=[s['name'] for s in suggestions],
                            tone=decision['tone'],
                            context_summary=context_summary,
                            triggered_insights=triggered_insights  # NEW: Structured insights
                        )
                        
                        # Check if any activities are external content
                        has_external_content = any(
                            act.get('action_type') == 'open_external' 
                            for act in suggestions
                        )
                        
                        # Always keep workflow active when showing suggestions
                        return self._ask_confirmation(
                            message=msg,
                            ui_elements=['action_buttons_multiple'],
                            actions=suggestions,
                            events=[{'type': 'mood_logged', 'mood': mood_emoji, 'reason': 'physical_state'}]
                        )
                    else:
                        # No suggestions - use empathetic response
                        msg = phrase_empathetic_response(
                            user_message=message,
                            mood_context=mood_emoji
                        )
                        
                        state.complete_workflow()
                        return WorkflowResponse(
                            message=msg,
                            completed=True,
                            next_state=ConversationState.IDLE
                        )
        
        # Couldn't extract mood - ask explicitly
        state.start_workflow(self.workflow_name, {'step': 'asking_mood'})
        
        return self._ask_clarification(
            message="How are you feeling?",
            ui_elements=['emoji_selector']
        )
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Process message in active mood workflow"""
        step = state.get_workflow_data('step')
        logger.info(f"Processing mood workflow, step: {step}")
        
        # UNIVERSAL: Check if user returned from external activity
        return_response = self.handle_external_activity_return(message, state, user_id)
        if return_response:
            return return_response
        
        # UNIVERSAL: Check if user is providing feedback
        feedback_response = self.handle_external_activity_feedback(message, state, user_id)
        if feedback_response:
            return feedback_response
        
        if step == 'asking_mood':
            return self._handle_mood_selection(message, state, user_id)
        
        elif step == 'mood_selected':
            return self._handle_reason_selection(message, state, user_id)
        
        elif step == 'asking_custom_reason':
            return self._handle_custom_reason(message, state, user_id)
        
        elif step == 'suggesting_action':
            return self._handle_action_response(message, state, user_id)
        
        elif step == 'waiting_feedback':
            return self._handle_activity_feedback(message, state, user_id)
        
        # Unknown step - complete
        logger.warning(f"Unknown step '{step}' in mood workflow")
        return self._complete_workflow(message="Mood logging completed.")
    
    def _handle_mood_selection(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle mood emoji selection"""
        if not validate_mood_emoji(message):
            return self._ask_clarification(
                message="Please select a mood emoji.",
                ui_elements=['emoji_selector']
            )
        
        mood_emoji = message
        state.update_workflow_step('mood_selected', {'mood_emoji': mood_emoji})
        
        if is_positive_mood(mood_emoji):
            # Positive mood - log and complete
            mood_log = save_mood_log(user_id, mood_emoji, reason=None)
            
            # Phase 2: Emit event after successful save
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                publisher.publish_mood_logged(
                    user_id=str(user_id),
                    mood_emoji=mood_emoji,
                    reason=None,
                    mood_value=get_mood_value(mood_emoji)
                )
                logger.info(f"📊 Published mood_logged event for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to publish mood_logged event: {e}")
            
            return self._create_positive_mood_response(mood_emoji, user_id=user_id)
        else:
            # Negative mood - ask for reason
            reasons = get_mood_reasons()
            return self._ask_clarification(
                message="What's contributing to this feeling?",
                ui_elements=['reason_selector'],
                reasons=reasons
            )
    
    def _handle_reason_selection(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle reason selection"""
        mood_emoji = state.get_workflow_data('mood_emoji')
        
        # Check if user selected "Other" - ask for custom reason
        if message.lower() in ['other', 'something else', 'other reason']:
            logger.info(f"User selected 'Other' - asking for custom reason")
            state.update_workflow_step('asking_custom_reason', {
                'mood_emoji': mood_emoji
            })
            return self._ask_clarification(
                message="Tell me more - what's on your mind?",
                ui_elements=['text_input']
            )
        
        # Handle "skip"
        if message.lower() == 'skip':
            reason = None
        else:
            reason = message
        
        # Save mood log
        mood_log = save_mood_log(user_id, mood_emoji, reason)
        
        # Phase 2: Emit event after successful save
        try:
            from app.services.event_publisher import get_event_publisher
            publisher = get_event_publisher()
            publisher.publish_mood_logged(
                user_id=str(user_id),
                mood_emoji=mood_emoji,
                reason=reason,
                mood_value=get_mood_value(mood_emoji)
            )
            logger.info(f"📊 Published mood_logged event for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to publish mood_logged event: {e}")
        
        # ===== PROACTIVE INSIGHTS =====
        # Check for concerning patterns after logging negative mood
        proactive_insight = None
        if not is_positive_mood(mood_emoji):
            try:
                from app.services.insight_generator import get_insight_generator
                from app.services.pattern_detector import PatternDetector
                
                insight_gen = get_insight_generator()
                pattern_detector = PatternDetector()
                
                # Get patterns
                patterns = pattern_detector.detect_all_patterns(user_id)
                
                # Generate insights (only high priority for proactive)
                insights = insight_gen.generate_insights(user_id, current_mood=mood_emoji)
                high_priority_insights = [i for i in insights if i.priority == 1]
                
                if high_priority_insights:
                    insight = high_priority_insights[0]
                    
                    # Format insight message
                    if insight.insight_type == 'prolonged_stress_pattern':
                        days = insight.data['consecutive_days']
                        recurring_reason = insight.data.get('recurring_reason', 'various reasons')
                        proactive_insight = f"\n\n💡 I've noticed you've been stressed for {days} consecutive days, mostly about {recurring_reason}. Let's work on this together."
                    
                    elif insight.insight_type == 'stress_inactivity_cycle':
                        days = insight.data['stressed_days']
                        drop = insight.data['activity_drop']
                        proactive_insight = f"\n\n💡 I've noticed you've been stressed for {days} days and your activity has dropped {drop:.0f}%. This pattern can make things harder. Let's break it together."
                    
                    # Add health patterns if available
                    if patterns and 'health_patterns' in patterns:
                        health = patterns['health_patterns']
                        if health.get('sleep_decline'):
                            sleep_current = health.get('sleep_current_avg', 0)
                            sleep_baseline = health.get('sleep_baseline_avg', 0)
                            if proactive_insight:
                                proactive_insight += f"\n\nI also see your sleep has decreased to {sleep_current:.1f} hours (from {sleep_baseline:.1f}). This can affect how you feel."
                    
                    # Mark insight as shown
                    if proactive_insight:
                        insight_gen.mark_insight_shown(user_id, insight.insight_type)
                        logger.info(f"🔔 Showing proactive insight: {insight.insight_type}")
                
            except Exception as e:
                logger.error(f"Failed to generate proactive insight: {e}", exc_info=True)
        # ==============================
        
        # Get up to 3 context-aware activity suggestions
        context = build_context(user_id)
        suggestions = get_smart_suggestions(mood_emoji, reason or '', context, count=3)
        
        # Get 2 personalized content suggestions (with user context)
        content_suggestions = get_content_suggestions(
            user_id=user_id,
            mood_emoji=mood_emoji,
            reason=reason,
            user_context=context,
            count=2
        )
        
        # Combine activity and content suggestions
        all_suggestions = suggestions + content_suggestions
        
        if all_suggestions:
            # Store ranking_context_id for later selection tracking
            ranking_context_id = context.get('ranking_context_id')
            
            state.update_workflow_step('suggesting_action', {
                'reason': reason,
                'suggestions': all_suggestions,
                'ranking_context_id': ranking_context_id
            })
            
            # Phase 2: Emit suggestion_shown events (only for activities, not content)
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                for suggestion in suggestions:  # Only activity suggestions
                    suggestion_key = suggestion.get('id') or suggestion.get('suggestion_key')
                    publisher.publish_suggestion_shown(
                        user_id=str(user_id),
                        suggestion_key=suggestion_key,
                        mood_emoji=mood_emoji,
                        reason=reason
                    )
                logger.info(f"📊 Published {len(suggestions)} suggestion_shown events")
            except Exception as e:
                logger.warning(f"Failed to publish suggestion_shown events: {e}")
            
            # Create natural message based on number of suggestions
            if len(all_suggestions) == 1:
                message = f"Would you like to try {all_suggestions[0]['name']}?"
            elif len(all_suggestions) == 2:
                message = f"Would you like to try {all_suggestions[0]['name']} or {all_suggestions[1]['name']}?"
            else:
                message = f"Here are some things that might help. What would you like to try?"
            
            # Add proactive insight if available
            if proactive_insight:
                message = proactive_insight + "\n\n" + message
            
            # Check if any activities are external content
            has_external_content = any(
                act.get('action_type') == 'open_external' 
                for act in all_suggestions
            )
            
            # Always keep workflow active when showing suggestions
            return self._ask_confirmation(
                message=message,
                ui_elements=['action_buttons_multiple'],
                actions=all_suggestions,
                events=[
                    {'type': 'mood_logged', 'mood': mood_emoji, 'reason': reason},
                    {'type': 'suggestions_shown', 'count': len(suggestions)}
                ]
            )
        else:
            # No suggestion - complete
            return self._complete_workflow(
                message="Your mood has been logged."
            )
    
    def _handle_custom_reason(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle custom reason input when user selected 'Other'"""
        mood_emoji = state.get_workflow_data('mood_emoji')
        
        # Use the custom reason provided by user
        reason = message.strip()
        
        # Validate that user provided something meaningful
        if not reason or len(reason) < 3:
            return self._ask_clarification(
                message="Please tell me a bit more about what's bothering you, or say 'skip' to continue without a reason.",
                ui_elements=['text_input']
            )
        
        logger.info(f"User provided custom reason: '{reason}'")
        
        # Save mood log with custom reason
        mood_log = save_mood_log(user_id, mood_emoji, reason)
        
        # Phase 2: Emit event after successful save
        try:
            from app.services.event_publisher import get_event_publisher
            publisher = get_event_publisher()
            publisher.publish_mood_logged(
                user_id=str(user_id),
                mood_emoji=mood_emoji,
                reason=reason,
                mood_value=get_mood_value(mood_emoji)
            )
            logger.info(f"📊 Published mood_logged event for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to publish mood_logged event: {e}")
        
        # Get context-aware activity suggestions based on custom reason
        context = build_context(user_id)
        suggestions = get_smart_suggestions(mood_emoji, reason, context, count=3)
        
        # Get 2 personalized content suggestions (with user context)
        content_suggestions = get_content_suggestions(
            user_id=user_id,
            mood_emoji=mood_emoji,
            reason=reason,
            user_context=context,
            count=2
        )
        
        # Combine activity and content suggestions
        all_suggestions = suggestions + content_suggestions
        
        if all_suggestions:
            # Store ranking_context_id for later selection tracking
            ranking_context_id = context.get('ranking_context_id')
            
            state.update_workflow_step('suggesting_action', {
                'reason': reason,
                'suggestions': all_suggestions,
                'ranking_context_id': ranking_context_id
            })
            
            # Phase 2: Emit suggestion_shown events (only for activities)
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                for suggestion in suggestions:  # Only activity suggestions
                    suggestion_key = suggestion.get('id') or suggestion.get('suggestion_key')
                    publisher.publish_suggestion_shown(
                        user_id=str(user_id),
                        suggestion_key=suggestion_key,
                        mood_emoji=mood_emoji,
                        reason=reason
                    )
                logger.info(f"📊 Published {len(suggestions)} suggestion_shown events")
            except Exception as e:
                logger.warning(f"Failed to publish suggestion_shown events: {e}")
            
            # Create natural message based on number of suggestions
            if len(all_suggestions) == 1:
                message = f"I understand. Would you like to try {all_suggestions[0]['name']}?"
            elif len(all_suggestions) == 2:
                message = f"I understand. Would you like to try {all_suggestions[0]['name']} or {all_suggestions[1]['name']}?"
            else:
                message = f"I understand. Here are some things that might help. What would you like to try?"
            
            return self._ask_confirmation(
                message=message,
                ui_elements=['action_buttons_multiple'],
                actions=suggestions,
                events=[
                    {'type': 'mood_logged', 'mood': mood_emoji, 'reason': reason},
                    {'type': 'suggestions_shown', 'count': len(suggestions)}
                ]
            )
        else:
            # No suggestion - complete
            return self._complete_workflow(
                message="I understand. Your mood has been logged."
            )
    
    def _handle_action_response(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle action confirmation"""
        logger.info(f"Handling action response: '{message}'")
        
        # Map contextless input
        intent = self.handle_contextless_input(message)
        logger.info(f"Intent mapped: {intent}")
        
        suggestions = state.get_workflow_data('suggestions', [])
        logger.info(f"📊 Found {len(suggestions)} suggestions in state")
        
        # Check if user selected a specific activity or said yes/no
        selected_activity = None
        
        if intent == 'decline' or 'skip' in message.lower():
            # User declined - track globally
            logger.info("User declined activity suggestion")
            
            # Use global rejection tracking
            state.track_rejection()
            
            if state.should_stop_suggesting():
                # User rejected 2+ times - stop suggesting
                logger.info(f"User rejected {state.get_rejection_count()} times - stopping suggestions")
                state.reset_rejection_count()
                return self._complete_workflow(
                    message="No problem! I'm here if you need anything else. 😊"
                )
            
            # First rejection - offer alternatives
            from app.services.engagement_context_analyzer import EngagementContextAnalyzer
            analyzer = EngagementContextAnalyzer()
            
            engagement = analyzer.analyze_context(user_id, {
                'mood_emoji': state.get_workflow_data('mood_emoji'),
                'reason': state.get_workflow_data('reason'),
                'declined_activity': True
            })
            
            logger.info(f"Engagement buttons: {engagement['buttons']}")
            
            # Convert to actions format
            actions = [
                {'id': btn['action'], 'name': btn['label']} 
                for btn in engagement['buttons']
            ]
            
            logger.info(f"Actions to send: {actions}")
            
            return self._complete_workflow(
                message=engagement['message'],
                ui_elements=['action_buttons_multiple'],
                actions=actions
            )
        elif intent == 'confirm' or 'yes' in message.lower():
            # User said yes - use first suggestion
            if suggestions:
                selected_activity = suggestions[0]
        else:
            # Check if message matches any suggested activity name or ID
            message_lower = message.lower()
            
            for suggestion in suggestions:
                # Get both name and title (for compatibility)
                activity_name = (suggestion.get('name') or suggestion.get('title', '')).lower()
                activity_id = str(suggestion.get('id', ''))
                
                logger.info(f"Checking suggestion: '{activity_name}' (ID: {activity_id})")
                
                # Check if message contains the activity name or ID
                if activity_name and activity_name in message_lower:
                    selected_activity = suggestion
                    logger.info(f"✅ Matched by name: '{activity_name}'")
                    break
                elif activity_id and activity_id in message:
                    selected_activity = suggestion
                    logger.info(f"✅ Matched by ID: {activity_id}")
                    break
                # Also check if message is like "I want to [activity]"
                elif message_lower.startswith('i want to') and activity_name in message_lower:
                    selected_activity = suggestion
                    logger.info(f"✅ Matched by 'I want to' pattern")
                    break
                # Check for "Watch/Read/Listen" patterns
                elif any(verb in message_lower for verb in ['watch', 'read', 'listen']) and activity_name in message_lower:
                    selected_activity = suggestion
                    logger.info(f"✅ Matched by verb pattern")
                    break
        
        if selected_activity:
            # Phase 2: Emit suggestion_accepted event
            try:
                from app.services.event_publisher import get_event_publisher
                publisher = get_event_publisher()
                suggestion_key = selected_activity.get('id') or selected_activity.get('suggestion_key')
                publisher.publish_suggestion_accepted(
                    user_id=str(user_id),
                    suggestion_key=suggestion_key
                )
                logger.info(f"📊 Published suggestion_accepted event for {suggestion_key}")
            except Exception as e:
                logger.warning(f"Failed to publish suggestion_accepted event: {e}")
            
            # Track ranking selection for quality analysis
            try:
                ranking_context_id = state.get_workflow_data('ranking_context_id')
                if ranking_context_id:
                    from app.services.ranking_context_logger import RankingContextLogger
                    ranking_logger = RankingContextLogger()
                    suggestion_key = selected_activity.get('id') or selected_activity.get('suggestion_key')
                    ranking_logger.log_user_selection(ranking_context_id, suggestion_key)
                    logger.info(f"📊 Logged user selection for ranking context {ranking_context_id}")
            except Exception as e:
                logger.warning(f"Failed to log ranking selection: {e}")
            
            # Save activity to history
            from .user_history import save_activity_to_history
            mood_emoji = state.get_workflow_data('mood_emoji')
            reason = state.get_workflow_data('reason')
            
            save_activity_to_history(
                user_id=user_id,
                activity_id=selected_activity['id'],
                activity_name=selected_activity['name'],
                mood_emoji=mood_emoji,
                reason=reason,
                completed=True
            )
            
            # Check if this is an external activity (YouTube, blog, etc.)
            is_external = selected_activity.get('action_type') == 'open_external'
            is_module = selected_activity.get('is_module', False)
            
            # Build response message
            if is_module:
                # Module-based activity - user will be taken to another screen
                message = f"Great! Starting {selected_activity['name']}. I'll be here when you're done! 💪"
            elif is_external:
                # External activity - user will open in new tab
                message = f"Great choice! Opening {selected_activity['name']}. Take your time, and let me know when you're done! 💙"
            else:
                # Non-module activity - user does it themselves
                message = f"Awesome! Take your time with {selected_activity['name']}. I'm here if you need anything! 💙"
            
            response_data = {
                'message': message,
                'events': [{'type': 'suggestion_accepted', 'activity': selected_activity['id']}]
            }
            
            # Add module trigger info if it's a module
            if is_module:
                response_data['trigger_module'] = selected_activity['id']
                response_data['module_name'] = selected_activity['name']
            
            # For external activities, use universal external activity handler
            if is_external:
                # Update step to waiting_feedback so process() knows we're waiting
                state.update_workflow_step('waiting_feedback', {
                    'activity_id': selected_activity['id'],
                    'activity_name': selected_activity['name'],
                    'mood_emoji': mood_emoji,
                    'reason': reason
                })
                
                return self.start_external_activity(
                    state=state,
                    activity_id=str(selected_activity['id']),
                    activity_name=selected_activity['name']
                )
            else:
                # For other activities, complete the workflow
                return self._complete_workflow(**response_data)
        else:
          
            # Couldn't determine selection - ask again
            return self._ask_confirmation(
                message="Which activity would you like to try? Or say 'skip' to continue.",
                ui_elements=['action_buttons_multiple'],
                actions=suggestions
            )

    def _handle_activity_feedback(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle feedback after external activity completion"""
        activity_name = state.get_workflow_data('activity_name', 'the activity')
        
        logger.info(f"Handling activity feedback for: {activity_name}")
        
        # Check if user is ready for feedback or just returned
        message_lower = message.lower().strip()
        
        # If user returned from external activity, ask for feedback immediately
        if message_lower in ['returned_from_external_activity', 'returned_from_activity']:
            logger.info(f"User returned from external activity: {activity_name}")
            # Ask for feedback
            feedback_actions = [
                {'id': 'helpful', 'name': '👍 Helpful'},
                {'id': 'not_helpful', 'name': '👎 Not helpful'},
                {'id': 'skip_feedback', 'name': 'Skip'}
            ]
            
            return self._ask_confirmation(
                message=f"Welcome back! Was \"{activity_name}\" helpful?",
                ui_elements=['action_buttons_multiple'],
                actions=feedback_actions
            )
        
        # If user just says something casual, ask for feedback
        casual_responses = ['done', 'finished', 'back', 'im back', "i'm back", 'completed', 'ok', 'okay']
        if message_lower in casual_responses or len(message) < 10:
            # Ask for feedback
            feedback_actions = [
                {'id': 'helpful', 'name': '👍 Helpful'},
                {'id': 'not_helpful', 'name': '👎 Not helpful'},
                {'id': 'skip_feedback', 'name': 'Skip'}
            ]
            
            return self._ask_confirmation(
                message=f"Welcome back! Was \"{activity_name}\" helpful?",
                ui_elements=['action_buttons_multiple'],
                actions=feedback_actions
            )
        
        # Check if this is feedback
        if message_lower in ['helpful', 'yes', 'yeah', 'yep'] or 'helpful' in message_lower:
            feedback = 'helpful'
        elif message_lower in ['not_helpful', 'no', 'nope', 'not really'] or 'not helpful' in message_lower:
            feedback = 'not_helpful'
        elif message_lower in ['skip', 'skip_feedback']:
            feedback = 'skip'
        else:
            # User said something else - treat as general conversation and complete
            return self._complete_workflow(
                message="Thanks for trying that! I'm here if you need anything else. 😊"
            )
        
        # Log feedback
        if feedback != 'skip':
            logger.info(f"User feedback for {activity_name}: {feedback}")
            # TODO: Store feedback in database
        
        # Thank user and complete
        if feedback == 'helpful':
            response_message = f"That's great to hear! I'm glad \"{activity_name}\" helped. 😊"
        elif feedback == 'not_helpful':
            response_message = f"Thanks for letting me know. I'll keep that in mind for next time. 💙"
        else:
            response_message = "No problem! I'm here if you need anything else. 😊"
        
        return self._complete_workflow(message=response_message)

    def _get_mood_name(self, mood_emoji: str) -> str:
        """Get friendly name for mood emoji"""
        mood_names = {
            '😊': 'Happy',
            '😄': 'Very Happy',
            '😐': 'Neutral',
            '😔': 'Sad',
            '😢': 'Very Sad',
            '😡': 'Angry',
            '😰': 'Anxious',
            '😴': 'Tired',
            '🤗': 'Grateful',
            '😌': 'Calm'
        }
        return mood_names.get(mood_emoji, 'Good')
    
    def _create_positive_mood_response(self, mood_emoji: str, user_id: int = None, reason: str = None) -> WorkflowResponse:
        """Create response for positive mood with proactive features"""
        from chat_assistant.proactive_helpers import add_proactive_mood_response
        
        # If user_id provided, use proactive response
        if user_id:
            proactive_response = add_proactive_mood_response(user_id, mood_emoji, reason)
            
            return WorkflowResponse(
                message=proactive_response['message'],
                completed=True,
                next_state=ConversationState.IDLE,
                ui_elements=[],
                extra_data=proactive_response.get('metadata', {})
            )
        
        # Fallback to simple response
        mood_name = self._get_mood_name(mood_emoji)
        return WorkflowResponse(
            message=f"✓ Logged: {mood_name} mood {mood_emoji}\n\nThat's wonderful! Keep that positive energy going! 🎉",
            completed=True,
            next_state=ConversationState.IDLE,
            ui_elements=[],
            extra_data={}
        )
    
    def _update_session_summary(self, state: WorkflowState, mood_emoji: str):
        """
        Update session summary after mood logging
        
        Args:
            state: Workflow state with session summary
            mood_emoji: Mood emoji that was logged
        """
        from .session_summary import SessionFocus
        
        # Set focus to mood
        state.session_summary.set_focus(SessionFocus.MOOD)
        
        # Store the logged mood as preference for potential follow-ups
        state.session_summary.set_preference('last_mood', mood_emoji)
        
        logger.info(f"Updated session summary: {state.session_summary}")
