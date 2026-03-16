# llm_service.py
# Centralized LLM service for all OpenAI interactions
# Uses OpenAI Responses API for all text generation

import json
import logging
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, ENABLE_LLM, LLM_TIMEOUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
_openai_client = None
if OPENAI_API_KEY:
    if not OPENAI_API_KEY.startswith("sk-"):
        logger.error("Invalid OpenAI API key format")
    else:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"OpenAI client initialized (model: {LLM_MODEL})")
else:
    logger.warning("No OpenAI API key found")

# Rate limiting
last_openai_call = 0
MIN_CALL_INTERVAL = 1


class LLMError(Exception):
    pass


class LLMUnavailableError(LLMError):
    pass


class LLMAPIError(LLMError):
    pass


class LLMService:

    def __init__(self):
        self.client = _openai_client
        self.model = LLM_MODEL

        # Fitness-focused suggestion categories
        self.suggestion_categories = {
            "breathing": {
                "id": "breathing",
                "name": "Breathing Exercise",
                "effort": "low",
                "work_friendly": True,
                "description": "Quick breathing exercises",
                "duration": "3-5 min"
            },
            "short_walk": {
                "id": "short_walk",
                "name": "Short Walk",
                "effort": "medium",
                "work_friendly": False,
                "description": "Brief walk or movement",
                "duration": "10-15 min"
            },
            "meditation": {
                "id": "meditation",
                "name": "Meditation",
                "effort": "low",
                "work_friendly": True,
                "description": "Mindfulness practice",
                "duration": "5-10 min"
            },
            "stretching": {
                "id": "stretching",
                "name": "Stretching",
                "effort": "low",
                "work_friendly": True,
                "description": "Gentle stretches",
                "duration": "5-10 min"
            },
            "workout": {
                "id": "workout",
                "name": "Quick Workout",
                "effort": "medium",
                "work_friendly": False,
                "description": "Short exercise session",
                "duration": "15-20 min"
            }
        }

    def is_available(self):
        return ENABLE_LLM and self.client is not None

    def _rate_limit(self):
        global last_openai_call
        now = time.time()
        if now - last_openai_call < MIN_CALL_INTERVAL:
            time.sleep(MIN_CALL_INTERVAL - (now - last_openai_call))
        last_openai_call = time.time()

    def call(
        self,
        prompt: str = None,
        system_message: str = "You're a friendly wellness companion who talks like a real person.",
        max_tokens: int = 100,
        temperature: float = 0.7,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> str:

        if not self.is_available():
            raise LLMUnavailableError("LLM not available")

        self._rate_limit()

        try:

            if messages is None:
                if prompt is None:
                    raise ValueError("Prompt or messages required")

                input_messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            else:
                input_messages = messages

            logger.info(f"Calling OpenAI Responses API with {len(input_messages)} messages")

            response = self.client.responses.create(
                model=self.model,
                input=input_messages,
                temperature=temperature,
                max_output_tokens=max(16, max_tokens),
                timeout=LLM_TIMEOUT
            )

            result = response.output_text.strip()
            logger.info(f"LLM response length: {len(result)}")

            return result

        except Exception as e:

            err = str(e).lower()

            if "rate limit" in err:
                raise LLMAPIError("Rate limit exceeded")

            if "quota" in err or "billing" in err:
                raise LLMAPIError("Quota exceeded")

            if "authentication" in err:
                raise LLMAPIError("API authentication failed")

            if "connection" in err or "network" in err:
                raise LLMAPIError("Network error")

            raise LLMAPIError(str(e))

    def call_structured(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        schema_name: str = "response",
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.3,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Call LLM and expect JSON response.
        Note: OpenAI Responses API doesn't support structured outputs,
        so we rely on prompt engineering and parsing.
        """
        # Add explicit JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with ONLY valid JSON matching this schema. No explanations, no markdown, just raw JSON."
        
        response_text = self.call(
            prompt=json_prompt,
            system_message=system_message,
            max_tokens=max_tokens,
            temperature=temperature
        )

        try:
            # Try to parse JSON
            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Structured response parsing failed: {e}")
            logger.warning(f"Response text: {response_text[:200]}")
            return {}
        except Exception as e:
            logger.warning(f"Structured response parsing failed: {e}")
            return {}

    def call_with_fallback(
        self,
        prompt: str = None,
        system_message: str = "You're a friendly wellness companion.",
        max_tokens: int = 100,
        temperature: float = 0.7,
        messages: Optional[List[Dict[str, str]]] = None,
        fallback_response: str = "I'm having trouble right now. Please try again."
    ) -> str:

        try:
            return self.call(prompt, system_message, max_tokens, temperature, messages)
        except Exception as e:
            logger.warning(f"LLM fallback used: {e}")
            return fallback_response

    # --------------------
    # INTENT DETECTION
    # --------------------

    def detect_intent(self, user_message: str, conversation_history=None):
        """
        Simplified intent detection - only detect explicit commands.
        Most messages should go to general_chat for natural conversation.
        """
        if not self.is_available():
            return self._fallback_intent_detection(user_message)

        prompt = f"""
You are a fitness coach assistant. Detect if this is an explicit command or just conversation.

User message: "{user_message}"

Return ONLY ONE of these:
- activity_logging (explicit: "log workout", "log my run", "track exercise")
- challenge_query (explicit: "start challenge", "my challenges")
- general_chat (everything else - questions, casual talk, fitness advice)

Most messages should be general_chat. Only detect explicit logging/command requests.
"""

        try:
            result = self.call(prompt, max_tokens=20, temperature=0.1)
            r = result.lower()

            if "activity_logging" in r:
                return "activity_logging"

            if "challenge" in r:
                return "challenge_query"

            # Default to general chat for natural conversation
            return "general_chat"

        except Exception:
            return self._fallback_intent_detection(user_message)

    def _fallback_intent_detection(self, user_message):

        msg = user_message.lower()

        if "challenge" in msg:
            return "challenge_query"

        if "what activity" in msg or "suggest activity" in msg:
            return "activity_query"

        mood_words = ["happy", "sad", "stressed", "anxious", "tired"]

        for w in mood_words:
            if w in msg:
                return "log_mood"

        return "unknown"

    # --------------------
    # RULE BASED SUGGESTIONS
    # --------------------

    def select_suggestion_with_llm(self, mood, reason, context):
        return self._smart_rule_selection(mood, reason, context)

    def _smart_rule_selection(self, mood, reason, context):

        hour = context.get("hour", datetime.now().hour)
        work = 9 <= hour <= 17
        time_period = context.get("time_period", "day")

        if reason:
            r = reason.lower()

            if "work" in r:
                return random.choice(
                    ["breathing", "stretching", "take_break"]
                    if work else ["short_walk", "meditation"]
                )

        if time_period == "morning":
            return random.choice(["stretching", "breathing"])

        if time_period == "evening":
            return random.choice(["meditation", "breathing"])

        return random.choice(["breathing", "stretching", "take_break"])


_llm_service: Optional[LLMService] = None


def get_llm_service():

    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService()

    return _llm_service