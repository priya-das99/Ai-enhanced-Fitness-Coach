# general_workflow.py
# General conversation workflow (catch-all for non-specific chat)
# Integrated with depth guardrails and selective context

from typing import Optional
from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
from .domain.llm.response_phraser import get_response_phraser
from .response_templates import ResponseTemplates
from .conversation_depth_tracker import TopicDetector
from .context_detector import needs_conversation_context
import logging

logger = logging.getLogger(__name__)

class GeneralWorkflow(BaseWorkflow):
    """
    General conversation workflow - handles greetings, questions, and general chat
    
    Integrated Features:
    - Response templates (0 tokens for common questions)
    - Depth tracking (prevent infinite information loops)
    - Selective context (only pass history when needed)
    - Action nudges (guide users to take action after 3 info responses)
    
    Phase 1: LLM-based intent detection
    Phase 2: Depth guardrails & selective context
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="general_chat",
            handled_intents=['general_chat', 'help', 'greeting', 'unknown', 'question', 'off_topic']
        )
        self.response_phraser = get_response_phraser()
        self.templates = ResponseTemplates()
        self.topic_detector = TopicDetector()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """
        Handle general conversation with integrated depth guardrails and selective context.
        
        Flow:
        1. Check for rejections (global tracking)
        2. Check templates (0 tokens) → Return if match
        3. Detect topic (rules, 0 tokens)
        4. Check depth limit for topic
        5. If limit hit → Generate action nudge with buttons
        6. If under limit → Call LLM with selective context
        7. Record informational response
        8. Return response
        """
        logger.info(f"[Phase 2] General workflow handling message: '{message}'")
        
        # ===== GLOBAL REJECTION TRACKING =====
        # Check if user is rejecting suggestions
        if self.is_rejection(message):
            state.track_rejection()
            
            if state.should_stop_suggesting():
                # User rejected 2+ times - stop suggesting
                logger.info(f"User {user_id}: Rejected {state.get_rejection_count()} times - stopping suggestions")
                state.reset_rejection_count()  # Reset for next time
                
                return self._complete_workflow(
                    message="No problem! I'm here if you need anything else. 😊"
                )
        
        # Check if this is a wellness activity button click
        wellness_activities = ['breathing', 'meditation', 'stretching', 'short_walk', 'take_break', 
                              'hydrate', 'walk', 'exercise', 'rest', 'relax']
        message_lower = message.lower().strip()
        
        if message_lower in wellness_activities:
            logger.info(f"Wellness activity selected: {message_lower}")
            # Reset depth for this activity's topic
            topic = state.ACTIVITY_TO_TOPIC.get(message_lower)
            if topic and state.depth_tracker:
                state.depth_tracker.reset_topic(topic)
                logger.info(f"✓ Reset depth for topic: {topic}")
            
            return self._complete_workflow(
                message=f"Great choice! {self._get_activity_encouragement(message_lower)} 😊\n\nHow are you feeling now?",
                ui_elements=['emoji_selector'],
                suggestions=[]  # Clear suggestions to prevent repetition
            )
        
        # Check if this is a simple acknowledgment
        if self._is_simple_acknowledgment(message):
            logger.info("Simple acknowledgment detected - checking context")
            message_lower = message.lower().strip()
            
            # For "thanks" - simple response without LLM
            if message_lower in ['thanks', 'thank you', 'ty']:
                return self._complete_workflow(
                    message="You're welcome! 😊 Want to try a quick wellness activity?",
                    ui_elements=[],  # No activity logging buttons
                    suggestions=self._get_wellness_suggestions(user_id)
                )
            
            # For yes/no/ok - MUST use LLM with context to understand what they're agreeing to
            # This is critical for challenge acceptance, activity confirmation, etc.
            if message_lower in ['yes', 'yeah', 'yep', 'yup', 'no', 'nope', 'nah', 'ok', 'okay']:
                logger.info(f"Acknowledgment '{message_lower}' requires context - passing to LLM")
                # Don't return early - let it fall through to LLM with context
            else:
                # For other simple acknowledgments - check DB-based engagement
                engagement_response = self._get_contextual_engagement(user_id, state)
                
                if engagement_response:
                    return engagement_response
                
                # Fallback: just a thumbs up
                return self._complete_workflow(message="👍")
        
        # Safety check first
        safety_response = self._check_safety(message)
        if safety_response:
            # Return safety response without UI elements (buttons should persist from initialization)
            return self._complete_workflow(
                message=safety_response
            )
        
        # ===== PHASE 2: DEPTH GUARDRAILS & TEMPLATES =====
        
        # 1. Detect topic (0 tokens, rule-based)
        topic = self.topic_detector.detect_topic(message)
        logger.info(f"[Phase 2] Detected topic: {topic}")
        
        # 2. Check templates BEFORE LLM (0 tokens)
        if topic:
            template_response = self.templates.match_template(topic, message)
            if template_response:
                logger.info(f"[Phase 2] ✓ Template match! 0 tokens used")
                # Don't count template responses toward depth
                return self._complete_workflow(
                    message=template_response
                )
        
        # 3. DISABLED: Depth limit check - let conversations flow naturally
        # Users should be able to ask as many questions as they want
        # if topic and state.depth_tracker:
        #     depth_count = state.depth_tracker.get_info_count(topic)
        #     should_nudge = state.depth_tracker.should_nudge_to_action(topic)
        #     
        #     logger.info(f"[Phase 2] Topic '{topic}' depth: {depth_count}/3")
        #     
        #     if should_nudge:
        #         # Check if user is requesting override
        #         if state.depth_tracker.is_override_request(message) and state.depth_tracker.can_override(topic):
        #             logger.info(f"[Phase 2] Override requested and allowed for topic: {topic}")
        #             state.depth_tracker.use_override(topic)
        #             # Continue to LLM response below
        #         else:
        #             # Depth limit reached - nudge to action
        #             logger.info(f"[Phase 2] Depth limit reached for topic: {topic} - nudging to action")
        #             return self._generate_action_nudge(topic, user_id, state)
        
        # 4. Check if this is a casual off-topic mention (not a question/request)
        is_casual_mention = self._is_casual_mention(message)
        
        # 5. Selective context passing (only when needed)
        use_context = needs_conversation_context(message, state)
        logger.info(f"[Phase 2] Context needed: {use_context}")
        
        conversation_context = None
        if use_context:
            conversation_context = self._get_conversation_context(user_id)
        
        # 6. Get user fitness context (recent activities)
        user_context = self._get_user_fitness_context(user_id)
        
        # 7. Call LLM for natural responses with full context
        try:
            response_text = self.response_phraser.phrase_general_response(
                message, 
                conversation_context=conversation_context,
                user_context=user_context
            )
            logger.info(f"[Phase 2] Using LLM-generated response")
        except Exception as e:
            logger.warning(f"LLM response failed, using fallback: {e}")
            response_text = self._get_friendly_fallback(message.lower())
        
        # 7. Record informational response for depth tracking
        if topic and state.depth_tracker:
            # Only count actual informational responses, not questions or confirmations
            if not self._is_question_or_confirmation(response_text):
                state.depth_tracker.record_informational_response(topic)
                new_count = state.depth_tracker.get_info_count(topic)
                logger.info(f"[Phase 2] Recorded info response for '{topic}' - count now: {new_count}/3")
        
        # 7.5. Check if LLM response is about challenges and add challenge buttons
        if self._is_challenge_related_response(response_text, conversation_context):
            logger.info("[Context-Aware] LLM response is challenge-related - adding challenge buttons")
            return self._add_challenge_buttons_to_response(response_text, user_id)
        
        # 8. Decide whether to show action buttons based on context
        should_show_buttons = self._should_show_action_buttons(message, is_casual_mention, state)
        
        # Always just return text response - buttons should persist from initialization
        return self._complete_workflow(
            message=response_text
        )
    
    def _is_casual_mention(self, message: str) -> bool:
        """Check if message is a casual mention vs a question/request"""
        message_lower = message.lower().strip()
        
        # Questions/requests should get buttons
        question_indicators = ['what', 'how', 'can you', 'could you', 'help', 'show', '?']
        if any(indicator in message_lower for indicator in question_indicators):
            return False
        
        # Short acknowledgments are casual (including single word responses)
        casual_phrases = [
            'ok', 'okay', 'sure', 'thanks', 'thank you', 'cool', 'nice', 'great',
            'yes', 'yeah', 'yep', 'yup', 'no', 'nope', 'nah',
            'got it', 'understood', 'alright', 'sounds good'
        ]
        
        # Check if the entire message is just a casual phrase
        if message_lower in casual_phrases:
            return True
        
        # Check if message contains casual phrases and is short
        if len(message.split()) <= 3:
            if any(phrase in message_lower for phrase in casual_phrases):
                return True
        
        # Statements about activities (not logging) are casual
        casual_activity_patterns = [
            'i played', 'i am playing', 'i watched', 'i am watching',
            'i went to', 'i visited', 'i saw', 'i read'
        ]
        if any(pattern in message_lower for pattern in casual_activity_patterns):
            return True
        
        return False
    
    def _is_question_or_confirmation(self, response_text: str) -> bool:
        """
        Check if response is a question or confirmation (not informational).
        These don't count toward depth.
        """
        response_lower = response_text.lower()
        
        # Questions end with ? or contain question words
        if '?' in response_text:
            return True
        
        # Confirmation phrases
        confirmation_phrases = [
            'got it', 'logged', 'saved', 'recorded', 'added',
            'great', 'nice', 'awesome', 'perfect', 'done'
        ]
        
        # If response is very short and contains confirmation
        if len(response_text.split()) <= 5:
            if any(phrase in response_lower for phrase in confirmation_phrases):
                return True
        
        return False
    
    def _generate_action_nudge(self, topic: str, user_id: int, state: WorkflowState) -> WorkflowResponse:
        """
        Generate action nudge when depth limit reached.
        Encourages user to take action instead of just asking questions.
        """
        logger.info(f"[Phase 2] Generating action nudge for topic: {topic}")
        
        # Contextual nudge messages per topic
        nudge_messages = {
            "breathing": "You've asked great questions about breathing! The best way to understand it is by trying. Ready for a quick 3-minute session?",
            "sleep": "Let's move from talking about sleep to tracking it. This will help me give you personalized insights. Want to log last night's sleep?",
            "exercise": "Ready to move from planning to action? Let's start with a quick workout together!",
            "hydration": "Let's track your water intake today so I can help you stay hydrated.",
            "meditation": "Meditation is best experienced, not explained. Ready for a guided session?",
            "nutrition": "Let's log your meals so I can give you personalized nutrition insights.",
            "stress": "I can see stress management is important to you. Let's try a quick stress-relief activity.",
            "energy": "Let's boost that energy! Here are some quick activities that can help."
        }
        
        nudge_message = nudge_messages.get(topic, 
            "Let's put this into action! Here are some options based on your preferences:")
        
        # Get personalized activity suggestions for this topic
        suggestions = self._get_wellness_suggestions(user_id)
        
        # Don't count nudge toward depth
        return self._complete_workflow(
            message=nudge_message,
            ui_elements=['activity_buttons'],
            suggestions=suggestions
        )
    
    def _is_simple_acknowledgment(self, message: str) -> bool:
        """Check if message is a simple acknowledgment that doesn't need a response"""
        message_lower = message.lower().strip()
        
        # List of simple acknowledgments
        simple_acks = [
            'yes', 'yeah', 'yep', 'yup',
            'ok', 'okay', 'k',
            'sure', 'alright',
            'got it', 'understood',
            'thanks', 'thank you', 'ty'
        ]
        
        # Check if the entire message is just an acknowledgment
        return message_lower in simple_acks
    
    def _get_activity_encouragement(self, activity: str) -> str:
        """Get encouragement message for wellness activity"""
        encouragements = {
            'breathing': 'Take a few deep breaths and relax.',
            'meditation': 'Take some time to meditate and clear your mind.',
            'stretching': 'Stretch it out and release that tension.',
            'short_walk': 'A short walk can do wonders for your mood.',
            'take_break': 'Taking a break is important. You deserve it.',
            'hydrate': 'Stay hydrated! Water helps everything.',
            'walk': 'Going for a walk is a great idea.',
            'exercise': 'Movement is medicine. You got this!',
            'rest': 'Rest is productive. Take care of yourself.',
            'relax': 'Relaxation is key. Take your time.'
        }
        return encouragements.get(activity, 'That sounds like a good plan!')
    
    def _should_show_action_buttons(self, message: str, is_casual: bool, state: WorkflowState) -> bool:
        """
        Decide if action buttons should be shown using LLM.
        
        NEW: Uses LLM to understand context and user intent.
        A friend doesn't immediately suggest activities - they listen first.
        """
        message_lower = message.lower()
        
        # Quick checks first (no LLM needed)
        if is_casual:
            return False
        
        if len(message.split()) <= 2:
            return False
        
        # Use LLM to decide if buttons are appropriate
        try:
            from chat_assistant.llm_service import get_llm_service
            llm = get_llm_service()
            
            if not llm.is_available():
                # Fallback to conservative default
                return False
            
            prompt = f"""Should we show activity suggestion buttons to the user?

User message: "{message}"

Context: This is a fitness/wellness app with activities like breathing, meditation, walking, stretching.

Show buttons (return "yes") ONLY if user:
- Explicitly asks for help: "what can I do?", "help me", "suggest something"
- Asks for options/recommendations: "show me activities", "what should I try?"
- Requests suggestions: "give me ideas", "what activities?"

Hide buttons (return "no") if user:
- Expresses feelings: "I am angry", "feeling stressed", "I'm tired"
- Asks informational questions: "is running good?", "how do I do pushups?"
- Shares information: "I just went for a run", "I had a bad day"
- Greets or chats: "hi", "hello", "thanks"

CRITICAL EXAMPLES:
- "What can I do?" = yes (explicitly asking for options)
- "I am angry" = no (expressing emotion, listen first)
- "Is running good?" = no (wants information, not activities)
- "Help me feel better" = yes (requesting help)
- "I'm feeling stressed" = no (expressing feeling)

Return ONLY: yes or no
"""
            
            result = llm.call(prompt, max_tokens=5, temperature=0.1)
            decision = result.strip().lower()
            
            should_show = "yes" in decision
            logger.info(f"[Button Decision] Message: '{message[:50]}...' → {'SHOW' if should_show else 'HIDE'} buttons")
            
            return should_show
            
        except Exception as e:
            logger.warning(f"[Button Decision] LLM failed: {e}, defaulting to NO buttons")
            return False  # Conservative default - don't show buttons
    
    def _check_safety(self, message: str) -> str:
        """Check for inappropriate content and return appropriate response"""
        message_lower = message.lower()
        
        # Check for threats/violence
        violence_indicators = [
            'kill', 'murder', 'hurt', 'harm', 'attack', 'die', 'death',
            'shoot', 'stab', 'punch', 'hit', 'beat'
        ]
        
        if any(word in message_lower for word in violence_indicators):
            return ("I'm here to support your wellness, not to engage with harmful content. "
                   "If you're experiencing thoughts of harming yourself or others, please reach out "
                   "to a mental health professional or crisis helpline. 🆘\n\n"
                   "For wellness support, I can help you track your mood and activities. "
                   "How can I assist you today?")
        
        # Check for abusive/profane language
        profanity_indicators = [
            'fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard',
            'stupid', 'idiot', 'dumb', 'hate you', 'suck', 'crap'
        ]
        
        if any(word in message_lower for word in profanity_indicators):
            return ("I understand you might be frustrated. 😔 I'm here to help you with your "
                   "wellness journey - tracking mood, activities, and challenges. "
                   "Let's focus on something positive! How can I help you today?")
        
        # Check for completely off-topic queries (questions/requests, not casual mentions)
        off_topic_indicators = [
            'weather', 'news', 'politics', 'sports', 'movie', 'game',
            'recipe', 'cooking', 'travel', 'shopping', 'stock', 'crypto',
            'bitcoin', 'investment', 'dating', 'relationship advice',
            'joke', 'funny', 'story', 'time', 'date', 'clock'
        ]
        
        # Only trigger if it's a question or request (not just mentioning)
        is_question = any(word in message_lower for word in ['what', 'how', 'when', 'where', 'why', 'can you', 'tell me', '?'])
        
        if is_question and any(word in message_lower for word in off_topic_indicators):
            return ("I appreciate your question! However, I'm specifically designed to help "
                   "with your wellness and fitness journey. 🏃‍♀️💪\n\n"
                   "I can help you:\n"
                   "• Track your mood and emotions\n"
                   "• Log activities (water, sleep, exercise)\n"
                   "• Monitor your wellness challenges\n"
                   "• Get personalized wellness suggestions\n\n"
                   "What would you like to focus on?")
        
        # If just mentioning (not asking), return None to let LLM handle naturally
        if any(word in message_lower for word in off_topic_indicators):
            return None  # Let LLM acknowledge naturally without safety message
        
        # Check for spam/gibberish
        # Criteria: Very long, or very short with repeated characters, or too many spaces
        if len(message) > 500:
            return ("That's quite a long message! 😅 I'm here to help with "
                   "wellness tracking. Try asking about mood logging, activity tracking, "
                   "or your challenges.")
        
        # Check for repeated characters (gibberish)
        if len(message) < 50:  # Only check short messages
            # Count repeated characters
            repeated_count = 0
            for i in range(len(message) - 1):
                if message[i] == message[i+1]:
                    repeated_count += 1
            
            # If more than 40% of characters are repeated
            if len(message) > 3 and repeated_count / len(message) > 0.4:
                return ("I'm having trouble understanding that. 🤔 I'm here to help with "
                       "wellness tracking! Try asking about mood logging, activity tracking, "
                       "or your challenges.")
        
        # Check for excessive spacing (another gibberish indicator)
        space_count = message.count(' ')
        if len(message) > 5 and space_count / len(message) > 0.3:
            return ("I'm having trouble understanding that. 🤔 I'm here to help with "
                   "wellness tracking! Try asking about mood logging, activity tracking, "
                   "or your challenges.")
        
        return None  # No safety issues
    
    def _get_personalized_actions(self, user_id: int) -> list:
        """Get personalized action buttons based on user's past interactions"""
        try:
            from app.services.behavior_scorer import get_behavior_scorer
            from chat_assistant.smart_suggestions import WELLNESS_ACTIVITIES
            
            scorer = get_behavior_scorer()
            metrics = scorer.get_user_metrics(user_id)
            
            actions = []
            
            # Suggest based on what user does most
            if metrics.get('water_frequency', 0) > 0.5:
                actions.append({
                    'id': 'log_water',
                    'key': 'log_water',
                    'name': '💧 Log Water',
                    'type': 'activity',
                    'description': 'Track your water intake',
                    'duration': 'Quick'
                })
            
            if metrics.get('exercise_frequency', 0) > 0.5:
                actions.append({
                    'id': 'log_exercise',
                    'key': 'log_exercise',
                    'name': '🏃 Log Exercise',
                    'type': 'activity',
                    'description': 'Record your workout',
                    'duration': 'Quick'
                })
            
            if metrics.get('mood_frequency', 0) > 0.5:
                actions.append({
                    'id': 'log_mood',
                    'key': 'log_mood',
                    'name': '😊 Log Mood',
                    'type': 'mood',
                    'description': 'How are you feeling?',
                    'duration': 'Quick'
                })
            
            # Always include challenges
            actions.append({
                'id': 'view_challenges',
                'key': 'view_challenges',
                'name': '🎯 View Challenges',
                'type': 'challenges',
                'description': 'Check your progress',
                'duration': 'Quick'
            })
            
            # If no personalized actions, use defaults
            if len(actions) == 1:  # Only challenges
                actions = [
                    {
                        'id': 'log_mood',
                        'key': 'log_mood',
                        'name': '😊 Log Mood',
                        'type': 'mood',
                        'description': 'How are you feeling?',
                        'duration': 'Quick'
                    },
                    {
                        'id': 'log_water',
                        'key': 'log_water',
                        'name': '💧 Log Water',
                        'type': 'activity',
                        'description': 'Track your water intake',
                        'duration': 'Quick'
                    },
                    {
                        'id': 'log_exercise',
                        'key': 'log_exercise',
                        'name': '🏃 Log Exercise',
                        'type': 'activity',
                        'description': 'Record your workout',
                        'duration': 'Quick'
                    },
                    {
                        'id': 'view_challenges',
                        'key': 'view_challenges',
                        'name': '🎯 View Challenges',
                        'type': 'challenges',
                        'description': 'Check your progress',
                        'duration': 'Quick'
                    }
                ]
            
            return actions[:4]  # Max 4 buttons
            
        except Exception as e:
            logger.warning(f"Failed to get personalized actions: {e}")
            # Default actions
            return [
                {
                    'id': 'log_mood',
                    'key': 'log_mood',
                    'name': '😊 Log Mood',
                    'type': 'mood',
                    'description': 'How are you feeling?',
                    'duration': 'Quick'
                },
                {
                    'id': 'log_water',
                    'key': 'log_water',
                    'name': '💧 Log Water',
                    'type': 'activity',
                    'description': 'Track your water intake',
                    'duration': 'Quick'
                },
                {
                    'id': 'view_challenges',
                    'key': 'view_challenges',
                    'name': '🎯 View Challenges',
                    'type': 'challenges',
                    'description': 'Check your progress',
                    'duration': 'Quick'
                }
            ]
    
    def _get_wellness_suggestions(self, user_id: int) -> list:
        """Get personalized wellness activity suggestions for engagement"""
        try:
            from chat_assistant.smart_suggestions import get_smart_suggestions
            from chat_assistant.context_builder_simple import build_context
            
            # Build user context
            context = build_context(user_id)
            
            # Get suggestions for general wellness (no specific mood)
            # This will use the smart_suggestions system with personalization
            suggestions = get_smart_suggestions(
                mood_emoji="😊",
                reason="general",
                context=context,
                count=4
            )
            
            logger.info(f"Got {len(suggestions)} wellness suggestions from smart_suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get wellness suggestions from smart_suggestions: {e}")
            # If smart_suggestions fails completely, return empty list
            # This will cause no buttons to show rather than showing hardcoded ones
            return []
    
    def _get_conversation_context(self, user_id: int) -> str:
        """Get recent conversation context for better responses"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from app.repositories.chat_repository import ChatRepository
            
            chat_repo = ChatRepository()
            return chat_repo.get_conversation_context(user_id, max_messages=6)
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
            return ""
    
    def _get_user_fitness_context(self, user_id: int) -> dict:
        """Get user's recent fitness activities for context-aware responses"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from app.repositories.activity_repository import ActivityRepository
            
            activity_repo = ActivityRepository()
            recent_activities = activity_repo.get_recent_activities(user_id, limit=5)
            
            return {
                'recent_activities': [
                    {
                        'activity_type': activity.get('activity_type', 'activity'),
                        'timestamp': activity.get('timestamp'),
                        'duration': activity.get('duration_minutes')
                    }
                    for activity in recent_activities
                ]
            }
        except Exception as e:
            logger.warning(f"Failed to get user fitness context: {e}")
            return {'recent_activities': []}
    
    def _get_friendly_fallback(self, message_lower: str) -> str:
        """Get a friendly fallback response based on message content"""
        import random
        
        # Check for greetings
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            greetings = [
                "Hey there! 👋 I'm your fitness buddy. What's your goal today?",
                "Hello! 😊 Ready to crush your fitness goals? What can I help with?",
                "Hi! 🌟 I'm here to help with workouts, exercises, and tracking. What's up?",
            ]
            return random.choice(greetings)
        
        # Check for fitness questions
        if any(word in message_lower for word in ['exercise', 'workout', 'fitness', 'train', 'gym']):
            fitness_responses = [
                "I love talking fitness! What specific exercise or workout are you curious about?",
                "Great question! Tell me more about what you're trying to achieve.",
                "I can help with that! What's your fitness goal - strength, cardio, or flexibility?",
            ]
            return random.choice(fitness_responses)
        
        # Default friendly response
        default_responses = [
            "I'm here to help with your fitness journey! Ask me about exercises, workouts, or tracking activities.",
            "Not sure I caught that, but I'm great at fitness advice! What would you like to know?",
            "Let's talk fitness! I can help with workouts, exercises, nutrition, or tracking your progress.",
        ]
        return random.choice(default_responses)
    
    def _get_contextual_engagement(self, user_id: int, state: WorkflowState) -> Optional[WorkflowResponse]:
        """
        Get contextual engagement response based on user's recent activity and challenges.
        Returns None if no engagement opportunity found.
        """
        try:
            from db import get_connection
            
            # Convert user_id to int if it's a string
            user_id_int = int(user_id) if isinstance(user_id, str) else user_id
            
            # Query challenges directly from database (works with both test and production DB)
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get active challenges
            cursor.execute('''
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.challenge_type,
                    c.target_value,
                    c.target_unit,
                    uc.progress,
                    uc.status
                FROM challenges c
                JOIN user_challenges uc ON c.id = uc.challenge_id
                WHERE uc.user_id = ? AND uc.status = 'active'
                ORDER BY uc.joined_at DESC
            ''', (user_id_int,))
            
            challenge_rows = cursor.fetchall()
            active_challenges = []
            for row in challenge_rows:
                active_challenges.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'challenge_type': row[3],
                    'target_value': row[4],
                    'target_unit': row[5],
                    'progress': row[6],
                    'status': row[7]
                })
            
            logger.info(f"[Engagement] User {user_id_int} has {len(active_challenges)} active challenges")
            
            # Check recent activity from database (last 5 minutes)
            cursor.execute('''
                SELECT activity_type, value, unit
                FROM health_activities
                WHERE user_id = ?
                AND timestamp >= datetime('now', '-5 minutes')
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id_int,))
            recent_activity = cursor.fetchone()
            conn.close()
            
            logger.info(f"[Engagement] Recent activity found: {recent_activity is not None}")
            
            # If user has active challenges AND just logged an activity, provide contextual engagement
            if active_challenges and recent_activity:
                challenge = active_challenges[0]  # Focus on first active challenge
                progress = challenge.get('progress', 0)
                title = challenge.get('title', 'your challenge')
                activity_type = recent_activity[0]
                value = recent_activity[1]
                unit = recent_activity[2]
                
                # Format value nicely (remove .0 for whole numbers)
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                
                logger.info(f"[Engagement] Providing challenge + activity engagement for '{title}'")
                
                # Create contextual message based on challenge and activity
                if activity_type in title.lower() or challenge.get('challenge_type') == activity_type:
                    # Activity is related to challenge
                    if progress >= 75:
                        message = f"Awesome! That brings you to {progress:.0f}% on '{title}'! 🔥 You're almost there!"
                    elif progress >= 50:
                        message = f"Great! You're now at {progress:.0f}% on '{title}'! 💪 Keep it up!"
                    elif progress >= 25:
                        message = f"Nice! You're at {progress:.0f}% on '{title}'! 👍 Making progress!"
                    else:
                        message = f"Good start! You're at {progress:.0f}% on '{title}'! 🎯 Every step counts!"
                else:
                    # Activity not related to challenge, but still motivate
                    message = f"Great job logging that! 👍 Don't forget about '{title}' - you're at {progress:.0f}%!"
                
                # Get wellness suggestions but DON'T show activity logging buttons
                # (User just logged an activity, they know where the buttons are!)
                suggestions = self._get_wellness_suggestions(user_id_int)
                
                return self._complete_workflow(
                    message=message,
                    ui_elements=[],  # No buttons - keep chat clean
                    suggestions=suggestions
                )
            
            # If user has active challenges (but no recent activity), still motivate
            if active_challenges:
                challenge = active_challenges[0]
                progress = challenge.get('progress', 0)
                title = challenge.get('title', 'your challenge')
                
                logger.info(f"[Engagement] Providing challenge-only engagement for '{title}'")
                
                if progress >= 75:
                    message = f"You're crushing '{title}'! 🔥 At {progress:.0f}% - keep going!"
                elif progress >= 50:
                    message = f"Halfway through '{title}'! 💪 You're at {progress:.0f}%!"
                elif progress >= 25:
                    message = f"Nice progress on '{title}'! 👍 You're at {progress:.0f}%!"
                else:
                    message = f"You're working on '{title}'! 🎯 Currently at {progress:.0f}%!"
                
                suggestions = self._get_wellness_suggestions(user_id_int)
                
                return self._complete_workflow(
                    message=message,
                    ui_elements=[],  # No buttons - keep chat clean
                    suggestions=suggestions
                )
            
            # If user recently logged an activity, suggest related activities
            if recent_activity:
                activity_type = recent_activity[0]
                value = recent_activity[1]
                unit = recent_activity[2]
                
                # Suggest complementary activities
                complementary_messages = {
                    'water': "Great hydration! 💧 How about some movement to go with it?",
                    'exercise': "Nice workout! 💪 Don't forget to hydrate!",
                    'sleep': "Good rest is key! 😴 How about tracking your water intake today?",
                    'weight': "Tracking progress! ⚖️ Keep up with your wellness routine!"
                }
                
                message = complementary_messages.get(activity_type, "Keep up the great work! 🌟")
                suggestions = self._get_wellness_suggestions(user_id_int)
                
                return self._complete_workflow(
                    message=message,
                    ui_elements=['activity_buttons'] if suggestions else [],
                    suggestions=suggestions
                )
            
            # Check if it's a good time to suggest activities (randomly, 30% chance)
            import random
            if random.random() < 0.3:
                messages = [
                    "Want to try a quick wellness activity? 🌟",
                    "How about doing something good for yourself? 😊",
                    "Ready for a wellness boost? 💪"
                ]
                
                suggestions = self._get_wellness_suggestions(user_id_int)
                
                if suggestions:
                    return self._complete_workflow(
                        message=random.choice(messages),
                        ui_elements=['activity_buttons'],
                        suggestions=suggestions
                    )
            
            # No engagement opportunity found
            return None
            
        except Exception as e:
            logger.error(f"Failed to get contextual engagement: {e}", exc_info=True)
            return None
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """
        General workflow doesn't have multi-step flow.
        This should not be called, but handle it anyway.
        """
        return self.start(message, state, user_id)

    def _is_challenge_related_response(self, response_text: str, conversation_context: str = None) -> bool:
        """
        Check if LLM response is about challenges based on keywords and context.
        
        Returns True if response mentions challenges and user likely wants to join/view them.
        """
        response_lower = response_text.lower()
        
        # Challenge-related keywords in response
        challenge_keywords = ['challenge', 'join', 'take on', 'participate', 'available']
        
        # Check if response mentions challenges
        has_challenge_keywords = any(keyword in response_lower for keyword in challenge_keywords)
        
        if not has_challenge_keywords:
            return False
        
        # Check conversation context for challenge-related discussion
        if conversation_context:
            context_lower = conversation_context.lower()
            context_has_challenges = 'challenge' in context_lower
            
            # If both response and context mention challenges, it's challenge-related
            if context_has_challenges:
                logger.info("[Context-Aware] Detected challenge discussion in context + response")
                return True
        
        return False
    
    def _add_challenge_buttons_to_response(self, response_text: str, user_id: int) -> WorkflowResponse:
        """
        Add challenge-related buttons to LLM response.
        
        Fetches available challenges and adds JOIN buttons.
        """
        try:
            from app.services.challenge_service import ChallengeService
            challenge_service = ChallengeService()
            
            summary = challenge_service.get_challenges_summary(user_id)
            available = summary['available_challenges']
            
            buttons = []
            
            # Add JOIN buttons for available challenges (max 3)
            for challenge in available[:3]:
                buttons.append({
                    'id': f'join_challenge_{challenge["id"]}',
                    'name': f'Join: {challenge["title"][:30]}...' if len(challenge["title"]) > 30 else f'Join: {challenge["title"]}',
                    'user_message': f'Join {challenge["title"]}'
                })
            
            logger.info(f"[Context-Aware] Added {len(buttons)} challenge JOIN buttons to response")
            
            return self._complete_workflow(
                message=response_text,
                buttons=buttons
            )
            
        except Exception as e:
            logger.error(f"Failed to add challenge buttons: {e}")
            # Fallback: return response without buttons
            return self._complete_workflow(message=response_text)
