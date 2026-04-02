# chat_engine_with_suggestions.py
# Complete chat engine with reason selection and action suggestions

from .conversation_state import (
    ConversationState, get_state, set_state, reset_state,
    save_user_data, get_user_data, clear_user_data
)
from .mood_handler import (
    validate_mood_emoji, save_mood_log, has_logged_mood_today,
    is_positive_mood, is_negative_mood, get_last_mood_log_time
)
from .llm_intent_detector import detect_intent
from .mood_extractor import extract_mood_from_message
from .context_builder_simple import build_context
from .response_phrasing import phrase_response
from .response_validation import validate_response, get_fallback_response
from .action_suggestions import get_mood_reasons, WELLNESS_ACTIONS
from .smart_suggestions import get_smart_suggestions
from .user_history import save_activity_to_history
from .llm_service import get_llm_service
from .activity_chat_handler import ActivityChatHandler
from app.services.suggestion_interaction_tracker import SuggestionInteractionTracker
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize activity handler and suggestion tracker
activity_handler = ActivityChatHandler()
suggestion_tracker = SuggestionInteractionTracker()

def process_message(user_id, message):
    """
    Main entry point - complete flow with reason selection and suggestions
    """
    current_state = get_state(user_id)
    logger.info(f"Processing message for user {user_id}, state: {current_state}")
    
    # Check if we're waiting for activity value input
    if current_state == 'AWAITING_ACTIVITY_VALUE':
        return activity_handler.handle_activity_value_input(user_id, message)
    
    if current_state == ConversationState.IDLE:
        return handle_idle_state(user_id, message)
    
    elif current_state == ConversationState.ASKING_MOOD:
        return handle_mood_selection(user_id, message)
    
    elif current_state == ConversationState.ASKING_REASON:
        return handle_reason_selection(user_id, message)
    
    elif current_state == ConversationState.SUGGESTING_ACTION:
        return handle_action_response(user_id, message)
    
    else:
        reset_state(user_id)
        return _build_response('continue', user_id, ConversationState.IDLE)

