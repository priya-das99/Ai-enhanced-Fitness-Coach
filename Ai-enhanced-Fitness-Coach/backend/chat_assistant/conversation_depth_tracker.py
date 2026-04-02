"""
Conversation depth tracking to prevent infinite information loops.
Tracks informational responses per topic to nudge users toward action.

Key Design Principles:
- Only counts bot's informational responses (not user messages)
- Tracks per topic, not globally
- Allows one override per topic
- Resets when user takes action
"""

from typing import Optional, Dict
from datetime import datetime


class ConversationDepthTracker:
    """
    Tracks informational response depth per topic.
    Lives in WorkflowState (per-user session).
    """
    
    def __init__(self):
        # Track informational responses per topic
        self.topic_info_responses: Dict[str, int] = {}
        
        # Track if override used per topic
        self.topic_override_used: Dict[str, bool] = {}
        
        # Max informational responses before nudging to action
        self.max_info_responses = 3
        
    def record_informational_response(self, topic: str):
        """
        Call AFTER bot gives informational answer.
        Only call for actual explanations, not questions or confirmations.
        """
        current = self.topic_info_responses.get(topic, 0)
        self.topic_info_responses[topic] = current + 1
        
    def get_info_count(self, topic: str) -> int:
        """How many informational responses given for this topic"""
        return self.topic_info_responses.get(topic, 0)
        
    def should_nudge_to_action(self, topic: str) -> bool:
        """Check if depth limit reached"""
        return self.get_info_count(topic) >= self.max_info_responses
        
    def can_override(self, topic: str) -> bool:
        """Check if user can request one more explanation"""
        return not self.topic_override_used.get(topic, False)
        
    def use_override(self, topic: str):
        """Mark override as used for this topic"""
        self.topic_override_used[topic] = True
        
    def reset_topic(self, topic: str):
        """Reset when user takes action or switches topic"""
        self.topic_info_responses[topic] = 0
        self.topic_override_used[topic] = False
        
    def is_override_request(self, message: str) -> bool:
        """Detect if user is requesting more information"""
        override_phrases = [
            "just explain", "just tell me", "want to know",
            "more information", "explain more", "tell me more",
            "one more thing", "what else", "i want to know"
        ]
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in override_phrases)
    
    def get_state_summary(self) -> dict:
        """Get current state for debugging"""
        return {
            "topic_counts": self.topic_info_responses.copy(),
            "overrides_used": self.topic_override_used.copy(),
            "max_limit": self.max_info_responses
        }


class TopicDetector:
    """
    Rule-based topic detection (cheap, deterministic).
    Returns None for unmatched topics (no depth tracking).
    """
    
    # Action-eligible topics with keywords
    TOPIC_KEYWORDS = {
        "breathing": ["breath", "breathing", "breathe", "pranayama"],
        "sleep": ["sleep", "sleeping", "insomnia", "rest", "tired", "bed"],
        "exercise": ["exercise", "workout", "fitness", "training", "gym", "run"],
        "hydration": ["water", "hydration", "drink", "hydrated", "thirsty"],
        "meditation": ["meditate", "meditation", "mindfulness", "zen"],
        "nutrition": ["food", "eat", "nutrition", "diet", "meal", "hungry"],
        "stress": ["stress", "stressed", "anxiety", "anxious", "worried"],
        "energy": ["energy", "tired", "fatigue", "exhausted", "energetic"]
    }
    
    def detect_topic(self, message: str) -> Optional[str]:
        """
        Detect topic using rules first (0 tokens).
        Returns topic name or None.
        None = don't apply depth guardrails.
        """
        message_lower = message.lower()
        
        # Rule-based detection (95% of cases, 0 tokens)
        # Use word boundaries to avoid partial matches
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                # Check for word boundaries to avoid false matches
                # e.g., "eat" shouldn't match "weather"
                if f" {keyword} " in f" {message_lower} " or \
                   message_lower.startswith(keyword + " ") or \
                   message_lower.endswith(" " + keyword) or \
                   message_lower == keyword:
                    return topic
        
        # Return None for unmatched (don't track depth)
        # This prevents random questions from accumulating depth
        return None
    
    def get_supported_topics(self) -> list:
        """Get list of topics that support depth tracking"""
        return list(self.TOPIC_KEYWORDS.keys())


