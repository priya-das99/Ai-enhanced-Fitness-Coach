import logging

from .workflow_registry import get_registry
from .llm_service import get_llm_service
from .response_validator import validate_response

logger = logging.getLogger(__name__)

# Maps raw button/shorthand names → canonical log_ format
ACTIVITY_BUTTON_MAP = {
    "water": "log_water",
    "water_intake": "log_water",
    "drink_water": "log_water",
    "mood": "log_mood",
    "sleep": "log_sleep",
    "rest": "log_sleep",
    "sleep_log": "log_sleep",
    "exercise": "log_exercise",
    "workout": "log_exercise",
    "weight": "log_weight",
    "steps": "log_steps",
    "calories": "log_calories",
    "meal": "log_meal",
}

# Mood keywords used to detect mood expressions in free text
MOOD_KEYWORDS = [
    "stressed", "anxious", "worried", "nervous", "overwhelmed",
    "happy", "sad", "angry", "frustrated", "upset", "down",
    "excited", "tired", "exhausted", "energetic", "calm",
    "depressed", "joyful", "content", "lonely", "scared",
    "afraid", "confident", "proud", "ashamed", "guilty",
    "relieved", "hopeful", "hopeless", "bored", "motivated",
    "unmotivated", "inspired", "discouraged", "peaceful",
    "restless", "comfortable", "uncomfortable", "terrible", 
    "awful", "horrible", "great", "amazing", "fantastic", 
    "wonderful", "excellent", "good", "bad", "sick", "ill", 
    "unwell", "well"
]

MOOD_PHRASES = [
    "i feel", "i'm feeling", "i am", "i'm",
    "feeling", "not feeling", "been feeling",
]

# Phrases that indicate "log mood again" even mid-conversation
LOG_AGAIN_PHRASES = [
    "log again", "log my mood again", "log mood again",
    "log it again", "track again", "log another mood",
    "want to log again", "want to log my mood",
]

# These words in a "log again" message mean it's NOT about mood
LOG_AGAIN_EXCLUSIONS = ["water", "exercise", "sleep", "weight", "meal", "workout"]