def handle_idle_state(user_id, message):
    """Handle IDLE state - detect intent and extract mood from natural language"""
    
    # First check for activity logging intent
    mood_logged = has_logged_mood_today(user_id)
    activity_response = activity_handler.process_activity_message(user_id, message, mood_logged)
    
    if activity_response:
        # Activity was detected and logged, or suggestions provided
        if activity_response.get('state'):
            set_state(user_id, activity_response['state'])
        return activity_response
    
    # First detect intent
    intent = detect_intent(message)
    logger.info(f"Detected intent: {intent}")
    
    # If mood intent detected, try to extract mood from message
    if intent == 'log_mood':
        # Try to extract mood directly from the message
        mood_emoji, confidence = extract_mood_from_message(message)
        
        if mood_emoji and confidence == 'high':
            # Mood extracted successfully! Skip mood selection
            logger.info(f"✅ Mood extracted from message: {mood_emoji}")
            save_user_data(user_id, 'mood_emoji', mood_emoji)
            
            if is_positive_mood(mood_emoji):
                # Positive mood - log immediately
                save_mood_log(user_id, mood_emoji, reason=None)
                clear_user_data(user_id)
                reset_state(user_id)
                
                return _build_response('confirm_positive', user_id, ConversationState.IDLE)
            else:
                # Negative/neutral mood - ask for reason directly
                set_state(user_id, ConversationState.ASKING_REASON)
                reasons = get_mood_reasons()
                
                # Use LLM for natural acknowledgment
                llm_service = get_llm_service()
                if llm_service.is_available():
                    prompt = f"""You are a supportive wellness assistant. The user said: "{message}"

Generate a brief, empathetic acknowledgment (1 sentence) before asking for the reason.

Examples:
- "I'm sorry to hear you're not feeling well."
- "I understand you're going through a tough time."
- "That sounds really challenging."

Response:"""
                    
                    ack_text = llm_service.call(prompt, max_tokens=30, temperature=0.7)
                    if ack_text:
                        response_message = f"{ack_text} What's contributing to this feeling?"
                    else:
                        response_message = "What's contributing to this feeling?"
                else:
                    response_message = "What's contributing to this feeling?"
                
                return {
                    'message': response_message,
                    'ui_elements': ['reason_selector'],
                    'reasons': reasons,
                    'state': ConversationState.ASKING_REASON
                }
        else:
            # Couldn't extract mood confidently - ask for clarification
            set_state(user_id, ConversationState.ASKING_MOOD)
            return _build_response('ask_mood_reactive', user_id, ConversationState.ASKING_MOOD, 
                                 ui_elements=['emoji_selector'])
    
    # For non-mood messages, check cooldown
    last_log_time = get_last_mood_log_time(user_id)
    if last_log_time:
        time_since_log = (datetime.now() - last_log_time).total_seconds()
        if time_since_log < 120:  # Less than 2 minutes
            # User just logged mood, they're probably just chatting
            logger.info(f"User logged mood {time_since_log:.0f}s ago, treating as casual chat")
            
            # Use LLM to generate a conversational response
            llm_service = get_llm_service()
            if llm_service.is_available():
                prompt = f"""You are a supportive wellness assistant. The user just completed a wellness activity and said: "{message}"

Generate a brief, warm, encouraging response (1-2 sentences). Be conversational and supportive. Don't ask questions. Just acknowledge their feeling positively.

Examples:
- "That's wonderful! It sounds like the activity really helped."
- "I'm so glad to hear that! Keep up the great work."
- "That's fantastic! Taking care of yourself is so important."

Response:"""
                
                response_text = llm_service.call(prompt, max_tokens=50, temperature=0.7)
                if response_text:
                    return {
                        'message': response_text,
                        'ui_elements': [],
                        'state': ConversationState.IDLE
                    }
            
            # Fallback if LLM not available
            return {
                'message': "That's wonderful! I'm glad you're feeling better. 😊",
                'ui_elements': [],
                'state': ConversationState.IDLE
            }
    
    # Unknown intent - use LLM for conversational response
    llm_service = get_llm_service()
    if llm_service.is_available():
        prompt = f"""You are a wellness assistant in a fitness app. The user said: "{message}"

This doesn't seem to be a mood logging request. Generate a brief, friendly response (1-2 sentences) that:
- Acknowledges what they said
- Gently reminds them you can help log their mood
- Stays supportive and warm

Examples:
- "I appreciate you sharing that! If you'd like to log how you're feeling, just let me know."
- "Thanks for telling me! Whenever you want to track your mood, I'm here to help."

Response:"""
        
        response_text = llm_service.call(prompt, max_tokens=50, temperature=0.7)
        if response_text:
            return {
                'message': response_text,
                'ui_elements': [],
                'state': ConversationState.IDLE
            }
    
    return _build_response('unknown_intent', user_id, ConversationState.IDLE)

def handle_mood_selection(user_id, message):
    """Handle mood emoji selection"""
    if not validate_mood_emoji(message):
        return _build_response('ask_mood_reactive', user_id, ConversationState.ASKING_MOOD,
                             ui_elements=['emoji_selector'])
    
    save_user_data(user_id, 'mood_emoji', message)
    logger.info(f"User {user_id} selected mood: {message}")
    
    if is_positive_mood(message):
        # Positive mood - log immediately, no reason or suggestion needed
        save_mood_log(user_id, message, reason=None)
        clear_user_data(user_id)
        reset_state(user_id)
        
        return _build_response('confirm_positive', user_id, ConversationState.IDLE)
    
    else:
        # Negative/neutral mood - ask for reason
        set_state(user_id, ConversationState.ASKING_REASON)
        
        # Get predefined reasons
        reasons = get_mood_reasons()
        
        return {
            'message': "What's contributing to this feeling?",
            'ui_elements': ['reason_selector'],
            'reasons': reasons,
            'state': ConversationState.ASKING_REASON
        }

