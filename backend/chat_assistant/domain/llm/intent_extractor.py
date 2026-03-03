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
    INTENT_ACTIVITY_QUERY = "activity_query"  # New: For activity suggestions
    INTENT_CHALLENGES = "challenges"
    INTENT_GENERAL_CHAT = "general_chat"
    INTENT_CLARIFICATION = "clarification"
    INTENT_OFF_TOPIC = "off_topic"  # New: For inappropriate/off-topic content
    
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
            
            # Define JSON schema (strict mode requires all properties to be required or none)
            schema = {
                "type": "object",
                "properties": {
                    "primary_intent": {
                        "type": "string",
                        "enum": [
                            "mood_logging",
                            "activity_logging",
                            "activity_query",
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
                            "activity_logging",
                            "activity_query",
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
                            "mood_emoji": {"type": "string"},
                            "activity_type": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit": {"type": "string"}
                        },
                        "required": ["mood_emoji", "activity_type", "quantity", "unit"],  # ← All properties required in strict mode
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
        
        prompt = f"""
You are a strict intent classification engine for a wellness tracking application.

Your task:
Classify the user message into ONE primary intent and optionally ONE secondary intent.
You MUST choose only from the allowed intent list.

Allowed primary_intent values:
- mood_logging
- activity_logging
- activity_query
- challenges
- general_chat
- clarification
- off_topic

Definitions:

1) mood_logging
User expresses feelings, emotions, or physical/mental states.
Includes emotional statements, standalone emojis, and state descriptions.
Examples:
"I'm stressed"
"Feeling great"
"I am tired"
"I feel exhausted"
"I'm bored"
"😟"

IMPORTANT: "tired", "exhausted", "bored", "sleepy" are MOOD states, not activity logging.

2) activity_logging
User wants to log measurable health data OR expresses intent to log/update/track activities.
Supported activity types:
- water (ml, glasses)
- sleep (hours)
- exercise (minutes, workout)
- weight (kg, lbs)

Examples WITH numbers (complete):
"I drank 2 glasses of water"
"Slept 7 hours"
"Worked out 30 minutes"
"I weigh 70 kg"

Examples WITHOUT numbers (intent to log):
"I want to log water"
"I want to update weight"
"I want to track my sleep"
"log exercise"

IMPORTANT: 
- If message mentions logging/updating/tracking water/sleep/exercise/weight → activity_logging
- "I am tired" = mood_logging (expressing feeling, no intent to log)
- "I want to log sleep" = activity_logging (intent to log)
- "I slept 6 hours" = activity_logging (has number)

3) activity_query
User asks for activity suggestions, recommendations, or information about wellness activities.
This includes:
- Asking for suggestions/recommendations
- Asking about specific activity types (mindfulness, yoga, meditation, etc.)
- Expressing desire to do a wellness activity
- Asking "what can I do" or "tell me about"

Examples:
"what activity for stress"
"what can I do for anxiety"
"suggest activities for relaxation"
"suggest some activities on mindfulness"
"tell me about yoga"
"tell me about meditation"
"what should I do for sleep"
"activities to help with work stress"
"recommend something for anxiety"
"I want to meditate"
"I want to meditation"
"I want to do breathing exercises"
"I want to journal"
"I want to relax"
"show me mindfulness activities"
"what are some exercises for stress"
"help me with anxiety activities"

IMPORTANT: 
- ANY request for suggestions/recommendations = activity_query
- "Tell me about [activity type]" = activity_query (asking for info)
- "Suggest activities on [topic]" = activity_query (asking for suggestions)
- "I want to [wellness activity]" = activity_query (user wants to DO an activity)
- "I'm stressed" = mood_logging (expressing feeling only, no request)
- "what activity for stress" = activity_query (asking for help)

4) challenges
User asks about:
- challenge progress
- status
- points
- performance
- viewing challenges

Examples:
"How am I doing?"
"Show my challenges"
"What's my progress?"
"How am I doing with sleep?"

IMPORTANT:
If message includes phrases like:
"how am I doing"
"my progress"
"my status"
"classify as challenges"

5) general_chat
Greetings, onboarding, help questions, thanks.
Examples:
"Hello"
"What can you do?"
"Thanks"

5) clarification
Short follow-up responses:
"yes"
"no"
"okay"
"5"
"2 glasses"

6) off_topic
Unrelated, abusive, or non-wellness content.
Weather, politics, sports, jokes, profanity, spam.

---

MULTI-INTENT RULES:

If message contains BOTH emotion and activity:
- Detect both.
- If equal importance, set mood_logging as primary.
- If measurable logging is the main action, activity_logging is primary.

If message contains challenge query AND emotion:
- challenges is primary.

---

ENTITY EXTRACTION RULES:

Return ALL entity fields.

entities must contain:
- mood_emoji (string or "")
- activity_type (water | sleep | exercise | weight | "")
- quantity (number or 0)
- unit (ml | glasses | hours | minutes | kg | lbs | "")

Rules:
- If not present, return empty string "" or 0.
- Never guess missing numbers.
- Do NOT invent units.
- If user says "worked out", activity_type = exercise, quantity = 0, unit = "".

---

DISAMBIGUATION PRIORITY:

If unclear:
1) Measurable number + health word → activity_logging
2) Emotional language → mood_logging
3) Asking about progress/status → challenges
4) Single short reply → clarification
5) Otherwise → general_chat

User message:
"{message}"

Respond ONLY with valid JSON matching the required schema.
Do NOT include explanations.
"""
        
        return prompt
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based intent detection with multi-intent support"""
        message_lower = message.lower()
        
        # Check for activity query patterns FIRST (highest priority)
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
        
        # Check for mood keywords
        mood_keywords = [
            'feel', 'feeling', 'mood', 'emotion', 'happy', 'sad',
            'anxious', 'stressed', 'great', 'terrible', 'okay',
            'good', 'bad', 'angry', 'worried', 'excited', 'tired',
            'horrible', 'awful', 'depressed', 'nervous', 'sleepy',
            'exhausted', 'energetic', 'calm', 'frustrated', 'bored'
        ]
        
        # Check for activity keywords
        activity_keywords = [
            'water', 'sleep', 'slept', 'exercise', 'workout', 'weight',
            'drank', 'drink', 'glasses', 'hours', 'minutes', 'kg', 'lbs',
            'walked', 'ran', 'gym'
        ]
        
        # Check for challenge keywords
        challenge_keywords = [
            'challenge', 'challenges', 'progress', 'points',
            'show challenge', 'my challenge', 'view challenge',
            'leaderboard', 'achievement'
        ]
        
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
                # Activity mentioned first
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
