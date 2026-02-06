import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import openai
from config import OPENAI_API_KEY, LLM_MODEL, ENABLE_LLM, LLM_TIMEOUT, MAX_RETRIES
from db import get_connection
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key at module level (for v0.28.x)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    # Validate key format (should start with 'sk-' for OpenAI)
    if not OPENAI_API_KEY.startswith('sk-'):
        logger.error(f"Invalid OpenAI API key format: key does not start with 'sk-' (starts with: '{OPENAI_API_KEY[:10]}...')")
    else:
        logger.info(f"OpenAI API key configured (length: {len(OPENAI_API_KEY)}, prefix: {OPENAI_API_KEY[:7]}...)")
else:
    logger.warning("No OpenAI API key found in environment")

# Rate limiting
last_openai_call = 0
MIN_CALL_INTERVAL = 1  # seconds between calls (OpenAI is more generous)

class LLMSuggestionService:
    def __init__(self):
        # API key is already set at module level
        pass
        
        # Predefined suggestion categories (allow-list)
        self.suggestion_categories = {
            "breathing": {
                "id": "breathing",
                "effort": "low",
                "work_friendly": True,
                "description": "Quick breathing exercises"
            },
            "short_walk": {
                "id": "short_walk", 
                "effort": "medium",
                "work_friendly": False,
                "description": "Brief walk or movement"
            },
            "meditation": {
                "id": "meditation",
                "effort": "low", 
                "work_friendly": True,
                "description": "Mindfulness or meditation"
            },
            "stretching": {
                "id": "stretching",
                "effort": "low",
                "work_friendly": True, 
                "description": "Gentle stretches"
            },
            "take_break": {
                "id": "take_break",
                "effort": "low",
                "work_friendly": True,
                "description": "Step away from current activity"
            }
        }

    def get_recent_suggestions(self, user_id: str, hours: int = 24) -> List[str]:
        """Get recent suggestions given to user"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get recent mood logs that had suggestions
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "SELECT mood, reason FROM mood_logs WHERE user_id = ? AND timestamp > ? ORDER BY timestamp DESC",
                (user_id, since_time)
            )
            
            recent_logs = cursor.fetchall()
            conn.close()
            
            # Extract what suggestions would have been given
            recent_suggestions = []
            for mood, reason in recent_logs:
                if mood.lower() in ["horrible", "not good", "tired"]:
                    # This is a simplified way to track - in production you'd log actual suggestions
                    recent_suggestions.append(f"{mood}_{reason or 'default'}")
            
            return recent_suggestions
            
        except Exception as e:
            logger.error(f"Error getting recent suggestions: {e}")
            return []

    def get_context_info(self) -> Dict:
        """Get current context information"""
        now = datetime.now()
        
        return {
            "hour": now.hour,
            "day_of_week": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "is_work_hours": 9 <= now.hour <= 17,
            "time_period": self._get_time_period(now.hour)
        }

    def _get_time_period(self, hour: int) -> str:
        """Categorize time of day"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon" 
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def select_suggestion_with_llm(self, mood: str, reason: str, user_id: str) -> tuple[Optional[str], str]:
        """Use LLM to select best suggestion from predefined list"""
        
        if not ENABLE_LLM or not OPENAI_API_KEY:
            logger.info("LLM disabled or no API key, using fallback")
            return None, "disabled"
            
        try:
            # Try actual OpenAI LLM first
            llm_suggestion = self._try_openai_selection(mood, reason, user_id)
            if llm_suggestion:
                logger.info(f"🤖 OpenAI LLM selected: {llm_suggestion}")
                return llm_suggestion, "openai_llm"
            
            # Fallback to smart rule-based selection
            logger.info("OpenAI failed, using smart rule-based selection")
            fallback_suggestion = self._smart_rule_selection_fallback(mood, reason, user_id)
            return fallback_suggestion, "smart_rules"
                
        except Exception as e:
            logger.error(f"LLM selection failed: {e}")
            fallback_suggestion = self._smart_rule_selection_fallback(mood, reason, user_id)
            return fallback_suggestion, "smart_rules"

    def _try_openai_selection(self, mood: str, reason: str, user_id: str) -> Optional[str]:
        """Try to get suggestion from OpenAI LLM with rate limiting"""
        
        global last_openai_call
        
        # Rate limiting - avoid quota issues
        current_time = time.time()
        if current_time - last_openai_call < MIN_CALL_INTERVAL:
            logger.info(f"Rate limiting: skipping OpenAI call (last call {current_time - last_openai_call:.1f}s ago)")
            return None
        
        # Get context for better suggestions
        context = self.get_context_info()
        
        # Create a focused prompt for OpenAI
        prompt = f"""You are a wellness assistant. Select ONE activity from this exact list: breathing, meditation, stretching, take_break, short_walk

Context:
- User mood: {mood}
- Reason: {reason or 'not specified'}
- Time: {context['time_period']}
- Work hours: {context['is_work_hours']}

Choose the most appropriate activity. Respond with ONLY the activity name (one word):"""
        
        try:
            last_openai_call = current_time
            
            response = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful wellness assistant. Always respond with exactly one word from the given options."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3,
                timeout=LLM_TIMEOUT
            )
            
            if response.choices and response.choices[0].message:
                suggestion_text = response.choices[0].message.content.strip().lower()
                
                # Map common variations to our categories
                if "breathing" in suggestion_text or "breath" in suggestion_text:
                    suggestion_text = "breathing"
                elif "meditation" in suggestion_text or "meditate" in suggestion_text:
                    suggestion_text = "meditation"
                elif "stretching" in suggestion_text or "stretch" in suggestion_text:
                    suggestion_text = "stretching"
                elif "take" in suggestion_text or "break" in suggestion_text:
                    suggestion_text = "take_break"
                elif "walk" in suggestion_text:
                    suggestion_text = "short_walk"
                else:
                    # Default to first word if it matches our categories
                    first_word = suggestion_text.split()[0] if suggestion_text.split() else ""
                    if first_word in self.suggestion_categories:
                        suggestion_text = first_word
                
                if suggestion_text in self.suggestion_categories:
                    logger.info(f"OpenAI successfully selected: {suggestion_text}")
                    return suggestion_text
                else:
                    logger.warning(f"OpenAI returned unmappable response: '{response.choices[0].message.content.strip()}'")
                    
        except Exception as e:
            logger.warning(f"OpenAI API call failed")
            
        return None

    def _smart_rule_selection_fallback(self, mood: str, reason: str, user_id: str) -> Optional[str]:
        """Enhanced rule-based selection as fallback"""
        
        try:
            recent_suggestions = self.get_recent_suggestions(user_id)
            context = self.get_context_info()
            return self._smart_rule_selection(mood, reason, recent_suggestions, context)
        except Exception as e:
            logger.error(f"Smart rule selection failed: {e}")
            return "breathing"  # Ultimate fallback

    def _smart_rule_selection(self, mood: str, reason: str, recent_suggestions: List[str], context: Dict) -> Optional[str]:
        """Enhanced rule-based selection with context awareness"""
        
        # Available options
        options = list(self.suggestion_categories.keys())
        
        # Filter based on work hours
        if context['is_work_hours']:
            # Prefer work-friendly options during work hours
            work_friendly = [opt for opt in options if self.suggestion_categories[opt]['work_friendly']]
            if work_friendly:
                options = work_friendly
        
        # Filter based on time of day
        if context['time_period'] == 'morning':
            # Morning: prefer energizing activities
            preferred = ['stretching', 'breathing', 'short_walk']
        elif context['time_period'] == 'afternoon':
            # Afternoon: prefer quick refreshers
            preferred = ['take_break', 'breathing', 'stretching']
        elif context['time_period'] == 'evening':
            # Evening: prefer calming activities
            preferred = ['meditation', 'breathing', 'stretching']
        else:  # night
            # Night: prefer very gentle activities
            preferred = ['breathing', 'meditation']
        
        # Find intersection of available and preferred
        smart_options = [opt for opt in preferred if opt in options]
        if not smart_options:
            smart_options = options
        
        # Avoid recently suggested if possible
        if recent_suggestions and len(smart_options) > 1:
            # Simple heuristic: avoid if recent suggestion contains similar keywords
            filtered_options = []
            for opt in smart_options:
                avoid = False
                for recent in recent_suggestions[:2]:  # Check last 2
                    if any(keyword in recent.lower() for keyword in [opt, mood.lower()]):
                        avoid = True
                        break
                if not avoid:
                    filtered_options.append(opt)
            
            if filtered_options:
                smart_options = filtered_options
        
        # Select the first option from smart selection
        # In a real implementation, you could add more sophisticated logic here
        import random
        return random.choice(smart_options) if smart_options else None

    def _build_selection_prompt(self, mood: str, reason: str, recent_suggestions: List[str], context: Dict) -> str:
        """Build prompt for LLM suggestion selection"""
        
        prompt = f"""Select one wellness activity from this list:

Available options:
- breathing
- meditation  
- stretching
- take_break
- short_walk

Context: It's {context['time_period']} and work hours: {context['is_work_hours']}

Choose the most appropriate option (respond with just the option name):"""

        return prompt

    def _build_simple_prompt(self, mood: str, reason: str, context: Dict) -> str:
        """Build a simpler prompt for retry attempts"""
        
        prompt = f"""Pick one: breathing, meditation, stretching, take_break, short_walk

Answer:"""

        return prompt

    def _parse_llm_response(self, response: str) -> Optional[str]:
        """Parse LLM response to extract suggestion ID"""
        if not response:
            return None
            
        # Clean response
        suggestion_id = response.strip().lower()
        
        # Remove common prefixes/suffixes and extra text
        lines = suggestion_id.split('\n')
        suggestion_id = lines[0].strip()  # Take first line only
        
        # Remove common prefixes
        prefixes_to_remove = ["suggestion id:", "id:", "response:", "answer:", "suggestion:"]
        for prefix in prefixes_to_remove:
            if suggestion_id.startswith(prefix):
                suggestion_id = suggestion_id[len(prefix):].strip()
        
        # Remove punctuation
        suggestion_id = suggestion_id.replace(".", "").replace(",", "").replace(":", "")
        
        logger.info(f"Parsed suggestion from LLM response '{response.strip()}' -> '{suggestion_id}'")
        
        # Check for partial matches and fix common issues
        if suggestion_id in ["take", "take_", "break"]:
            suggestion_id = "take_break"
        elif suggestion_id in ["short", "short_", "walk"]:
            suggestion_id = "short_walk"
        elif suggestion_id in ["breath", "breathe"]:
            suggestion_id = "breathing"
        elif suggestion_id in ["meditate", "mindfulness"]:
            suggestion_id = "meditation"
        elif suggestion_id in ["stretch"]:
            suggestion_id = "stretching"
        
        return suggestion_id if suggestion_id in self.suggestion_categories else None

# Global service instance
llm_service = LLMSuggestionService()