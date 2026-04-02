# chat_assistant/domain/llm/intent_extractor.py
# Structured intent extraction using centralized LLM service

import logging
from typing import Dict, Any, Optional
from chat_assistant.llm_service import get_llm_service, LLMUnavailableError, LLMAPIError

logger = logging.getLogger(__name__)

class IntentExtractor:
    """
    Extracts user intent using centralized LLM service with strict JSON schema.
    
    Returns structured intent with:
    - primary_intent: Main user intent
    - secondary_intent: Optional secondary intent
    - confidence: Confidence level (high/medium/low)
    - entities: Extracted entities (mood, activity type, quantity, etc.)
    """
    
    # Intent types
    INTENT_MOOD_LOGGING = "mood_logging"
    INTENT_ACTIVITY_LOGGING = "activity_logging"
    INTENT_LOG_EXERCISE = "log_exercise"
    INTENT_LOG_WATER = "log_water"
    INTENT_LOG_SLEEP = "log_sleep"
    INTENT_LOG_WEIGHT = "log_weight"
    INTENT_ACTIVITY_QUERY = "activity_query"  # For activity suggestions
    INTENT_ACTIVITY_SUMMARY = "activity_summary"  # For viewing logged activities
    INTENT_CHALLENGES = "challenges"
    INTENT_GENERAL_CHAT = "general_chat"
    INTENT_CLARIFICATION = "clarification"
    INTENT_OFF_TOPIC = "off_topic"
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def extract_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract intent from user message.
        
        Args:
            message: User's message
            context: Optional context (active_workflow, state, etc.)
            
        Returns:
            {
                'primary_intent': str,
                'secondary_intent': str or None,
                'confidence': 'high' | 'medium' | 'low',
                'entities': dict
            }
        """
        try:
            # Build prompt with context
            prompt = self._build_prompt(message, context)
            
            # Define JSON schema with optional entity fields
            schema = {
                "type": "object",
                "properties": {
                    "primary_intent": {
                        "type": "string",
                        "enum": [
                            "mood_logging",
                            "log_exercise",
                            "log_water",
                            "log_sleep",
                            "log_weight",
                            "log_meal",
                            "log_steps",
                            "log_calories",
                            "activity_logging",
                            "activity_query",
                            "activity_summary",
                            "challenges",
                            "general_chat",
                            "clarification",
                            "off_topic"
                        ]
                    },
                    "secondary_intent": {
                        "type": "string",
                        "enum": [
                            "mood_logging",
                            "log_exercise",
                            "log_water",
                            "log_sleep",
                            "log_weight",
                            "log_meal",
                            "log_steps",
                            "log_calories",
                            "activity_logging",
                            "activity_query",
                            "activity_summary",
                            "challenges",
                            "general_chat",
                            "clarification",
                            "off_topic",
                            "none"
                        ]
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    },
                    "entities": {
                        "type": "object",
                        "properties": {
                            "mood_emoji": {"type": ["string", "null"]},
                            "activity_type": {"type": ["string", "null"]},
                            "quantity": {"type": ["number", "null"]},
                            "unit": {"type": ["string", "null"]}
                        },
                        "required": [],  # No required fields - all optional
                        "additionalProperties": False
                    }
                },
                "required": ["primary_intent", "secondary_intent", "confidence", "entities"],
                "additionalProperties": False
            }
            
            # Call LLM service with structured output
            result = self.llm_service.call_structured(
                prompt=prompt,
                json_schema=schema,
                schema_name="intent_extraction",
                system_message="You are an intent extraction system for a wellness app.",
                temperature=0.1,
                max_tokens=200
            )
            
            logger.info(f"🤖 Intent extracted: {result['primary_intent']} (confidence: {result['confidence']})")
            return result
            
        except (LLMUnavailableError, LLMAPIError) as e:
            logger.warning(f"LLM unavailable, using fallback: {e}")
            return self._fallback_intent_detection(message)
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return self._fallback_intent_detection(message)
    
    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Build strict classification prompt for structured intent extraction"""
        
        # Build context information
        context_info = ""
        if context:
            active_workflow = context.get('active_workflow')
            workflow_state = context.get('workflow_state')
            last_activity = context.get('last_logged_activity')
            awaiting_followup = context.get('awaiting_followup', False)
            
            if active_workflow and awaiting_followup and last_activity:
                context_info = f"""
# ============================================================================
# CURRENT CONTEXT (CRITICAL - CHECK THIS FIRST!)
# ============================================================================

The user is currently in an active {active_workflow} workflow and just logged: {last_activity}
The system is awaiting potential follow-up messages.

FOLLOW-UP INTENT RULES:
- If the message indicates adding/logging more of the same activity → use the SPECIFIC intent for that activity
- "add 1 more", "2 more", "another", "log more" → continue with {last_activity} logging
- Numbers alone (like "3", "5") → likely quantities for {last_activity}
- "done", "finished", "no more", "that's all" → general_chat (ending workflow)
- Different activity mentioned → switch to that new activity intent

Examples for current context ({last_activity}):
- "add 1 more" → log_{last_activity} with quantity=1
- "2 more" → log_{last_activity} with quantity=2  
- "another glass" → log_{last_activity} with quantity=1
- "3" → clarification with quantity=3
- "one more" → log_{last_activity} with quantity=1
- "log another" → log_{last_activity} with quantity=1
- "plus 2" → log_{last_activity} with quantity=2
- "done" → general_chat
- "finished" → general_chat
- "log exercise" → log_exercise (switching activities)

CRITICAL: When in follow-up context, prioritize continuation over new intents:
- Numbers alone (1, 2, 3, etc.) → clarification with quantity
- "more", "another", "add" + number → log_{last_activity} with quantity
- "done", "finished", "no more" → general_chat
- Different activity mentioned → switch to that activity intent

"""
            elif active_workflow:
                context_info = f"""
# ============================================================================
# CURRENT CONTEXT
# ============================================================================

The user is currently in an active {active_workflow} workflow.
Consider this context when classifying the intent.

"""
        
        prompt = f"""
You are a strict intent classification engine for a wellness tracking application.

Your task:
Classify the user message into ONE primary intent and optionally ONE secondary intent.
You MUST choose only from the allowed intent list.

{context_info}

Allowed primary_intent values:
- mood_logging
- log_exercise
- log_water
- log_sleep
- log_weight
- log_meal
- log_steps
- log_calories
- activity_logging (ONLY for activities that don't fit the specific types above)
- activity_query
- challenges
- general_chat
- clarification
- off_topic

# ============================================================================
# PRIORITY RULES (CRITICAL - CHECK THESE FIRST!)
# ============================================================================

1. SPECIFIC ACTIVITY INTENTS > GENERIC ACTIVITY_LOGGING
   - "I want to log exercise" → log_exercise (NOT activity_logging)
   - "I want log weight" → log_weight (NOT activity_logging)
   - "I want to track water" → log_water (NOT activity_logging)
   - "I want to log sleep" → log_sleep (NOT activity_logging)
   - "I want to log meal" → log_meal (NOT activity_logging)
   - "I want to log steps" → log_steps (NOT activity_logging)
   - "I want to log calories" → log_calories (NOT activity_logging)
   - "log workout" → log_exercise (NOT activity_logging)
   - "track my water intake" → log_water (NOT activity_logging)

2. REQUESTS > EXPRESSIONS
   - "suggest activities for mood" → activity_query (NOT mood_logging)
   - "suggest me some mood activities" → activity_query (NOT mood_logging)
   - "recommend activities" → activity_query (NOT mood_logging)
   - "I'm stressed" → mood_logging (expressing, not requesting)

3. EXPLICIT COMMANDS > IMPLICIT EXPRESSIONS
   - "log mood" → mood_logging (explicit command)
   - "I feel sad" → mood_logging (implicit expression)
   - "log water" → log_water (explicit command)

4. ACTION VERBS INDICATE INTENT
   - suggest/recommend/show/give/tell → activity_query
   - log/track/record → logging intent (use SPECIFIC type if possible)
   - feel/am/being → mood expression

5. QUESTION WORDS + WELLNESS = ACTIVITY_QUERY
   - "what can I do" → activity_query
   - "what activities" → activity_query
   - "how do I" → activity_query

# ============================================================================
# INTENT DEFINITIONS (Check in this order)
# ============================================================================

1) activity_query (CHECK FIRST!)
User REQUESTS or ASKS FOR activity suggestions, recommendations, or information.

Key indicators:
- suggest, recommend, show me, give me, tell me about
- what can I do, what should I do, what activities
- help me with, help me find
- I want to [wellness activity]

Examples:
"suggest activities for stress"
"suggest me some mood activities"  ← CRITICAL: This is activity_query!
"suggest activities on mindfulness"
"recommend something for anxiety"
"what can I do for stress"
"what activities help with sleep"
"show me activities for anxiety"
"tell me about meditation"
"help me with stress activities"
"I want to meditate"
"I want to do breathing exercises"
"give me some activity suggestions"

IMPORTANT: 
- ANY message with "suggest", "recommend", "show me", "what can I do" = activity_query
- Even if message contains "mood", if it's a REQUEST, it's activity_query
- "suggest me some mood activities" = activity_query (requesting suggestions)
- "I'm in a bad mood" = mood_logging (expressing emotion)

2) SPECIFIC ACTIVITY LOGGING INTENTS (CHECK BEFORE GENERIC activity_logging!)

2a) log_exercise
User wants to log exercise, workout, or physical activity.

Key indicators:
- log exercise, track exercise, record exercise
- log workout, track workout
- I want to log exercise, I want log exercise
- I want to track my workout
- worked out, exercised, went to gym

Examples:
"I want to log exercise"
"I want log exercise"
"log exercise"
"track my workout"
"I worked out 30 minutes"
"I exercised today"
"log workout"
"I want to track exercise"

2b) log_water
User wants to log water intake.

Key indicators:
- log water, track water, record water
- I want to log water, I want log water
- drank water, drink water
- water intake, hydration

Examples:
"I want to log water"
"I want log water"
"log water"
"track my water intake"
"I drank 2 glasses"
"I want to track water"
"log hydration"

2c) log_sleep
User wants to log sleep.

Key indicators:
- log sleep, track sleep, record sleep
- I want to log sleep, I want log sleep
- slept, sleep hours
- rest, rested

Examples:
"I want to log sleep"
"I want log sleep"
"log sleep"
"track my sleep"
"I slept 7 hours"
"I want to track sleep"
"log rest"

2d) log_weight
User wants to log weight.

Key indicators:
- log weight, track weight, record weight
- I want to log weight, I want log weight
- weigh, weight measurement
- kg, lbs, pounds

Examples:
"I want to log weight"
"I want log weight"
"log weight"
"track my weight"
"I weigh 70 kg"
"I want to track weight"
"update my weight"

2e) log_meal
User wants to log meal or food intake.

Key indicators:
- log meal, track meal, record meal
- I want to log meal, I want log meal
- log food, track food, food intake
- ate, had lunch, had dinner, had breakfast
- meal, food, nutrition

Examples:
"I want to log meal"
"I want log meal"
"log meal"
"track my meal"
"I had lunch"
"I want to track food"
"log my breakfast"
"record what I ate"

2f) log_steps
User wants to log steps or step count.

Key indicators:
- log steps, track steps, record steps
- I want to log steps, I want log steps
- step count, daily steps, walking steps
- walked, steps taken

Examples:
"I want to log steps"
"I want log steps"
"log steps"
"track my steps"
"I walked 8500 steps"
"I want to track step count"
"log my daily steps"
"record my walking"

2g) log_calories
User wants to log calories or caloric intake.

Key indicators:
- log calories, track calories, record calories
- I want to log calories, I want log calories
- calorie intake, caloric intake, energy intake
- consumed calories, ate calories

Examples:
"I want to log calories"
"I want log calories"
"log calories"
"track my calories"
"I consumed 350 calories"
"I want to track calorie intake"
"log my energy intake"
"record calories consumed"

2h) activity_logging (GENERIC - ONLY if no specific type matches)
User wants to log measurable health data that doesn't fit the specific types above.

IMPORTANT: 
- ONLY use activity_logging if the activity doesn't match exercise, water, sleep, weight, meal, steps, or calories
- ALWAYS prefer specific intents (log_exercise, log_water, log_meal, etc.) over activity_logging
- "I want to log exercise" = log_exercise (NOT activity_logging)
- "I want log weight" = log_weight (NOT activity_logging)
- "I want to log meal" = log_meal (NOT activity_logging)

3) mood_logging
User wants to LOG their emotional state (explicit command) OR expresses feelings.

Key indicators:
- log mood, track mood, record mood (explicit)
- I feel, I'm feeling, I am + emotion (expression)
- Standalone emotions: stressed, happy, sad, anxious

Examples:
"log mood"
"I want to track my mood"
"I'm stressed"
"feeling anxious"
"I am tired"
"I feel exhausted"
"😟"

IMPORTANT: 
- "tired", "exhausted", "bored", "sleepy" are MOOD states
- "I'm stressed" = mood_logging (expressing feeling)
- "suggest activities for stress" = activity_query (requesting help)

4) activity_summary
User asks to VIEW/RETRIEVE/CHECK their logged activities or health data.
This is DIFFERENT from activity_logging (which is for LOGGING new data).
This is DIFFERENT from activity_query (which is for REQUESTING suggestions).

Key indicators:
- Question words about past actions: "did I", "have I", "how much did I", "how many"
- Viewing requests: "show me my", "what did I", "what have I"
- Progress checks: "am I on track", "how close am I", "did I reach"
- Status queries: "what was my", "my intake", "my log"

Examples:
"What did I do today?"
"Show me my activities"
"How much water did I drink?"
"How much water did I drink today?"
"Did I exercise today?"
"What's my water intake today?"
"Show me my sleep log"
"Have I logged my mood?"
"What have I tracked today?"
"My activities today"
"How many hours did I sleep?"
"What was my mood today?"
"Show my water intake for today"
"Am I on track today?"
"How close am I to my targets?"
"Did I reach my water goal?"
"Am I meeting my goals?"

CRITICAL DISTINCTION:
- "How much water did I drink?" = activity_summary (VIEWING past data)
- "How much water should I drink?" = activity_query (REQUESTING advice)
- "Did I exercise today?" = activity_summary (CHECKING logged data)
- "What exercise should I do?" = activity_query (REQUESTING suggestions)
- "I drank 2 glasses" = log_water (LOGGING new data)
- "Suggest activities for stress" = activity_query (REQUESTING suggestions)

5) challenges
User asks about:
- challenge progress, status, points, performance
- viewing challenges
- specific challenge completion requirements
- how many more [units] needed for challenges
- challenge-related questions

Examples:
"How am I doing?"
"Show my challenges"
"What's my progress?"
"How am I doing with sleep?"
"How many more glasses do I need to complete my water challenge?"
"What more glass required to complete hydration challenge?"
"How much more do I need for my challenge?"
"Am I close to completing my challenge?"
"Challenge progress"
"My challenge status"

IMPORTANT:
If message includes phrases like:
"how am I doing"
"my progress"
"my status"
"challenge" + "complete/finish/need/more/required"
"how many more" + challenge-related terms
"what more" + challenge-related terms
→ classify as challenges

6) general_chat
Greetings, onboarding, help questions, thanks.
Examples:
"Hello"
"What can you do?"
"Thanks"

7) clarification
Short follow-up responses:
"yes"
"no"
"okay"
"5"
"2 glasses"

8) off_topic
Unrelated, abusive, or non-wellness content.
Weather, politics, sports, jokes, profanity, spam.

---

MULTI-INTENT RULES:

If message contains BOTH emotion and activity:
- Detect both.
- If equal importance, set mood_logging as primary.
- If measurable logging is the main action, use SPECIFIC activity intent as primary.

If message contains challenge query AND emotion:
- challenges is primary.

---

ENTITY EXTRACTION RULES:

entities object can contain (all optional):
- mood_emoji: string or null (e.g., "😟", "😊", or null)
- activity_type: "water" | "sleep" | "exercise" | "weight" | null
- quantity: number or null (e.g., 2, 7.5, or null)
- unit: "ml" | "glasses" | "hours" | "minutes" | "kg" | "lbs" | null

Rules:
- Only include fields that are explicitly mentioned
- If not present, use null (not empty string or 0)
- Never guess missing numbers
- Do NOT invent units
- If user says "worked out" without quantity, activity_type = "exercise", quantity = null, unit = null

Examples:
- "suggest activities" → entities: {{}}
- "I'm stressed 😟" → entities: {{"mood_emoji": "😟"}}
- "I drank 2 glasses" → entities: {{"activity_type": "water", "quantity": 2, "unit": "glasses"}}
- "I want to log water" → entities: {{"activity_type": "water"}}
- "I want to log exercise" → entities: {{"activity_type": "exercise"}}

---

DISAMBIGUATION PRIORITY:

If unclear:
1) Measurable number + health word → SPECIFIC activity intent (log_exercise, log_water, etc.)
2) Emotional language → mood_logging
3) Asking about progress/status → challenges
4) Single short reply → clarification
5) Otherwise → general_chat

User message:
"{message}"

CRITICAL: Respond with ONLY valid JSON. No markdown, no code blocks, no explanations.
Format: {{"primary_intent": "...", "secondary_intent": "...", "confidence": "...", "entities": {{...}}}}

Example valid responses:
{{"primary_intent": "log_exercise", "secondary_intent": "none", "confidence": "high", "entities": {{"activity_type": "exercise"}}}}
{{"primary_intent": "log_water", "secondary_intent": "none", "confidence": "high", "entities": {{"activity_type": "water"}}}}
{{"primary_intent": "activity_query", "secondary_intent": "none", "confidence": "high", "entities": {{}}}}
{{"primary_intent": "mood_logging", "secondary_intent": "none", "confidence": "high", "entities": {{"mood_emoji": "😟"}}}}
"""
        
        return prompt
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based intent detection with multi-intent support"""
        message_lower = message.lower()
        
        # Check for activity SUMMARY patterns FIRST (viewing logged data)
        activity_summary_patterns = [
            'what did i', 'how much did i', 'how many did i', 'did i',
            'have i logged', 'show me my', 'my activities', 'what have i',
            'how much water did', 'how many hours did', 'what was my',
            'my intake', 'my log', 'am i on track', 'how close am i',
            'did i reach', 'am i meeting'
        ]
        
        has_summary_pattern = any(pattern in message_lower for pattern in activity_summary_patterns)
        
        if has_summary_pattern:
            return {
                'primary_intent': 'activity_summary',
                'secondary_intent': 'none',
                'confidence': 'high',
                'entities': {}
            }
        
        # Check for activity query patterns (requesting suggestions)
        activity_query_patterns = [
            'suggest', 'recommend', 'tell me about', 'show me', 'what are',
            'activities for', 'activities on', 'help me with', 'what can i do',
            'what should i do', 'what activity', 'give me'
        ]
        
        wellness_topics = [
            'mindfulness', 'meditation', 'yoga', 'breathing', 'exercise',
            'stress', 'anxiety', 'sleep', 'relaxation', 'calm', 'energy'
        ]
        
        # Check if message contains activity query pattern + wellness topic
        has_query_pattern = any(pattern in message_lower for pattern in activity_query_patterns)
        has_wellness_topic = any(topic in message_lower for topic in wellness_topics)
        
        if has_query_pattern and has_wellness_topic:
            return {
                'primary_intent': 'activity_query',
                'secondary_intent': 'none',
                'confidence': 'high',
                'entities': {}
            }
        
        # Check for "I want to [activity]" patterns - these are activity queries
        wellness_activity_keywords = [
            'meditate', 'meditation', 'breathe', 'breathing', 'journal', 'journaling',
            'relax', 'stretch', 'stretching', 'walk', 'music', 'yoga'
        ]
        
        if 'i want to' in message_lower or 'i want' in message_lower:
            if any(activity in message_lower for activity in wellness_activity_keywords):
                return {
                    'primary_intent': 'activity_query',
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {}
                }
        
        # Check for SPECIFIC activity logging intents (PRIORITY!)
        # "I want to log exercise" → log_exercise
        # "I want log water" → log_water
        log_intent_patterns = [
            'i want to log', 'i want log', 'want to log', 'want log',
            'i want to track', 'i want track', 'want to track', 'want track',
            'log', 'track', 'record'
        ]
        
        has_log_intent = any(pattern in message_lower for pattern in log_intent_patterns)
        
        if has_log_intent:
            # Check for specific activity types
            if 'exercise' in message_lower or 'workout' in message_lower:
                return {
                    'primary_intent': 'log_exercise',
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'exercise'}
                }
            elif 'water' in message_lower or 'hydration' in message_lower:
                return {
                    'primary_intent': 'log_water',
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'water'}
                }
            elif 'sleep' in message_lower or 'rest' in message_lower:
                return {
                    'primary_intent': 'log_sleep',
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'sleep'}
                }
            elif 'weight' in message_lower:
                return {
                    'primary_intent': 'log_weight',
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'weight'}
                }
        
        # Check for mood keywords
        mood_keywords = [
            'feel', 'feeling', 'mood', 'emotion', 'happy', 'sad',
            'anxious', 'stressed', 'great', 'terrible', 'okay',
            'good', 'bad', 'angry', 'worried', 'excited', 'tired',
            'horrible', 'awful', 'depressed', 'nervous', 'sleepy',
            'exhausted', 'energetic', 'calm', 'frustrated', 'bored'
        ]
        
        # Check for activity keywords (for generic activity_logging)
        activity_keywords = [
            'water', 'sleep', 'slept', 'exercise', 'workout', 'weight',
            'drank', 'drink', 'glasses', 'hours', 'minutes', 'kg', 'lbs',
            'walked', 'ran', 'gym'
        ]
        
        # Check for challenge keywords
        challenge_keywords = [
            'challenge', 'challenges', 'progress', 'points',
            'show challenge', 'my challenge', 'view challenge',
            'leaderboard', 'achievement', 'complete challenge',
            'finish challenge', 'how many more', 'what more',
            'need to complete', 'required to complete',
            'close to completing', 'challenge status'
        ]
        
        # Special check for challenge completion queries
        challenge_completion_patterns = [
            'how many more', 'what more', 'need to complete',
            'required to complete', 'to finish', 'to complete'
        ]
        
        # Check if message contains challenge + completion pattern
        has_challenge_word = 'challenge' in message_lower
        has_completion_pattern = any(pattern in message_lower for pattern in challenge_completion_patterns)
        
        if has_challenge_word and has_completion_pattern:
            return {
                'primary_intent': 'challenges',
                'secondary_intent': 'none',
                'confidence': 'high',
                'entities': {}
            }
        
        # Check for clarification keywords
        clarification_keywords = ['yes', 'no', 'yeah', 'nope', 'ok', 'okay', 'sure']
        
        # Determine intents
        has_mood = any(keyword in message_lower for keyword in mood_keywords)
        has_activity = any(keyword in message_lower for keyword in activity_keywords)
        has_challenge = any(keyword in message_lower for keyword in challenge_keywords)
        is_clarification = message_lower.strip() in clarification_keywords
        
        # Multi-intent detection
        if has_challenge:
            return {
                'primary_intent': 'challenges',
                'secondary_intent': 'none',
                'confidence': 'high',
                'entities': {}
            }
        elif has_mood and has_activity:
            # Check which comes first to determine primary
            mood_pos = min([message_lower.find(k) for k in mood_keywords if k in message_lower])
            activity_pos = min([message_lower.find(k) for k in activity_keywords if k in message_lower])
            
            if activity_pos < mood_pos:
                # Activity mentioned first - check for specific type
                if 'exercise' in message_lower or 'workout' in message_lower:
                    return {
                        'primary_intent': self.INTENT_LOG_EXERCISE,
                        'secondary_intent': self.INTENT_MOOD_LOGGING,
                        'confidence': 'medium',
                        'entities': {'activity_type': 'exercise'}
                    }
                elif 'water' in message_lower:
                    return {
                        'primary_intent': self.INTENT_LOG_WATER,
                        'secondary_intent': self.INTENT_MOOD_LOGGING,
                        'confidence': 'medium',
                        'entities': {'activity_type': 'water'}
                    }
                elif 'sleep' in message_lower:
                    return {
                        'primary_intent': self.INTENT_LOG_SLEEP,
                        'secondary_intent': self.INTENT_MOOD_LOGGING,
                        'confidence': 'medium',
                        'entities': {'activity_type': 'sleep'}
                    }
                elif 'weight' in message_lower:
                    return {
                        'primary_intent': self.INTENT_LOG_WEIGHT,
                        'secondary_intent': self.INTENT_MOOD_LOGGING,
                        'confidence': 'medium',
                        'entities': {'activity_type': 'weight'}
                    }
                else:
                    # Generic activity
                    return {
                        'primary_intent': self.INTENT_ACTIVITY_LOGGING,
                        'secondary_intent': self.INTENT_MOOD_LOGGING,
                        'confidence': 'medium',
                        'entities': {}
                    }
            else:
                # Mood mentioned first
                return {
                    'primary_intent': self.INTENT_MOOD_LOGGING,
                    'secondary_intent': self.INTENT_ACTIVITY_LOGGING,
                    'confidence': 'medium',
                    'entities': {}
                }
        elif has_mood:
            return {
                'primary_intent': self.INTENT_MOOD_LOGGING,
                'secondary_intent': 'none',
                'confidence': 'high',
                'entities': {}
            }
        elif has_activity:
            # Check for specific activity type
            if 'exercise' in message_lower or 'workout' in message_lower:
                return {
                    'primary_intent': self.INTENT_LOG_EXERCISE,
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'exercise'}
                }
            elif 'water' in message_lower:
                return {
                    'primary_intent': self.INTENT_LOG_WATER,
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'water'}
                }
            elif 'sleep' in message_lower:
                return {
                    'primary_intent': self.INTENT_LOG_SLEEP,
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'sleep'}
                }
            elif 'weight' in message_lower:
                return {
                    'primary_intent': self.INTENT_LOG_WEIGHT,
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {'activity_type': 'weight'}
                }
            else:
                # Generic activity
                return {
                    'primary_intent': self.INTENT_ACTIVITY_LOGGING,
                    'secondary_intent': 'none',
                    'confidence': 'high',
                    'entities': {}
                }
        elif is_clarification:
            return {
                'primary_intent': self.INTENT_CLARIFICATION,
                'secondary_intent': 'none',
                'confidence': 'medium',
                'entities': {}
            }
        else:
            return {
                'primary_intent': self.INTENT_GENERAL_CHAT,
                'secondary_intent': 'none',
                'confidence': 'low',
                'entities': {}
            }


# Global instance
_intent_extractor = None

def get_intent_extractor() -> IntentExtractor:
    """Get or create global IntentExtractor instance"""
    global _intent_extractor
    if _intent_extractor is None:
        _intent_extractor = IntentExtractor()
    return _intent_extractor