class ChatEngineWorkflow:
    """
    Chat engine with a single, linear routing chain.

    Routing order (first match wins):
    1.  Guardrails  – block unsafe messages immediately
    2.  Button-click routing  – log_*, mapped shortcuts (PRIORITY - before context router)
    3.  Context Router  – handles workflow switching / activity detection
    4.  Universal Context Handler  – follow-ups to recent activity (idle only)
    5.  Continue active workflow  – pass message straight to the running workflow
    6.  "Log again" shortcut  – route to mood workflow
    7.  Mood expression detection  – free-text mood → mood workflow
    8.  External / activity-start buttons  – start_content_*, start_*
    9.  Mood emoji direct logging
    10. LLM intent detection  – general fallback
    """

    def __init__(self):
        self.registry = get_registry()
        self.llm_service = get_llm_service()
        self.enable_multi_intent = True
        self.enable_validation = True
        self.enable_events = True
        self.enable_intent_gate = True  # NEW: Two-stage intent classification

    # ------------------------------------------------------------------ #
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------ #

    def process_message(self, user_id: str, message: str) -> dict:
        logger.info(f"[Engine] user={user_id} message='{message}'")

        try:
            # --- 1. GUARDRAILS ---
            from .guardrails import apply_guardrails

            allowed, response_override, metadata = apply_guardrails(message)

            if not allowed:
                logger.warning(
                    f"[Guardrails] blocked user={user_id} "
                    f"type={metadata.get('violation_type')}"
                )
                return {
                    "message": response_override,
                    "ui_elements": [],
                    "state": "idle",
                    "completed": True,
                    "guardrail_triggered": True,
                    "violation_type": metadata.get("violation_type"),
                }

            from .unified_state import get_workflow_state

            uid = int(user_id)
            workflow_state = get_workflow_state(uid)

            logger.info(
                f"[Engine] state={workflow_state.state.value} "
                f"active_workflow={workflow_state.active_workflow}"
            )

            # Load DB history on first message after restart
            self._maybe_load_db_history(user_id, workflow_state)

            # Store user turn
            workflow_state.add_message("user", message)

            return self._route(uid, message, workflow_state)

        except Exception:
            logger.exception(f"[Engine] Critical error for user={user_id}")
            return {
                "message": "I'm having trouble right now. Please try again.",
                "ui_elements": [],
                "state": "idle",
                "completed": True,
                "error_recovery": True,
            }

    # ------------------------------------------------------------------ #
    # INTENT GATE (Two-Stage Classification)
    # ------------------------------------------------------------------ #

    def _classify_intent_type(self, message: str) -> str:
        """
        Stage 1: Classify if message is a command or conversation.
        
        This is the first gate that determines if the user wants to:
        - command: Perform an action (log, track, start, show)
        - conversation: Chat, ask questions, express feelings
        
        Returns: 'command' or 'conversation'
        """
        # Skip for buttons (always commands)
        msg_lower = message.lower().strip()
        if msg_lower.startswith("log_") or msg_lower.startswith("start_"):
            return "command"
        
        # Quick keyword check for obvious commands (faster than LLM)
        command_keywords = [
            'log', 'track', 'record', 'want to log', 'want log',
            'want to track', 'want track', 'i want to log', 'i want log',
            'suggest', 'recommend', 'show me', 'give me', 'help me',
            'what can i do', 'show my', 'view my',
            # Activity summary queries (viewing logged data)
            'what did i', 'how much did i', 'how many did i', 'did i',
            'have i logged', 'my activities', 'what have i',
            'how much water did', 'how many hours did', 'what was my',
            'my intake', 'my log', 'am i on track', 'how close am i',
            'did i reach', 'am i meeting', 'my progress', 'my status'
        ]
        
        # Check for activity statements with quantities (should be logged)
        activity_patterns = [
            # Exercise patterns
            r'i (played|did|went|ran|walked|exercised|worked out)',
            r'i (swam|cycled|biked|jogged|lifted|stretched)',
            r'played \w+ for \d+',
            r'exercised for \d+',
            r'worked out for \d+',
            r'ran for \d+',
            r'walked for \d+',
            # Consumption patterns  
            r'i (drank|ate|had|consumed) \d+',
            r'drank \d+ (glasses|cups|bottles)',
            r'ate \d+ (servings|meals|portions)',
            r'had \d+ (glasses|cups|servings)',
            # Sleep patterns
            r'i slept (for )?\d+',
            r'slept \d+ hours',
            r'got \d+ hours',
            # General activity with duration/quantity
            r'for \d+ (minutes|hours|mins|hrs)',
            r'\d+ (glasses|servings|hours|minutes|steps|calories)',
        ]
        
        import re
        for pattern in activity_patterns:
            if re.search(pattern, msg_lower):
                logger.info(f"[Intent Gate] Activity pattern match: '{pattern}' → command")
                return "command"
        
        for keyword in command_keywords:
            if keyword in msg_lower:
                logger.info(f"[Intent Gate] Quick match: '{keyword}' → command")
                return "command"
        
        # Use LLM for classification
        try:
            if not self.llm_service.is_available():
                logger.warning("[Intent Gate] LLM unavailable, defaulting to conversation")
                return "conversation"
            
            prompt = f"""Classify this user message as either 'command' or 'conversation'.

User message: "{message}"

COMMAND means the user wants to:
1. Log/track something explicitly ("log mood", "track water", "log workout", "I want to log exercise", "I want log weight")
2. Start an activity ("start challenge", "begin meditation")
3. Request help/suggestions/recommendations ("what can I do?", "help me", "suggest something", "show me options")
4. View data ("show my activities", "view my progress", "how much water did I drink", "did I reach my goal")
5. Check status/progress ("am I on track", "how close am I", "did I exercise today", "what did I do today")
6. Report activities with quantities/durations ("I played badminton for 30 minutes", "I drank 2 glasses of water", "I slept for 7 hours")

CONVERSATION means the user is:
1. Expressing feelings/emotions ("I am angry", "feeling stressed", "I'm tired")
2. Asking informational questions ("is running good?", "how do I do pushups?")
3. Greeting or chatting ("hi", "hello", "how are you?")
4. Sharing information without quantities ("I just went for a run", "I had a bad day")

CRITICAL EXAMPLES:
- "I want to log exercise" = command (wants to log activity)
- "I want log weight" = command (wants to log activity)
- "I want to track my mood" = command (wants to log activity)
- "log mood" = command (explicit logging)
- "I played badminton for 30 minutes" = command (activity with duration - should be logged)
- "I drank 2 glasses of water" = command (activity with quantity - should be logged)
- "I slept for 7 hours" = command (activity with duration - should be logged)
- "I exercised for 45 minutes" = command (activity with duration - should be logged)
- "I ate 3 servings" = command (activity with quantity - should be logged)
- "How much water did I drink today?" = command (viewing logged data)
- "Did I reach my water goal?" = command (checking progress)
- "What did I do today?" = command (viewing activities)
- "Am I on track?" = command (checking status)
- "I am angry" = conversation (expressing emotion)
- "What can I do?" = command (requesting options/help)
- "Is running good?" = conversation (asking question)
- "I'm feeling stressed" = conversation (expressing feeling)
- "I just went for a run" = conversation (sharing without quantity/duration)

IMPORTANT: 
- Any message with "log", "track", "record" + activity name = COMMAND
- Any message with "I want to log/track/record" = COMMAND
- Any message with "suggest", "recommend", "show me" = COMMAND
- Any message asking about logged data ("how much did I", "did I reach", "what did I do") = COMMAND
- Any message reporting activities with specific quantities/durations = COMMAND
- Activities with numbers/measurements ("30 minutes", "2 glasses", "7 hours") = COMMAND

Return ONLY the word: command or conversation
"""
            
            result = self.llm_service.call(prompt, max_tokens=10, temperature=0.1)
            classification = result.strip().lower()
            
            logger.info(f"[Intent Gate] Message: '{message[:50]}...' → {classification}")
            
            if "command" in classification:
                return "command"
            else:
                return "conversation"
                
        except Exception as e:
            logger.warning(f"[Intent Gate] Classification failed: {e}, defaulting to conversation")
            return "conversation"  # Safe default

    # ------------------------------------------------------------------ #
    # ROUTING CHAIN
    # ------------------------------------------------------------------ #

    def _route(self, user_id: int, message: str, workflow_state) -> dict:
        try:
            msg_raw = message.strip()
            msg_lower = msg_raw.lower()
            msg_slug = msg_lower.replace(" ", "_")   # "log water" → "log_water"

            # Normalise shorthand button names (e.g. "water" → "log_water")
            if msg_slug in ACTIVITY_BUTTON_MAP:
                msg_slug = ACTIVITY_BUTTON_MAP[msg_slug]
                msg_lower = msg_slug
                logger.info(f"[Route] Mapped button to '{msg_slug}'")

            # Classify the incoming message once so every branch can read it
            # CRITICAL FIX: Only treat simple patterns as buttons, not complex natural language
            # "log_water" = button, "log_my_weight_now" = natural language
            simple_log_buttons = [
                'log_water', 'log_sleep', 'log_weight', 'log_exercise', 'log_mood',
                'log_meal', 'log_steps', 'log_calories'
            ]
            is_log_btn = msg_slug in simple_log_buttons or (
                msg_slug.startswith("log_") and len(msg_slug.split("_")) <= 2
            )
            is_start_content_btn = msg_slug.startswith("start_content_")
            is_start_btn = msg_slug.startswith("start_") and not is_start_content_btn

            # ========================================================== #
            # 1. INTENT GATE (Two-Stage Classification)
            # ========================================================== #
            # Skip intent gate if:
            # - It's a button click (always a command)
            # - Intent gate is disabled
            # - Workflow is waiting for custom input (date, time, duration, etc.)
            # - Workflow is waiting for clarification (asking for specific value)
            # - It's a mood expression (should be handled by mood workflow)
            # 
            # Check if workflow is awaiting custom input or clarification
            workflow_data = workflow_state.workflow_data or {}
            is_awaiting_input = any(key.startswith('awaiting_') for key in workflow_data.keys())
            
            # Check if this is a mood expression (should bypass Intent Gate)
            is_mood_expression = self._is_mood_expression(msg_lower)
            if is_mood_expression:
                logger.info(f"[Route] Mood expression detected: '{message}' - bypassing Intent Gate")
            
            # Check if this is a summary query (should complete active workflow and start fresh)
            summary_query_keywords = [
                'what did i', 'how much did i', 'how many did i', 'did i',
                'have i logged', 'my activities', 'what have i',
                'how much water did', 'how many hours did', 'what was my',
                'my intake', 'my log', 'am i on track', 'how close am i',
                'did i reach', 'am i meeting', 'show my water', 'show my sleep',
                'what have i logged', 'show my activities',
                # Additional logging query keywords from Test 3
                'what did i track', 'show me what i\'ve logged', 'what activities did i log',
                'did i log', 'have i logged', 'did i track', 'show my logging history',
                'what have i been logging', 'show my activity history'
            ]
            is_summary_query = any(keyword in msg_lower for keyword in summary_query_keywords)
            
            # If it's a summary query and there's an active NON-LOGGING workflow, complete it first
            # Logging workflows (activity_logging, exercise_logging, mood_logging) should NOT be completed
            # because the user might be providing a follow-up answer like "5 glasses"
            # But activity_query, challenges, etc. should be completed so summary can route properly
            logging_workflows = ['activity_logging', 'exercise_logging', 'mood_logging']
            is_logging_workflow = workflow_state.active_workflow in logging_workflows
            
            if is_summary_query and workflow_state.active_workflow and not is_logging_workflow:
                logger.info(f"[Intent Gate] Summary query detected, completing non-logging workflow '{workflow_state.active_workflow}'")
                workflow_state.complete_workflow()
            
            # For logging workflows with summary queries, we'll let the Intent Gate run
            # so it can properly detect if this is a new intent or a clarification
            # The Intent Gate will classify "5 glasses" as conversation (clarification)
            # but "How much water did I drink?" as command (new intent)
            
            # Also check if workflow is in CLARIFICATION_PENDING state (asking for specific value)
            # OR if there's any active workflow (let workflow handle its own inputs)
            # BUT: Don't skip for summary queries (they should always get fresh routing)
            is_awaiting_clarification = (
                workflow_state.state.value == 'clarification_pending' or
                (workflow_state.active_workflow is not None and not is_summary_query)  # Skip Intent Gate for active workflows UNLESS it's a summary query
            )
            
            if (self.enable_intent_gate and 
                not is_log_btn and 
                not is_start_btn and
                not is_start_content_btn and
                not is_awaiting_input and
                not is_mood_expression and  # Skip Intent Gate for mood expressions
                not is_awaiting_clarification):  # CRITICAL: Skip Intent Gate if workflow is waiting for clarification
                
                intent_type = self._classify_intent_type(message)
                
                if intent_type == "conversation":
                    # If there's an active workflow but user is having conversation,
                    # complete the workflow and start fresh
                    if workflow_state.active_workflow:
                        logger.info(f"[Intent Gate] User switched to conversation, completing workflow '{workflow_state.active_workflow}'")
                        workflow_state.complete_workflow()
                    
                    # Route directly to general chat, skip all other routing
                    logger.info("[Intent Gate] ✓ Classified as CONVERSATION → General Chat")
                    workflow = self.registry.get_workflow_for_intent("general_chat")
                    
                    if workflow:
                        response = workflow.start(message, workflow_state, user_id)
                        workflow_state.add_message("assistant", response.message)
                        return self._convert_response(response, workflow_state, "general_chat", user_id)
                    else:
                        logger.error("[Intent Gate] General chat workflow not found! This should never happen.")
                        # CRITICAL: Don't fall through - return error response
                        return {
                            "message": "I'm here to help! How can I assist you today?",
                            "ui_elements": [],
                            "completed": True,
                            "state": "idle",
                        }
                else:
                    # It's a command, continue to existing routing
                    logger.info("[Intent Gate] ✓ Classified as COMMAND → Continue routing")
            elif is_awaiting_input:
                logger.info(f"[Intent Gate] ⏭️ Skipping Intent Gate - workflow awaiting custom input")
            elif is_mood_expression:
                logger.info(f"[Intent Gate] ⏭️ Skipping Intent Gate - mood expression detected: '{message}'")
            elif is_awaiting_clarification:
                logger.info(f"[Intent Gate] ⏭️ Skipping Intent Gate - workflow awaiting clarification")
            else:
                logger.info(f"[Intent Gate] ⏭️ Skipping Intent Gate - other reason")
            
            # ========================================================== #
            # 2. BUTTON ROUTING (PRIORITY - before context router)
            # ========================================================== #
            # Handle button clicks FIRST to avoid context router interference
            if is_log_btn:
                logger.info(f"🔘 [BUTTON ROUTING] Detected log button: '{msg_slug}'")
                
                # Check if this is a workflow continuation button (log_activity_category, log_activity_select, etc.)
                is_workflow_continuation = any(msg_slug.startswith(prefix) for prefix in [
                    'log_activity_category:',
                    'log_activity_select:',
                    'log_activity_date:',
                    'log_activity_time:',
                    'log_activity_duration:'
                ])
                
                # If it's a workflow continuation and we have an active workflow, continue it
                if is_workflow_continuation and workflow_state.active_workflow == "exercise_logging":
                    logger.info(f"🔄 [BUTTON ROUTING] Continuing exercise_logging workflow with: '{msg_slug}'")
                    workflow = self.registry.get_workflow("exercise_logging")
                    if workflow:
                        response = workflow.process(msg_raw, workflow_state, user_id)
                        workflow_state.add_message("assistant", response.message)
                        return self._convert_response(response, workflow_state, "exercise_logging", user_id)
                
                # CRITICAL FIX: If a workflow is active, complete it before starting a new one
                if workflow_state.active_workflow:
                    logger.info(f"🔄 [BUTTON ROUTING] Completing active workflow '{workflow_state.active_workflow}' before starting new button action")
                    workflow_state.complete_workflow()
                
                # log_mood is special – goes to mood workflow
                if msg_slug == "log_mood":
                    logger.info("[Route] log_mood button → mood workflow")
                    return self._start_workflow("mood_logging", "Log Mood", workflow_state, user_id)
                
                # log_exercise is special – goes to exercise_logging workflow
                if msg_slug == "log_exercise":
                    logger.info("[Route] log_exercise button → exercise_logging workflow")
                    return self._start_workflow("log_exercise", msg_slug, workflow_state, user_id)

                # All other log_* → activity workflow
                logger.info(f"[Route] log button '{msg_slug}' → activity workflow")
                return self._start_workflow("activity_logging", msg_slug, workflow_state, user_id)

            # ---------------------------------------------------------- #
            # 3. CONTEXT ROUTER
            # ---------------------------------------------------------- #
            try:
                from .context_router import ContextRouter

                routed = ContextRouter().route_message(message, workflow_state, user_id)

                if routed:
                    logger.info("[Route] Context router handled message")
                    workflow_state.update_activity_time()
                    workflow_state.add_message("assistant", routed.message)
                    return self._convert_response(routed, workflow_state, "context_router", user_id)

            except Exception:
                logger.warning("[Route] Context router error – continuing", exc_info=True)

            # ---------------------------------------------------------- #
            # 4. UNIVERSAL CONTEXT HANDLER (idle only)
            # ---------------------------------------------------------- #
            if workflow_state.is_idle():
                try:
                    from .universal_context_handler import get_universal_context_handler

                    handler = get_universal_context_handler()

                    if handler.can_handle_followup(message, workflow_state):
                        response = handler.handle_followup(message, workflow_state, user_id)

                        if response:
                            logger.info("[Route] Universal context handled follow-up")
                            workflow_state.add_message("assistant", response.message)
                            return self._convert_response(
                                response, workflow_state, "universal_context", user_id
                            )

                except Exception:
                    logger.warning("[Route] Universal context error – continuing", exc_info=True)

            # ---------------------------------------------------------- #
            # 5. CONTINUE ACTIVE WORKFLOW
            # ---------------------------------------------------------- #
            if workflow_state.active_workflow and not workflow_state.is_idle():
                workflow = self.registry.get_workflow(workflow_state.active_workflow)

                if workflow:
                    logger.info(f"[Route] Continuing workflow '{workflow_state.active_workflow}'")
                    response = workflow.process(message, workflow_state, user_id)
                    workflow_state.add_message("assistant", response.message)
                    return self._convert_response(
                        response, workflow_state, workflow.workflow_name, user_id
                    )
                else:
                    logger.warning("[Route] Active workflow missing from registry – resetting")
                    workflow_state.complete_workflow()

            # ---------------------------------------------------------- #
            # 6. "LOG AGAIN" SHORTCUT → mood workflow
            # ---------------------------------------------------------- #
            is_log_again = (
                any(p in msg_lower for p in LOG_AGAIN_PHRASES)
                and not any(w in msg_lower for w in LOG_AGAIN_EXCLUSIONS)
            )

            if is_log_again:
                logger.info("[Route] 'Log again' → mood workflow")
                return self._start_workflow("mood_logging", message, workflow_state, user_id)

            # ---------------------------------------------------------- #
            # 7. MOOD EXPRESSION DETECTION (free text, not a button)
            # ---------------------------------------------------------- #
            if not is_log_btn and not is_start_btn and not is_start_content_btn:
                # Check for explicit mood log commands
                explicit_mood_log = any(phrase in msg_lower for phrase in ["log mood", "log my mood", "track mood"])
                if explicit_mood_log:
                    logger.info("[Route] Explicit mood log request → mood workflow")
                    workflow_state.complete_workflow()
                    return self._start_workflow("mood_logging", message, workflow_state, user_id)
                
                # Check for mood expressions in natural language
                if self._is_mood_expression(msg_lower):
                    logger.info(f"[Route] Mood expression detected: '{message}' → mood workflow")
                    workflow_state.complete_workflow()
                    return self._start_workflow("mood_logging", message, workflow_state, user_id)
                else:
                    logger.info(f"[Route] Not a mood expression: '{message}'")

            # ---------------------------------------------------------- #
            # 8. EXTERNAL / ACTIVITY-START BUTTONS
            # ---------------------------------------------------------- #
            if is_start_content_btn or is_start_btn:
                logger.info(f"[Route] Activity-start button '{msg_raw}' → activity workflow")
                return self._start_workflow("activity_logging", message, workflow_state, user_id)

            # ---------------------------------------------------------- #
            # 9. MOOD EMOJI DIRECT LOGGING
            # ---------------------------------------------------------- #
            try:
                from .mood_handler import validate_mood_emoji

                if validate_mood_emoji(msg_raw):
                    logger.info(f"[Route] Mood emoji '{msg_raw}' → mood workflow")
                    return self._start_workflow("mood_logging", message, workflow_state, user_id)

            except Exception:
                logger.warning("[Route] Mood emoji check failed – continuing", exc_info=True)

            # ---------------------------------------------------------- #
            # 10. LLM INTENT DETECTION
            # ---------------------------------------------------------- #
            logger.info("[Route] Falling back to LLM intent detection")

            intent_result = self._detect_intent(message, workflow_state, user_id)
            primary = intent_result.get("primary_intent", "general_chat")
            secondary = intent_result.get("secondary_intent")

            logger.info(f"[Route] Intent: primary={primary} secondary={secondary}")

            # Stash entities so workflows can read them
            if "entities" in intent_result:
                workflow_state.set_workflow_data("intent_entities", intent_result["entities"])

            workflow = self.registry.get_workflow_for_intent(primary)

            if not workflow:
                logger.warning(f"[Route] No workflow for intent '{primary}' – using general_chat")
                workflow = self.registry.get_workflow_for_intent("general_chat")
                
                if not workflow:
                    # Last resort: try to get GeneralWorkflow directly
                    logger.error("[Route] general_chat workflow not found in registry!")
                    logger.info(f"[Route] Available workflows: {self.registry.list_workflows()}")
                    logger.info(f"[Route] Intent mappings: {list(self.registry.intent_to_workflow.keys())}")
                    
                    # Try to create it directly
                    try:
                        from .general_workflow import GeneralWorkflow
                        workflow = GeneralWorkflow()
                        logger.info("[Route] Created GeneralWorkflow directly as fallback")
                    except Exception as e:
                        logger.error(f"[Route] Failed to create GeneralWorkflow: {e}")

            if not workflow:
                return {
                    "message": "I'm here to help! You can log your mood or activities anytime.",
                    "ui_elements": [],
                    "completed": True,
                    "state": "idle",
                }

            # Multi-intent
            if self.enable_multi_intent and secondary and secondary != "none":
                return self._handle_multi_intent(
                    message, workflow_state, user_id, primary, secondary
                )

            response = workflow.start(message, workflow_state, user_id)

            if self.enable_validation:
                validate_response(response, workflow.workflow_name, strict=False)

            workflow_state.add_message("assistant", response.message)
            return self._convert_response(response, workflow_state, workflow.workflow_name, user_id)

        except Exception:
            logger.exception(f"[Route] Routing error for user={user_id}")
            from .fallback_responses import get_error_fallback
            return get_error_fallback()

    # ------------------------------------------------------------------ #
    # HELPERS
    # ------------------------------------------------------------------ #

    def _start_workflow(self, intent: str, message: str, workflow_state, user_id: int) -> dict:
        """Look up a workflow by intent, start it, and return the converted response."""
        workflow = self.registry.get_workflow_for_intent(intent)

        if not workflow:
            logger.error(f"[Engine] No workflow registered for intent '{intent}'")
            return {
                "message": "I'm not sure how to help with that.",
                "ui_elements": [],
                "completed": True,
                "state": "idle",
            }

        response = workflow.start(message, workflow_state, user_id)
        workflow_state.add_message("assistant", response.message)
        return self._convert_response(response, workflow_state, workflow.workflow_name, user_id)

    def _detect_intent(self, message: str, workflow_state, user_id: int) -> dict:
        """Detect intent via LLM with conversation context."""
        try:
            from chat_assistant.domain.llm.intent_extractor import get_intent_extractor

            extractor = get_intent_extractor()
            context = {
                "active_workflow": workflow_state.active_workflow,
                "state": workflow_state.state.value,
                "conversation_history": workflow_state.conversation_history,
            }
            return extractor.extract_intent(message, context=context)

        except Exception:
            logger.exception("[Engine] Intent detection failed – defaulting to general_chat")
            return {"primary_intent": "general_chat", "secondary_intent": "none", "confidence": 0.5}

    def _is_mood_expression(self, msg_lower: str) -> bool:
        """Return True when the message reads as a free-text mood statement."""
        # Phrase + keyword combo
        for phrase in MOOD_PHRASES:
            if phrase in msg_lower:
                for kw in MOOD_KEYWORDS:
                    if kw in msg_lower:
                        logger.debug(f"[Mood] phrase='{phrase}' kw='{kw}'")
                        return True

        # Short standalone keyword (≤ 3 words, no button-like patterns)
        button_patterns = ("start_", "log_", "content_", "_module", "button")
        if len(msg_lower.split()) <= 3 and not any(p in msg_lower for p in button_patterns):
            for kw in MOOD_KEYWORDS:
                if kw in msg_lower:
                    logger.debug(f"[Mood] standalone keyword='{kw}'")
                    return True

        return False

    def _maybe_load_db_history(self, user_id: str, workflow_state) -> None:
        """Populate in-memory conversation history from DB after a restart."""
        if workflow_state.conversation_history:
            return   # already populated

        try:
            from app.repositories.chat_repository import ChatRepository

            messages = ChatRepository().get_recent_messages(user_id, limit=10)

            for msg in messages:
                role = "user" if msg["sender"] == "user" else "assistant"
                workflow_state.conversation_history.append(
                    {"role": role, "content": msg["message"]}
                )

            logger.info(f"[Engine] Loaded {len(messages)} messages from DB for user={user_id}")

        except Exception:
            logger.warning("[Engine] Could not load DB conversation history", exc_info=True)

    # ------------------------------------------------------------------ #
    # MULTI-INTENT
    # ------------------------------------------------------------------ #

    def _handle_multi_intent(
        self, message: str, workflow_state, user_id: int, primary: str, secondary: str
    ) -> dict:
        logger.info(f"[Multi-intent] primary={primary} secondary={secondary}")

        primary_wf = self.registry.get_workflow_for_intent(primary)
        secondary_wf = self.registry.get_workflow_for_intent(secondary)

        if not primary_wf:
            return {
                "message": "I'm not sure how to help with that.",
                "ui_elements": [],
                "completed": True,
                "state": "idle",
            }

        primary_resp = primary_wf.start(message, workflow_state, user_id)
        primary_result = self._convert_response(
            primary_resp, workflow_state, primary_wf.workflow_name, user_id
        )

        # Primary still needs input – can't run secondary yet
        if not primary_resp.completed or not secondary_wf:
            return primary_result

        # Run secondary
        workflow_state.complete_workflow()
        secondary_resp = secondary_wf.start(message, workflow_state, user_id)
        secondary_result = self._convert_response(
            secondary_resp, workflow_state, secondary_wf.workflow_name, user_id
        )

        # Merge messages
        merged_msg = f"{primary_result['message']} {secondary_result['message']}"

        if not secondary_resp.completed:
            secondary_result["message"] = merged_msg
            return secondary_result

        primary_result["message"] = merged_msg
        workflow_state.complete_workflow()
        return primary_result

    # ------------------------------------------------------------------ #
    # RESPONSE CONVERSION + EVENT PUBLISHING
    # ------------------------------------------------------------------ #

    def _convert_response(self, response, workflow_state, workflow_name: str, user_id) -> dict:
        state = workflow_state.state.value if workflow_state.state else "idle"

        result = {
            "message": response.message,
            "ui_elements": response.ui_elements,
            "completed": response.completed,
            "state": state,
        }
        result.update(response.extra_data)

        logger.info(
            f"[Engine] workflow={workflow_name} completed={response.completed} state={state}"
        )

        # Phase 2: publish events before completing workflow
        if response.completed and self.enable_events and getattr(response, "events", None):
            for event in response.events:
                self._publish_event(event, str(user_id))

        if response.completed:
            workflow_state.complete_workflow()
            logger.info(f"[Engine] workflow={workflow_name} completed – state reset")
            
            # UI elements should only be added during initialization, not after every workflow completion
            # The frontend will keep the persistent UI elements from initialization

        return result

    def _publish_event(self, event: dict, user_id: str) -> None:
        """Publish a workflow completion event (Phase 2). Never raises."""
        try:
            from app.services.event_publisher import get_event_publisher
            from app.services.behavior_scorer import get_behavior_scorer

            publisher = get_event_publisher()
            event_type = event.get("type")

            logger.info(f"[Events] Publishing '{event_type}' for user={user_id}")

            if event_type == "mood_logged":
                publisher.publish_mood_logged(
                    user_id=user_id,
                    mood_emoji=event.get("mood"),
                    reason=event.get("reason"),
                    mood_value=event.get("mood_value"),
                )
                try:
                    get_behavior_scorer().update_mood_metrics(user_id, event)
                except Exception:
                    logger.warning("[Events] Behavior scorer (mood) failed", exc_info=True)

            elif event_type == "activity_logged":
                publisher.publish_activity_logged(
                    user_id=user_id,
                    activity_type=event.get("activity_type"),
                    value=event.get("value"),
                    unit=event.get("unit"),
                )
                try:
                    get_behavior_scorer().update_activity_metrics(user_id, event)
                except Exception:
                    logger.warning("[Events] Behavior scorer (activity) failed", exc_info=True)

                try:
                    from app.services.challenge_service import ChallengeService
                    ChallengeService().update_progress_from_event(user_id, event)
                except Exception:
                    logger.warning("[Events] Challenge progress update failed", exc_info=True)

            elif event_type == "suggestion_shown":
                publisher.publish_suggestion_shown(
                    user_id=user_id,
                    suggestion_key=event.get("suggestion_key"),
                    mood_emoji=event.get("mood"),
                    reason=event.get("reason"),
                )

            elif event_type == "suggestion_accepted":
                publisher.publish_suggestion_accepted(
                    user_id=user_id,
                    suggestion_key=event.get("suggestion_key"),
                )

            logger.info(f"[Events] '{event_type}' published OK")

        except Exception:
            logger.error(f"[Events] Failed to publish '{event.get('type')}'", exc_info=True)

    # ------------------------------------------------------------------ #
    # INIT CONVERSATION
    # ------------------------------------------------------------------ #

    def init_conversation(self, user_id: str) -> dict:
        try:
            from .mood_handler import has_logged_mood_today
            from .unified_state import get_workflow_state

            uid = int(user_id)
            workflow_state = get_workflow_state(uid)
            workflow_state.complete_workflow()

            activity_buttons = [
                {"id": "log_water",    "label": "💧 Log Water"},
                {"id": "log_sleep",    "label": "😴 Log Sleep"},
                {"id": "log_exercise", "label": "🏃 Log Exercise"},
                {"id": "log_weight",   "label": "⚖️ Log Weight"},
                {"id": "log_steps",    "label": "👟 Log Steps"},
                {"id": "log_calories", "label": "🔥 Log Calories"},
                {"id": "log_meal",     "label": "🍽️ Log Meal"},
                {"id": "log_mood",     "label": "😊 Log Mood"},
            ]

            if not has_logged_mood_today(uid):
                # Show mood selector + activity buttons WITHOUT Log Mood
                return {
                    "message": "Hey! How are you feeling today?",
                    "ui_elements": ["emoji_selector", "activity_buttons"],
                    "activity_options": activity_buttons[:-1],   # exclude log_mood
                    "persistent_buttons": False,
                    "completed": False,
                    "state": "idle",
                }

            # Mood already logged – show all buttons including Log Mood
            return {
                "message": "Hey there! What do you want to track?",
                "ui_elements": ["activity_buttons"],
                "activity_options": activity_buttons,
                "persistent_buttons": False,
                "completed": True,
                "state": "idle",
            }

        except Exception:
            logger.exception(f"[Engine] init_conversation failed for user={user_id}")
            return {
                "message": "Welcome! What would you like to track? 🌟",
                "ui_elements": ["activity_buttons"],
                "activity_options": [
                    {"id": "log_water",    "label": "💧 Log Water"},
                    {"id": "log_sleep",    "label": "😴 Log Sleep"},
                    {"id": "log_exercise", "label": "🏃 Log Exercise"},
                    {"id": "log_weight",   "label": "⚖️ Log Weight"},
                    {"id": "log_steps",    "label": "👟 Log Steps"},
                    {"id": "log_calories", "label": "🔥 Log Calories"},
                    {"id": "log_meal",     "label": "🍽️ Log Meal"},
                    {"id": "log_mood",     "label": "😊 Log Mood"},
                ],
                "persistent_buttons": False,
                "completed": True,
                "state": "idle",
            }


# ------------------------------------------------------------------ #
# GLOBAL SINGLETON
# ------------------------------------------------------------------ #

_engine: ChatEngineWorkflow | None = None


def get_chat_engine() -> ChatEngineWorkflow:
    global _engine
    if _engine is None:
        _engine = ChatEngineWorkflow()
    return _engine


def process_message(user_id: str, message: str) -> dict:
    return get_chat_engine().process_message(user_id, message)


def init_conversation(user_id: str) -> dict:
    return get_chat_engine().init_conversation(user_id)