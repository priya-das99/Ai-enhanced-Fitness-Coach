"""
Guardrails System for Fitness Chat Assistant
Ensures the assistant stays focused on fitness, wellness, and health activities
Includes conversation depth tracking to prevent infinite information loops
"""

import re
import logging
from typing import Tuple, Optional, Dict
from enum import Enum
from .conversation_depth_tracker import TopicDetector, ActionNudgeGenerator

logger = logging.getLogger(__name__)


class GuardrailViolationType(Enum):
    """Types of guardrail violations"""
    OUT_OF_SCOPE = "out_of_scope"
    MEDICAL_ADVICE = "medical_advice"
    CRISIS_SITUATION = "crisis_situation"
    PERSONAL_INFO_REQUEST = "personal_info_request"
    TECHNICAL_SUPPORT = "technical_support"
    ENTERTAINMENT = "entertainment"
    COMMERCIAL = "commercial"
    INAPPROPRIATE = "inappropriate"


class FitnessGuardrails:
    """
    Guardrails to keep the assistant focused on fitness and wellness
    Includes depth tracking to nudge users toward action
    """
    
    def __init__(self, smart_suggestions=None):
        """Initialize with optional smart suggestions for depth nudges"""
        self.topic_detector = TopicDetector()
        self.nudge_generator = ActionNudgeGenerator(smart_suggestions) if smart_suggestions else None
    
    # Core functionality scope
    ALLOWED_TOPICS = {
        'fitness', 'exercise', 'workout', 'running', 'walking', 'yoga', 'gym',
        'health', 'wellness', 'mood', 'feeling', 'emotion', 'stress', 'anxiety',
        'sleep', 'rest', 'meditation', 'mindfulness', 'breathing',
        'nutrition', 'food', 'meal', 'eating', 'diet', 'water', 'hydration',
        'weight', 'activity', 'steps', 'calories', 'energy',
        'challenge', 'goal', 'progress', 'achievement', 'motivation',
        'tired', 'energetic', 'relaxed', 'happy', 'sad', 'angry'
    }
    
    # Medical advice indicators (we should NOT provide medical advice)
    MEDICAL_ADVICE_PATTERNS = [
        r'\b(diagnose|diagnosis|disease|illness|sick|infection|virus|bacteria)\b',
        r'\b(medicine|medication|prescription|drug|pill|tablet|dose)\b',
        r'\b(doctor|physician|hospital|clinic|emergency|ambulance)\b',
        r'\b(symptom|pain|ache|fever|cough|cold|flu|covid)\b',
        r'\b(blood pressure|heart rate|pulse|cholesterol|diabetes|cancer)\b',
        r'\b(injury|broken|fracture|sprain|strain|torn|surgery)\b',
        r'\b(pregnant|pregnancy|breastfeeding|menstrual)\b',
        r'\b(allergy|allergic|asthma|condition|disorder)\b',
    ]
    
    # Crisis situation indicators (need specialized response)
    CRISIS_PATTERNS = [
        r'\b(suicide|suicidal|kill myself|end my life|want to die|don\'t want to live)\b',
        r'\b(self.harm|self harm|cut myself|hurt myself|harm myself)\b',
        r'\b(abuse|abused|violence|violent|assault|attacked)\b',
        r'\b(emergency|urgent|critical|dying)\b',
        r'\b(help me (now|please|immediately))\b',
    ]
    
    # Out of scope topics
    OUT_OF_SCOPE_PATTERNS = {
        'weather': r'\b(weather|temperature|rain|snow|sunny|cloudy|forecast)\b',
        'news': r'\b(news|headline|current events|breaking)\b',
        'politics': r'\b(politics|political|election|government|president|vote)\b',
        'entertainment': r'\b(movie|film|tv show|series|actor|celebrity|music|song|concert)\b',
        'technology': r'\b(computer|laptop|phone|software|app|bug|error|crash|install)\b',
        'finance': r'\b(stock|crypto|bitcoin|investment|trading|market|price)\b',
        'shopping': r'\b(buy|purchase|shop|store|amazon|price|discount|sale)\b',
        'travel': r'\b(vacation|holiday|trip|flight|hotel|booking|travel)\b',
        'education': r'\b(homework|assignment|exam|test|study|school|college|university)\b',
        'work': r'\b(job|career|interview|resume|salary|boss|colleague|meeting)\b',
        'relationships': r'\b(dating|relationship|boyfriend|girlfriend|marriage|divorce)\b',
        'legal': r'\b(lawyer|attorney|legal|lawsuit|court|judge)\b',
    }
    
    # Personal information requests (we should not ask for or store)
    PERSONAL_INFO_PATTERNS = [
        r'\b(social security|ssn|credit card|bank account|password)\b',
        r'\b(address|home address|street|zip code|postal code)\b',
        r'\b(phone number|telephone|mobile number)\b',
        r'\b(email address|email me)\b',
        r'\b(full name|first name|last name|date of birth|birthday)\b',
    ]
    
    # Entertainment/joke requests
    ENTERTAINMENT_PATTERNS = [
        r'\b(tell me a joke|make me laugh|funny|humor|comedy)\b',
        r'\b(story|tale|once upon a time)\b',
        r'(let\'s play|play a game|game time|wanna play)',
        r'\b(sing|song|poem|rhyme)\b',
    ]
    
    # Commercial/promotional content
    COMMERCIAL_PATTERNS = [
        r'\b(buy|purchase|sale|discount|promo|coupon)\b',
        r'\b(product|service|offer|deal|price)\b',
        r'\b(advertisement|sponsor|affiliate)\b',
    ]
    
    def check_message(self, message: str) -> Tuple[bool, Optional[GuardrailViolationType], Optional[str]]:
        """
        Check if message violates any guardrails
        
        Returns:
            (is_allowed, violation_type, suggested_response)
        """
        if not message or not message.strip():
            return True, None, None
        
        message_lower = message.lower().strip()
        
        # 1. Check for crisis situations (highest priority)
        for pattern in self.CRISIS_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"Guardrail: Crisis situation detected")
                return False, GuardrailViolationType.CRISIS_SITUATION, self._get_crisis_response()
        
        # 2. Check for medical advice requests
        for pattern in self.MEDICAL_ADVICE_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.info(f"Guardrail: Medical advice request detected")
                return False, GuardrailViolationType.MEDICAL_ADVICE, self._get_medical_disclaimer()
        
        # 3. Check for personal information requests
        for pattern in self.PERSONAL_INFO_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.info(f"Guardrail: Personal info request detected")
                return False, GuardrailViolationType.PERSONAL_INFO_REQUEST, self._get_privacy_response()
        
        # 4. Check if it's a question/request (not just casual mention)
        is_question_or_request = any(word in message_lower for word in [
            'what', 'how', 'when', 'where', 'why', 'who', 'which',
            'can you', 'could you', 'will you', 'would you',
            'tell me', 'show me', 'give me', 'help me with',
            'let\'s', 'lets', 'want to', 'wanna',
            '?'
        ])
        
        if is_question_or_request:
            # 5. Check for out-of-scope topics
            for topic, pattern in self.OUT_OF_SCOPE_PATTERNS.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(f"Guardrail: Out-of-scope topic detected: {topic}")
                    return False, GuardrailViolationType.OUT_OF_SCOPE, self._get_scope_response()
            
            # 6. Check for entertainment requests
            for pattern in self.ENTERTAINMENT_PATTERNS:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(f"Guardrail: Entertainment request detected")
                    return False, GuardrailViolationType.ENTERTAINMENT, self._get_entertainment_response()
            
            # 7. Check for commercial content
            for pattern in self.COMMERCIAL_PATTERNS:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(f"Guardrail: Commercial content detected")
                    return False, GuardrailViolationType.COMMERCIAL, self._get_commercial_response()
        
        # Message is allowed
        return True, None, None
    
    @staticmethod
    def _get_crisis_response() -> str:
        """Response for crisis situations"""
        return (
            "I'm concerned about what you're sharing. If you're in crisis or need immediate help, "
            "please reach out to a crisis helpline or emergency services:\n\n"
            "🆘 National Crisis Hotline: 988 (US)\n"
            "🆘 Emergency Services: 911\n\n"
            "I'm here to support your wellness journey, but I'm not equipped to handle crisis situations. "
            "Please talk to a mental health professional who can provide the help you need."
        )
    
    @staticmethod
    def _get_medical_disclaimer() -> str:
        """Response for medical advice requests"""
        return (
            "I appreciate your question, but I'm not qualified to provide medical advice or diagnose health conditions. "
            "For medical concerns, please consult with a healthcare professional.\n\n"
            "I can help you track your fitness activities, mood, and wellness habits. "
            "Would you like to log an activity or check your progress? 🏃‍♀️💪"
        )
    
    @staticmethod
    def _get_privacy_response() -> str:
        """Response for personal information requests"""
        return (
            "For your privacy and security, I don't collect or store personal information like "
            "addresses, phone numbers, or financial details.\n\n"
            "I'm here to help you track your fitness activities and wellness. "
            "What would you like to log today? 🎯"
        )
    
    @staticmethod
    def _get_scope_response() -> str:
        """Response for out-of-scope topics"""
        return (
            "I appreciate your question! However, I'm specifically designed to help with "
            "your wellness and fitness journey. 🏃‍♀️💪\n\n"
            "I can help you:\n"
            "• Track activities (exercise, sleep, meals, water)\n"
            "• Log your mood and feelings\n"
            "• Set and monitor fitness goals\n"
            "• Get wellness suggestions\n\n"
            "What would you like to focus on today?"
        )
    
    @staticmethod
    def _get_entertainment_response() -> str:
        """Response for entertainment requests"""
        return (
            "I'd love to keep things fun, but I'm focused on helping you with your fitness and wellness goals! 💪\n\n"
            "How about we make your wellness journey more enjoyable instead? "
            "Would you like to set a new challenge or track an activity?"
        )
    
    @staticmethod
    def _get_commercial_response() -> str:
        """Response for commercial content"""
        return (
            "I'm here to support your wellness journey, not for commercial purposes. 🎯\n\n"
            "Let's focus on your fitness goals! Would you like to log an activity or check your progress?"
        )
    
    @staticmethod
    def is_fitness_related(message: str) -> bool:
        """
        Quick check if message is fitness/wellness related
        """
        message_lower = message.lower()
        
        # Check if any allowed topic is mentioned
        for topic in FitnessGuardrails.ALLOWED_TOPICS:
            if topic in message_lower:
                return True
        
        return False
    
    @staticmethod
    def get_capabilities_message() -> str:
        """Get message describing what the assistant can do"""
        return (
            "I'm your fitness and wellness assistant! Here's what I can help you with:\n\n"
            "📊 Activity Tracking:\n"
            "• Exercise and workouts\n"
            "• Sleep duration\n"
            "• Water intake\n"
            "• Meals and nutrition\n"
            "• Weight tracking\n\n"
            "😊 Mood & Wellness:\n"
            "• Log your feelings and emotions\n"
            "• Track stress and anxiety levels\n"
            "• Get wellness suggestions\n\n"
            "🎯 Goals & Challenges:\n"
            "• Set fitness goals\n"
            "• Join wellness challenges\n"
            "• Monitor your progress\n\n"
            "What would you like to do today?"
        )
    
    async def check_conversation_depth(
        self,
        message: str,
        user_id: int,
        depth_tracker,  # ConversationDepthTracker from WorkflowState
        context: dict
    ) -> Optional[dict]:
        """
        Check if conversation depth limit reached.
        Returns nudge response if limit hit, None otherwise.
        
        This is called AFTER template check, BEFORE LLM.
        """
        # Detect topic (rule-based, cheap)
        topic = self.topic_detector.detect_topic(message)
        
        # If no topic match, don't apply depth tracking
        if topic is None:
            return None
        
        # Check current depth
        info_count = depth_tracker.get_info_count(topic)
        
        # If at limit
        if info_count >= 3:
            # Check for override request
            if (depth_tracker.is_override_request(message) and 
                depth_tracker.can_override(topic)):
                # Allow one more explanation
                depth_tracker.use_override(topic)
                logger.info(f"User {user_id}: Override allowed for topic '{topic}'")
                return {
                    "allow_llm": True,
                    "is_final": True,
                    "topic": topic
                }
            
            # Generate action nudge with smart suggestions
            if self.nudge_generator:
                nudge = await self.nudge_generator.generate_nudge_with_activities(
                    user_id=user_id,
                    topic=topic,
                    context=context
                )
            else:
                # Fallback if no smart suggestions available
                nudge = {
                    "response": f"Let's put this into action! Ready to try some {topic} activities?",
                    "suggestions": [],
                    "buttons": [{"text": "Maybe later", "action": "dismiss"}],
                    "metadata": {
                        "source": "depth_nudge",
                        "nudge_reason": "depth_limit",
                        "topic": topic,
                        "counts_toward_depth": False
                    }
                }
            
            logger.info(f"User {user_id}: Depth limit reached for topic '{topic}', nudging to action")
            
            return {
                "should_nudge": True,
                "nudge_response": nudge,
                "topic": topic
            }
        
        return None
    
    def record_informational_response(self, depth_tracker, topic: str):
        """Call after bot gives informational response"""
        depth_tracker.record_informational_response(topic)
    
    def reset_topic_depth(self, depth_tracker, topic: str):
        """Call when user completes action"""
        depth_tracker.reset_topic(topic)


def apply_guardrails(message: str, guardrails_instance=None) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Apply guardrails to a message
    
    Returns:
        (is_allowed, response_override, metadata)
    """
    if guardrails_instance is None:
        guardrails_instance = FitnessGuardrails()
    
    is_allowed, violation_type, suggested_response = guardrails_instance.check_message(message)
    
    if not is_allowed:
        metadata = {
            'guardrail_triggered': True,
            'violation_type': violation_type.value if violation_type else None,
            'original_message_length': len(message)
        }
        return False, suggested_response, metadata
    
    return True, None, None


def get_scope_reminder() -> str:
    """Get a friendly reminder about the assistant's scope"""
    return (
        "Just a reminder: I'm here to help with your fitness and wellness journey! 🏃‍♀️\n"
        "I can track activities, log moods, and support your health goals."
    )
