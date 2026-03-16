"""
Activity Query Workflow - Handles requests for activity suggestions
Responds to queries like "what activity for stress", "help me with anxiety", etc.

Uses LLM-based reason extraction to understand ANY user query without keyword matching.
"""
from typing import Dict, Any, Optional, List
from chat_assistant.workflow_base import BaseWorkflow, WorkflowResponse
from chat_assistant.smart_suggestions import get_smart_suggestions
from chat_assistant.context_builder_simple import build_context
from chat_assistant.unified_state import WorkflowState, ConversationState
from chat_assistant.llm_service import get_llm_service, LLMUnavailableError, LLMAPIError
import re
import logging

logger = logging.getLogger(__name__)


class ActivityQueryWorkflow(BaseWorkflow):
    """Handles user queries asking for activity suggestions"""
    
    def __init__(self):
        super().__init__(
            workflow_name="activity_query",
            handled_intents=['activity_query', 'activity_request', 'activity_suggestion']
        )
        self.llm_service = get_llm_service()
    
    # Map keywords to mood emoji and reason
    REASON_MAPPING = {
        'stress': {'mood': '😟', 'reason': 'stress'},
        'stressed': {'mood': '😟', 'reason': 'stress'},
        'anxiety': {'mood': '😰', 'reason': 'anxiety'},
        'anxious': {'mood': '😰', 'reason': 'anxiety'},
        'sleep': {'mood': '😴', 'reason': 'tired'},
        'tired': {'mood': '😴', 'reason': 'tired'},
        'energy': {'mood': '😴', 'reason': 'low_energy'},
        'energize': {'mood': '😴', 'reason': 'low_energy'},
        'energizing': {'mood': '😴', 'reason': 'low_energy'},
        'boost': {'mood': '😴', 'reason': 'low_energy'},
        'mood': {'mood': '😐', 'reason': 'mood_boost'},
        'uplift': {'mood': '😐', 'reason': 'mood_boost'},
        'uplifting': {'mood': '😐', 'reason': 'mood_boost'},
        'lighten': {'mood': '😐', 'reason': 'mood_boost'},
        'lightning': {'mood': '😐', 'reason': 'mood_boost'},  # Common typo for "lightening"
        'lightening': {'mood': '😐', 'reason': 'mood_boost'},
        'lift': {'mood': '😐', 'reason': 'mood_boost'},
        'happy': {'mood': '😊', 'reason': 'happiness'},
        'joy': {'mood': '😊', 'reason': 'happiness'},
        'fun': {'mood': '😊', 'reason': 'fun'},
        'relax': {'mood': '😌', 'reason': 'calm'},
        'relaxation': {'mood': '😌', 'reason': 'calm'},
        'calm': {'mood': '😌', 'reason': 'calm'},
        'sad': {'mood': '😢', 'reason': 'sad'},
        'down': {'mood': '😢', 'reason': 'sad'},
        'angry': {'mood': '😠', 'reason': 'angry'},
        'frustrated': {'mood': '😠', 'reason': 'frustrated'},
        'overwhelm': {'mood': '😰', 'reason': 'overwhelmed'},
        'overwhelmed': {'mood': '😰', 'reason': 'overwhelmed'},
        'work': {'mood': '😟', 'reason': 'work'},
        'focus': {'mood': '🤔', 'reason': 'focus'},
        # Add wellness activity types
        'mindfulness': {'mood': '😌', 'reason': 'mindfulness'},
        'meditation': {'mood': '😌', 'reason': 'mindfulness'},
        'yoga': {'mood': '😌', 'reason': 'exercise'},
        'breathing': {'mood': '😌', 'reason': 'calm'},
        'exercise': {'mood': '😊', 'reason': 'exercise'},
        'workout': {'mood': '😊', 'reason': 'exercise'},
    }
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Start the workflow - same as process for this workflow"""
        # Start the workflow in the state
        state.start_workflow(self.workflow_name, {'step': 'processing_query'})
        return self.process(message, state, user_id)
    
    def can_handle(self, message: str, intent: Optional[str] = None) -> bool:
        """Check if this is an activity query"""
        message_lower = message.lower()
        
        # Check for activity query patterns
        activity_patterns = [
            r'what.*activity',
            r'what.*can.*do',
            r'suggest.*activity',
            r'activities.*for',
            r'help.*with',
            r'need.*activity',
            r'recommend.*activity',
        ]
        
        is_activity_query = any(re.search(pattern, message_lower) for pattern in activity_patterns)
        
        # Also check intent
        if intent in ['activity_query', 'activity_request', 'activity_suggestion']:
            return True
            
        return is_activity_query
    
    def _extract_reason(self, message: str) -> Dict[str, str]:
        """
        Extract reason and mood from the message using LLM.
        Falls back to keyword matching if LLM unavailable.
        """
        # Try LLM-based extraction first
        if self.llm_service.is_available():
            try:
                return self._extract_reason_with_llm(message)
            except (LLMUnavailableError, LLMAPIError) as e:
                logger.warning(f"LLM extraction failed: {e}, using keyword fallback")
        
        # Fallback to keyword matching
        return self._extract_reason_with_keywords(message)
    
    def _extract_reason_with_llm(self, message: str) -> Dict[str, str]:
        """
        Use LLM to extract reason and mood from user message.
        This handles ANY input without keyword matching.
        """
        prompt = f"""You are analyzing a user's wellness query to determine what kind of activities to suggest.