class ActionNudgeGenerator:
    """
    Generate action nudges with personalized activity buttons.
    Uses existing smart_suggestions.py system.
    """
    
    # Map topics to activity types
    TOPIC_TO_ACTIVITIES = {
        "breathing": ["breathing_exercise", "meditation", "mindfulness"],
        "sleep": ["sleep_log", "bedtime_routine", "relaxation"],
        "exercise": ["quick_workout", "stretching", "cardio", "yoga"],
        "hydration": ["water_log", "hydration_reminder"],
        "meditation": ["guided_meditation", "breathing_exercise"],
        "nutrition": ["meal_log", "nutrition_tips"],
        "stress": ["breathing_exercise", "meditation", "relaxation"],
        "energy": ["quick_workout", "stretching", "water_log"]
    }
    
    def __init__(self, smart_suggestions):
        self.smart_suggestions = smart_suggestions
        
    async def generate_nudge_with_activities(
        self,
        user_id: int,
        topic: str,
        context: dict
    ) -> dict:
        """
        Generate friendly nudge with personalized activity buttons.
        """
        
        # Get personalized activities from smart suggestions
        activities = await self._get_activities_for_topic(
            user_id, topic, context
        )
        
        # Generate contextual nudge message
        nudge_message = self._get_nudge_message(topic, context)
        
        return {
            "response": nudge_message,
            "suggestions": activities,  # Activity action buttons
            "buttons": [
                {"text": "Maybe later", "action": "dismiss"}
            ],
            "metadata": {
                "source": "depth_nudge",
                "nudge_reason": "depth_limit",
                "topic": topic,
                "counts_toward_depth": False
            }
        }
    
    async def _get_activities_for_topic(
        self,
        user_id: int,
        topic: str,
        context: dict
    ) -> list:
        """Get top 3 personalized activities for topic"""
        
        activity_types = self.TOPIC_TO_ACTIVITIES.get(topic, [])
        
        if not activity_types:
            return []
        
        # Use existing smart suggestion system
        # This already considers:
        # - User behavior history
        # - Time of day
        # - Past preferences
        # - Engagement patterns
        suggestions = await self.smart_suggestions.generate_suggestions(
            user_id=user_id,
            context=context,
            activity_filter=activity_types,
            limit=3
        )
        
        return suggestions
    
    def _get_nudge_message(self, topic: str, context: dict) -> str:
        """Generate friendly, contextual nudge message"""
        
        # Extract user concerns from context
        user_concern = context.get("user_concern", "general")
        
        # Contextual nudges per topic
        nudges = {
            "breathing": {
                "stress": "I can tell stress is on your mind. Breathing exercises work best when you actually do them. Ready to try?",
                "focus": "You mentioned focus - let's do a quick breathing session to help with that right now.",
                "general": "You're asking great questions! The best way to understand breathing exercises is by experiencing one. Let's try together."
            },
            "sleep": {
                "tired": "Since you're feeling tired, let's track your sleep so I can spot patterns and help.",
                "insomnia": "Sleep tracking will help us identify what's affecting your rest. Let's start tonight.",
                "general": "Let's move from talking about sleep to actually tracking it. Ready?"
            },
            "exercise": {
                "energy": "Exercise will boost that energy! Let's start with something quick and easy.",
                "beginner": "Perfect time to start! I'll guide you through a simple session.",
                "general": "Ready to move from planning to action? Let's do a quick session together."
            },
            "hydration": {
                "general": "Let's track your water intake today so I can help you stay hydrated."
            },
            "meditation": {
                "general": "Meditation is best experienced, not explained. Ready for a guided session?"
            },
            "nutrition": {
                "general": "Let's log your meals so I can give you personalized nutrition insights."
            },
            "stress": {
                "general": "I can see stress management is important to you. Let's try a quick stress-relief activity."
            },
            "energy": {
                "general": "Let's boost that energy! Here are some quick activities that can help."
            }
        }
        
        topic_nudges = nudges.get(topic, {})
        return topic_nudges.get(user_concern, 
            "Let's put this into action! Here are some options based on your preferences:")
