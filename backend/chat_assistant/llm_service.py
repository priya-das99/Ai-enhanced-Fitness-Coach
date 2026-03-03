# llm_service.py
# Centralized LLM service for all OpenAI interactions
# Uses OpenAI Responses API for text generation
# Uses Chat Completions API for structured JSON outputs (with JSON schema support)

import json
import logging
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, ENABLE_LLM, LLM_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client (v1.0+ API)
_openai_client = None
if OPENAI_API_KEY:
    if not OPENAI_API_KEY.startswith('sk-'):
        logger.error(f"Invalid OpenAI API key format")
    else:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"✅ OpenAI client initialized (model: {LLM_MODEL})")
else:
    logger.warning("⚠️  No OpenAI API key found in environment")

# Rate limiting
last_openai_call = 0
MIN_CALL_INTERVAL = 1  # seconds between calls


class LLMError(Exception):
    """Base exception for LLM errors"""
    pass


class LLMUnavailableError(LLMError):
    """LLM service is not available"""
    pass


class LLMAPIError(LLMError):
    """OpenAI API error"""
    pass


class LLMService:
    """
    Centralized LLM service for all OpenAI interactions.
    
    Features:
    - Text generation (call) - Uses Responses API
    - Structured JSON output (call_structured) - Uses Responses API with JSON schema
    - Consistent error handling
    - Rate limiting
    - Logging
    
    Uses OpenAI Responses API (modern, non-legacy)
    """
    
    def __init__(self):
        self.client = _openai_client
        self.model = LLM_MODEL
        
        # Predefined suggestion categories
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
                "description": "Mindfulness or meditation",
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
            "take_break": {
                "id": "take_break",
                "name": "Take a Break",
                "effort": "low",
                "work_friendly": True,
                "description": "Step away from current activity",
                "duration": "5 min"
            }
        }
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return ENABLE_LLM and self.client is not None
    
    def _rate_limit(self):
        """Apply rate limiting between API calls"""
        global last_openai_call
        current_time = time.time()
        if current_time - last_openai_call < MIN_CALL_INTERVAL:
            time_since = current_time - last_openai_call
            time.sleep(MIN_CALL_INTERVAL - time_since)
        last_openai_call = time.time()
    
    def call(
        self,
        prompt: str = None,
        system_message: str = "You are a  personalized helpful assistant in a Fitness app called Vantage Fit .",
        max_tokens: int = 100,
        temperature: float = 0.3,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Call OpenAI Responses API and return response text.
        Uses modern OpenAI Responses API (not Chat Completions).
        
        Args:
            prompt: User prompt (optional if messages provided)
            system_message: System message (default: wellness app assistant)
            max_tokens: Max tokens in response
            temperature: Temperature (0.0-1.0)
            messages: Optional full message list (overrides prompt/system_message)
                     Format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]
            
        Returns:
            Response text
            
        Raises:
            LLMUnavailableError: If LLM is not available
            LLMAPIError: If API call fails
        """
        if not self.is_available():
            raise LLMUnavailableError("LLM service is not available")
        
        self._rate_limit()
        
        try:
            # Build input messages
            if messages is None:
                if prompt is None:
                    raise ValueError("Either 'prompt' or 'messages' must be provided")
                input_messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            else:
                input_messages = messages
            
            # Use OpenAI Responses API
            response = self.client.responses.create(
                model=self.model,
                input=input_messages,
                temperature=temperature,
                max_output_tokens=max(16, max_tokens),  # Minimum 16 tokens required
                timeout=LLM_TIMEOUT
            )
            
            # Response API returns output_text directly
            return response.output_text.strip()
            
        except Exception as e:
            logger.error(f"❌ OpenAI Responses API error: {e}")
            raise LLMAPIError(f"OpenAI API error: {e}")
    
    def call_structured(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        schema_name: str = "response",
        system_message: str = "You are a helpful assistant in a wellness app.",
        temperature: float = 0.2,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Call OpenAI Chat Completions API with Structured Outputs.
        
        Note: Responses API doesn't support JSON schema validation, so we use
        Chat Completions API for structured outputs with strict schema validation.
        
        Args:
            prompt: User prompt
            json_schema: JSON schema for structured output
            schema_name: Name for the schema
            system_message: System message
            temperature: Temperature (lower for structured output)
            max_tokens: Max tokens in response
            
        Returns:
            Parsed JSON response (guaranteed to match schema)
            
        Raises:
            LLMUnavailableError: If LLM is not available
            LLMAPIError: If API call fails
        """
        if not self.is_available():
            raise LLMUnavailableError("LLM service is not available")
        
        self._rate_limit()
        
        try:
            # Use Chat Completions API with Structured Outputs
            # (Responses API doesn't support JSON schema validation)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=LLM_TIMEOUT,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": json_schema
                    }
                }
            )
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                return json.loads(content)
            
            raise LLMAPIError("No response from OpenAI")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            raise LLMAPIError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            raise LLMAPIError(f"OpenAI API error: {e}")

    
    # --------------------
    # INTENT DETECTION (Legacy method - kept for backward compatibility)
    # --------------------
    def detect_intent(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Detect user intent from message with optional conversation context.
        Returns: 'log_mood', 'activity_query', 'challenge_query', or 'unknown'
        
        Args:
            user_message: The current user message
            conversation_history: Optional list of previous messages for context
        
        Note: This is a legacy method. New code should use IntentExtractor
        from domain.llm.intent_extractor for multi-intent support.
        """
        if not self.is_available():
            return self._fallback_intent_detection(user_message)

        # Build prompt with context if available
        if conversation_history and len(conversation_history) > 0:
            # Include last 3 messages for context
            recent_history = conversation_history[-6:]  # Last 3 exchanges (user + bot)
            context_str = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Bot'}: {msg['content']}"
                for msg in recent_history
            ])
            
            prompt = f"""You are an AI assistant in a wellness app. Detect the user's intent based on the conversation context.

Recent conversation:
{context_str}

User's latest message: "{user_message}"

Respond with ONLY ONE of these intents:
- "activity_query" if user is asking for activity suggestions or recommendations
- "challenge_query" if user is asking about challenges
- "log_mood" if user is expressing their current feelings or emotions
- "activity_logging" if user is logging an activity (water, sleep, exercise, etc.)
- "unknown" if it's a greeting, question, or unrelated

Consider the context: if the bot just asked a question and user says "yes", "ok", "sure", understand what they're agreeing to.

Intent:"""
        else:
            # No context - use simple prompt
            prompt = f"""You are an AI assistant in a wellness app. Detect the user's intent.

User said: "{user_message}"

Respond with ONLY ONE of these intents:
- "activity_query" if user is asking for activity suggestions or recommendations (e.g., "what activity", "what can I do", "suggest activity", "help me with [problem]")
- "challenge_query" if user is asking about challenges
- "log_mood" if user is expressing their current feelings or emotions
- "activity_logging" if user is logging an activity (water, sleep, exercise, etc.)
- "unknown" if it's a greeting, question, or unrelated

Intent:"""

        try:
            result = self.call(prompt, max_tokens=20, temperature=0.1)
            result_lower = result.lower()
            
            if 'activity_logging' in result_lower or 'log' in result_lower:
                logger.info(f"🤖 Detected intent: activity_logging")
                return 'activity_logging'
            elif 'activity' in result_lower:
                logger.info(f"🤖 Detected intent: activity_query")
                return 'activity_query'
            elif 'challenge' in result_lower:
                logger.info(f"🤖 Detected intent: challenge_query")
                return 'challenge_query'
            elif 'log_mood' in result_lower or 'mood' in result_lower:
                logger.info(f"🤖 Detected intent: log_mood")
                return 'log_mood'
            return 'unknown'
        except Exception:
            return self._fallback_intent_detection(user_message)

    # --------------------
    # FALLBACK INTENT
    # --------------------
    def _fallback_intent_detection(self, user_message: str) -> str:
        message = user_message.lower()
        
        # Check for activity queries first (most specific)
        activity_keywords = [
            "what activity", "what can i do", "suggest activity",
            "activities for", "help me with", "need activity",
            "recommend activity", "activity for", "what should i do",
            "help with", "activities to", "what to do"
        ]
        for keyword in activity_keywords:
            if keyword in message:
                return "activity_query"
        
        # Check for challenge queries
        if "challenge" in message:
            return "challenge_query"
        
        # Check for mood keywords
        keywords = [
            "feel",
            "feeling",
            "mood",
            "happy",
            "sad",
            "stressed",
            "anxious",
            "tired",
            "great",
            "bad",
        ]
        for k in keywords:
            if k in message:
                return "log_mood"
        return "unknown"

    # --------------------
    # SUGGESTION SELECTION (RULE-BASED)
    # --------------------
    def select_suggestion_with_llm(
        self, mood: str, reason: str, context: Dict
    ) -> Optional[str]:
        return self._smart_rule_selection(mood, reason, context)

    def _smart_rule_selection(
        self, mood: str, reason: str, context: Dict
    ) -> Optional[str]:

        hour = context.get("hour", datetime.now().hour)
        is_work_hours = 9 <= hour <= 17
        time_period = context.get("time_period", "day")

        if reason:
            r = reason.lower()
            if "work" in r:
                return random.choice(
                    ["breathing", "stretching", "take_break"]
                    if is_work_hours
                    else ["short_walk", "meditation"]
                )

        if time_period == "morning":
            return random.choice(["stretching", "breathing"])
        if time_period == "evening":
            return random.choice(["meditation", "breathing"])

        return random.choice(["breathing", "stretching", "take_break"])


# --------------------
# GLOBAL INSTANCE
# --------------------
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