User said: "{message}"

Determine:
1. Their primary wellness concern/goal
2. An appropriate mood emoji

Wellness Categories:
- weight_management: weight gain/loss, body image, weight control
- nutrition: diet, food, eating habits, meals, calories, healthy eating
- exercise: workout, fitness, physical activity, building muscle, cardio
- stress: stress, pressure, overwhelm, tension
- anxiety: worry, nervousness, fear, panic
- sleep: insomnia, tired, rest, sleep problems
- energy: fatigue, low energy, exhaustion, feeling drained
- mood: general mood improvement, happiness, sadness, emotional wellbeing
- focus: concentration, productivity, mental clarity, attention
- calm: relaxation, peace, unwinding, destressing
- pain: physical discomfort, aches, soreness
- general: unclear or multiple concerns

Mood Emojis:
😟 - stressed/worried
😰 - anxious/overwhelmed  
😴 - tired/sleepy
🤔 - thinking/planning
😊 - happy/positive
😌 - calm/relaxed
😢 - sad/down
😠 - angry/frustrated
🥗 - nutrition/food related
💪 - fitness/strength related
⚖️ - weight/balance related

Respond ONLY with valid JSON (no markdown, no code blocks):
{{"reason": "category_name", "mood": "emoji"}}"""

        try:
            # Use call_structured for guaranteed JSON response
            result = self.llm_service.call_structured(
                prompt=prompt,
                json_schema={
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"},
                        "mood": {"type": "string"}
                    },
                    "required": ["reason", "mood"],
                    "additionalProperties": False
                },
                schema_name="reason_extraction",
                temperature=0.2,
                max_tokens=50
            )
            
            logger.info(f"✅ LLM extracted - reason: {result['reason']}, mood: {result['mood']}")
            return {
                'mood': result['mood'],
                'reason': result['reason']
            }
            
        except Exception as e:
            logger.error(f"❌ LLM extraction error: {e}")
            raise LLMAPIError(f"Failed to extract reason: {e}")
    
    def _extract_reason_with_keywords(self, message: str) -> Dict[str, str]:
        """
        Fallback keyword-based extraction (when LLM unavailable).
        This is the old method - kept for reliability.
        """
        message_lower = message.lower()
        
        # Check for keywords in the message
        for keyword, mapping in self.REASON_MAPPING.items():
            if keyword in message_lower:
                logger.info(f"📝 Keyword match: {keyword} -> {mapping['reason']}")
                return mapping
        
        # Default to general wellness
        logger.info("📝 No keyword match, defaulting to 'general'")
        return {'mood': '😊', 'reason': 'general'}
    
    def process(
        self,
        message: str,
        user_id: int,
        state: WorkflowState,
        intent: Optional[str] = None
    ) -> WorkflowResponse:
        """Process activity query and return smart suggestions"""
        
        logger.info(f"ActivityQueryWorkflow processing: {message}")
        
        message_lower = message.lower().strip()
        
        # Check if user wants to START a specific activity (not ask for suggestions)
        start_activity_patterns = [
            r'^i want to (meditate|meditation|breathe|breathing|stretch|stretching|journal|journaling|relax|yoga|exercise|workout)',
            r'^start (meditate|meditation|breathe|breathing|stretch|stretching|journal|journaling|relax|yoga|exercise|workout)',
            r'^starting ',
            r'^(meditation|breathing|stretching|journaling|yoga|exercise|workout|hydrate|music)$'  # Single word activity name
        ]
        
        is_starting_activity = any(re.search(pattern, message_lower) for pattern in start_activity_patterns)
        
        if is_starting_activity:
            # User wants to START an activity, not get suggestions
            # Extract the activity name
            activity_name = None
            for pattern in start_activity_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if match.groups():
                        activity_name = match.group(1)
                    else:
                        # Single word match
                        activity_name = message_lower
                    break
            
            if not activity_name:
                activity_name = message_lower
            
            logger.info(f"User wants to start activity: {activity_name}")
            
            # Return encouragement message
            encouragements = {
                'meditation': "Great choice! Take a few moments to center yourself. 🧘",
                'meditate': "Great choice! Take a few moments to center yourself. 🧘",
                'breathing': "Perfect! Let's focus on your breath. 🌬️",
                'breathe': "Perfect! Let's focus on your breath. 🌬️",
                'stretching': "Nice! Gentle stretches can really help. 🤸",
                'stretch': "Nice! Gentle stretches can really help. 🤸",
                'journaling': "Excellent! Writing can be very therapeutic. ✍️",
                'journal': "Excellent! Writing can be very therapeutic. ✍️",
                'yoga': "Wonderful! Yoga is great for mind and body. 🧘",
                'exercise': "Awesome! Let's get moving! 💪",
                'workout': "Awesome! Let's get moving! 💪",
                'relax': "Good idea! Take some time to unwind. 😌",
                'hydrate': "Smart! Staying hydrated is important. 💧",
                'music': "Nice! Music can really lift your mood. 🎵"
            }
            
            encouragement = encouragements.get(activity_name, f"Great! Enjoy your {activity_name}. 😊")
            
            return WorkflowResponse(
                message=f"{encouragement}\n\nHow are you feeling now?",
                ui_elements=['emoji_selector'],
                extra_data={},
                completed=True,  # Complete the workflow!
                next_state=ConversationState.IDLE
            )
        
        # User is asking for suggestions (not starting a specific activity)
        # Extract reason and mood from message
        extracted = self._extract_reason(message)
        mood_emoji = extracted['mood']
        reason = extracted['reason']
        
        logger.info(f"Extracted - mood: {mood_emoji}, reason: {reason}")
        
        # Build user context
        context = build_context(user_id)
        
        # Get smart suggestions
        suggestions = get_smart_suggestions(
            mood_emoji=mood_emoji,
            reason=reason,
            context=context,
            count=5  # Get up to 5 suggestions
        )
        
        logger.info(f"Got {len(suggestions)} suggestions")
        
        # Create response message
        if reason == 'general':
            response_message = "Here are some activities that might help:"
        else:
            response_message = f"Here are some activities that might help with {reason}:"
        
        # Keep workflow active so user can click on activity buttons
        # Don't complete the workflow - let activity_logging handle the button clicks
        from .unified_state import ConversationState
        return WorkflowResponse(
            message=response_message,
            ui_elements=['activity_buttons'],
            extra_data={'suggestions': suggestions},
            completed=False,
            next_state=ConversationState.WORKFLOW_ACTIVE
        )