def handle_reason_selection(user_id, message):
    """Handle reason selection and provide smart suggestions"""
    mood_emoji = get_user_data(user_id, 'mood_emoji')
    
    # Check if user selected "other" - need custom input
    if message.lower() == 'other':
        save_user_data(user_id, 'reason_type', 'other')
        return {
            'message': 'Please tell me more about what\'s affecting your mood:',
            'ui_elements': ['text_input', 'skip_button'],
            'state': ConversationState.ASKING_REASON
        }
    
    # Check if this is custom text after selecting "other"
    reason_type = get_user_data(user_id, 'reason_type')
    if reason_type == 'other':
        reason = message if message.lower() != 'skip' else 'other'
    else:
        reason = message if message.lower() != 'skip' else None
    
    # Save reason
    save_user_data(user_id, 'reason', reason)
    
    # Build rich context for smart suggestions
    context = build_context(user_id)
    
    # Get smart suggestions (up to 3 activities)
    suggestions = get_smart_suggestions(mood_emoji, reason or '', context, count=3)
    
    if suggestions:
        # Track that suggestions were shown
        for suggestion in suggestions:
            try:
                suggestion_tracker.track_shown(
                    user_id=user_id,
                    suggestion_key=suggestion['id'],
                    mood_emoji=mood_emoji,
                    reason=reason
                )
                logger.info(f"Tracked suggestion shown: {suggestion['id']} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to track suggestion: {e}")
        
        # Save suggestions and move to suggesting state
        suggestion_ids = [s['id'] for s in suggestions]
        save_user_data(user_id, 'suggested_actions', ','.join(suggestion_ids))
        set_state(user_id, ConversationState.SUGGESTING_ACTION)
        
        # Build message with multiple suggestions
        if len(suggestions) == 1:
            message_text = f"Would you like to try {suggestions[0]['name']}? It might help."
        else:
            activity_list = ", ".join([s['name'] for s in suggestions[:-1]]) + f", or {suggestions[-1]['name']}"
            message_text = f"Here are some activities that might help: {activity_list}. Which would you like to try?"
        
        return {
            'message': message_text,
            'ui_elements': ['action_buttons_multiple'],
            'actions': suggestions,
            'state': ConversationState.SUGGESTING_ACTION
        }
    else:
        # No suggestion - just log mood
        save_mood_log(user_id, mood_emoji, reason)
        clear_user_data(user_id)
        reset_state(user_id)
        
        return _build_response('confirm_negative', user_id, ConversationState.IDLE)
        save_mood_log(user_id, mood_emoji, reason)
        clear_user_data(user_id)
        reset_state(user_id)
        
        return _build_response('confirm_negative', user_id, ConversationState.IDLE)

def handle_action_response(user_id, message):
    """Handle user response to action suggestion"""
    mood_emoji = get_user_data(user_id, 'mood_emoji')
    reason = get_user_data(user_id, 'reason')
    suggested_actions_str = get_user_data(user_id, 'suggested_actions')
    
    # Parse suggested actions
    suggested_actions = suggested_actions_str.split(',') if suggested_actions_str else []
    
    # Log mood
    save_mood_log(user_id, mood_emoji, reason)
    
    # Check if user selected an activity
    message_lower = message.lower()
    selected_activity = None
    
    # Check if message matches any suggested activity
    for act_id in suggested_actions:
        if act_id in message_lower or message_lower in ['yes', 'start', 'ok']:
            selected_activity = act_id
            break
    
    # If user said yes/start and only one suggestion, use that
    if not selected_activity and message_lower in ['yes', 'start', 'ok'] and len(suggested_actions) == 1:
        selected_activity = suggested_actions[0]
    
    # Clear temporary data
    clear_user_data(user_id)
    reset_state(user_id)
    
    if selected_activity:
        # Track that suggestion was accepted
        try:
            suggestion_tracker.track_accepted(user_id, selected_activity)
            logger.info(f"Tracked suggestion accepted: {selected_activity} for user {user_id}")
            
            # Also log which rank was selected for ranking quality analysis
            from .user_history import get_user_data
            ranking_context_id = get_user_data(user_id, 'ranking_context_id')
            if ranking_context_id:
                from app.services.ranking_context_logger import RankingContextLogger
                ranking_logger = RankingContextLogger()
                ranking_logger.log_user_selection(ranking_context_id, selected_activity)
                logger.info(f"Logged user selection for ranking context {ranking_context_id}")
        except Exception as e:
            logger.error(f"Failed to track acceptance: {e}")
        
        # Save activity to history
        from .smart_suggestions import WELLNESS_ACTIVITIES
        activity = WELLNESS_ACTIVITIES.get(selected_activity)
        
        if activity:
            save_activity_to_history(
                user_id=user_id,
                activity_id=activity['id'],
                activity_name=activity['name'],
                mood_emoji=mood_emoji,
                reason=reason,
                completed=True
            )
            logger.info(f"✅ Saved activity {activity['name']} to user history")
        
        # Use LLM to generate encouraging start message
        llm_service = get_llm_service()
        if llm_service.is_available() and activity:
            prompt = f"""You are a supportive wellness assistant. The user just agreed to start: {activity['name']}

Generate a brief, encouraging message (1 sentence) to motivate them. Be warm and supportive.

Examples:
- "Wonderful! Take your time and focus on your breathing."
- "Great choice! Enjoy this moment of calm."
- "Perfect! Let yourself relax and be present."

Response:"""
            
            response_text = llm_service.call(prompt, max_tokens=40, temperature=0.7)
            if response_text:
                return {
                    'message': response_text,
                    'ui_elements': [],
                    'state': ConversationState.IDLE
                }
        
        return {
            'message': f'Great! Starting {activity["name"] if activity else selected_activity}. Take your time.',
            'ui_elements': [],
            'state': ConversationState.IDLE
        }
    else:
        # User skipped
        llm_service = get_llm_service()
        if llm_service.is_available():
            prompt = f"""You are a supportive wellness assistant. The user declined a wellness activity suggestion.

Generate a brief, understanding response (1 sentence). Be supportive and non-judgmental.

Examples:
- "No problem! Your mood has been logged. Take care of yourself."
- "That's okay! I'm here whenever you need support."
- "Understood! Remember, I'm here to help anytime."

Response:"""
            
            response_text = llm_service.call(prompt, max_tokens=40, temperature=0.7)
            if response_text:
                return {
                    'message': response_text,
                    'ui_elements': [],
                    'state': ConversationState.IDLE
                }
        
        return {
            'message': 'No problem. Your mood has been logged.',
            'ui_elements': [],
            'state': ConversationState.IDLE
        }

def init_conversation(user_id):
    """Initialize conversation with proactive mood check"""
    current_state = get_state(user_id)
    
    if current_state != ConversationState.IDLE:
        return _build_response('continue', user_id, current_state)
    
    if not has_logged_mood_today(user_id):
        set_state(user_id, ConversationState.ASKING_MOOD)
        return _build_response('ask_mood_proactive', user_id, ConversationState.ASKING_MOOD,
                             ui_elements=['emoji_selector'])
    else:
        return _build_response('greeting', user_id, ConversationState.IDLE)

def _build_response(template_key: str, user_id: str, state: str, ui_elements: list = None):
    """Build complete response"""
    context = build_context(user_id)
    message = phrase_response(template_key, context)
    
    is_valid, error_reason = validate_response(message)
    
    if not is_valid:
        logger.warning(f"Response validation failed: {error_reason}")
        message = get_fallback_response(template_key.split('_')[0])
    
    return {
        'message': message,
        'ui_elements': ui_elements or [],
        'state': state
    }
