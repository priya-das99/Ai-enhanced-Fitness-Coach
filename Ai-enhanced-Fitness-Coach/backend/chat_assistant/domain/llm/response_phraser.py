# chat_assistant/domain/llm/response_phraser.py
# Natural language phrasing using centralized LLM service
# With selective conversation context passing

import logging
from typing import Optional
from chat_assistant.llm_service import get_llm_service, LLMUnavailableError, LLMAPIError
from chat_assistant.context_detector import needs_conversation_context, get_recent_topic_from_state

logger = logging.getLogger(__name__)

class ResponsePhraser:
    """
    Uses centralized LLM service to generate natural, human-like responses.
    
    Rules:
    - Max 3 sentences
    - Human, warm tone
    - No medical advice
    - Supportive and encouraging
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def phrase_general_response(self, user_message: str, conversation_context: str = None, user_context: dict = None) -> str:
        """
        Generate a general conversational response with context awareness.
        
        Args:
            user_message: User's current message
            conversation_context: Recent conversation history
            user_context: User's recent activities and fitness data
            
        Returns:
            Natural language response (max 3 sentences)
        """
        try:
            # Build user context section
            context_section = ""
            if conversation_context:
                context_section = f"\nRecent conversation:\n{conversation_context}\n"
            
            # Add user fitness context
            user_info = ""
            if user_context:
                recent_activities = user_context.get('recent_activities', [])
                if recent_activities:
                    activities_str = ", ".join([a.get('activity_type', 'activity') for a in recent_activities[:3]])
                    user_info = f"\nUser's recent activities: {activities_str}"
            
            prompt = f"""
You're a friendly fitness coach and wellness buddy who talks like a real friend.

Your personality:
- Supportive and encouraging, never judgmental
- Knowledgeable about fitness, exercise, nutrition, and wellness
- Conversational and warm, not robotic or formal
- Proactive - suggest workouts, give tips, share advice
- Remember context - reference what the user mentioned before

Your main jobs:
1. Answer fitness questions (exercises, workouts, nutrition, recovery)
2. Provide workout suggestions based on user's situation
3. Give exercise form tips and guidance
4. Offer motivation and celebrate progress
5. Help track activities naturally through conversation
6. Understand when users mention activities and acknowledge them
{context_section}{user_info}

User message:
"{user_message}"

Respond naturally as a fitness coach friend (2-3 sentences). Be specific and helpful.

Examples:
- If they mention an activity: "Nice work on that run! How far did you go? Make sure to stretch after."
- If they ask about exercise: "Pushups are great for chest! Keep your core tight and elbows at 45 degrees."
- If they're tired: "Rest is important too! Maybe try some light stretching or take a recovery day."
- If they ask what to do: "What's your goal today? Cardio, strength, or something chill?"

Response:
"""
            
            text = self.llm_service.call(
                prompt=prompt,
                system_message="You're a knowledgeable fitness coach who talks like a friend. Be specific, helpful, and encouraging.",
                temperature=0.7,
                max_tokens=100
            )
            
            # Ensure max 3 sentences
            sentences = text.split('.')
            if len(sentences) > 3:
                text = '. '.join(sentences[:3]) + '.'
            
            logger.info(f"🤖 Phrased response: {text[:50]}...")
            return text
            
        except (LLMUnavailableError, LLMAPIError) as e:
            logger.warning(f"LLM unavailable, using fallback: {e}")
            return self._fallback_general_response()
        except Exception as e:
            logger.error(f"Response phrasing failed: {e}")
            return self._fallback_general_response()
    
    def phrase_acknowledgment(self, context: str) -> str:
        """
        Generate an acknowledgment response.
        
        Args:
            context: Context for acknowledgment (e.g., "mood logged", "activity saved")
            
        Returns:
            Natural acknowledgment
        """
        try:
            prompt = f"""
You are MoodCapture, a wellness tracking assistant.

Generate a short, natural acknowledgment (1 sentence) for: "{context}"

Rules:
- Sound human, not robotic.
- Encouraging but not exaggerated.
- Avoid overusing exclamation marks.
- Vary wording.

Examples:
- "Got it. I've logged that for you."
- "Nice work, that's saved."
- "Thanks, I've added it."

Response:
"""
            
            text = self.llm_service.call(
                prompt=prompt,
                system_message="You are a supportive wellness assistant.",
                temperature=0.5,
                max_tokens=30
            )
            
            return text
            
        except (LLMUnavailableError, LLMAPIError) as e:
            logger.warning(f"LLM unavailable, using fallback: {e}")
            return self._fallback_acknowledgment(context)
        except Exception as e:
            logger.error(f"Acknowledgment phrasing failed: {e}")
            return self._fallback_acknowledgment(context)
    
    def _fallback_general_response(self) -> str:
        """Fallback general response"""
        import random
        responses = [
            "Hey! I'm your fitness buddy. What's your goal today?",
            "Hi there! Want to work out, track an activity, or just chat about fitness?",
            "What's up? I can help with workouts, exercises, or tracking your activities.",
            "Hey! How's your fitness journey going? I'm here to help!"
        ]
        return random.choice(responses)
    
    def _build_contextual_messages(self, user_message: str, state) -> list:
        """
        Build messages array with conversation history and context.
        Uses STRUCTURED state, not text extraction.
        """
        messages = []
        
        # 1. Enhanced system message with capped context
        system_content = self._build_system_message_with_context(state)
        messages.append({"role": "system", "content": system_content})
        
        # 2. Recent conversation history (last 6 messages = 3 exchanges)
        history = state.get_conversation_history(limit=6)
        if history:
            messages.extend(history)
        
        # 3. Current message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _build_system_message_with_context(self, state) -> str:
        """
        Build system message with user context.
        CAPPED at 200 characters to keep prompts stable.
        """
        base = "You are MoodCapture, a calm and supportive wellness assistant."
        
        context_parts = []
        
        # Get recent topic from STRUCTURED state (not text extraction)
        recent_topic = get_recent_topic_from_state(state)
        if recent_topic:
            context_parts.append(f"Current topic: {recent_topic}")
        
        # Add semantic summary if available
        if hasattr(state, 'session_summary') and state.session_summary:
            summary_text = state.session_summary.to_prompt()
            if summary_text and len(summary_text) < 100:
                context_parts.append(summary_text)
        
        # Build final system message with cap
        if context_parts:
            context_str = " | ".join(context_parts)
            # Cap at 150 chars for context
            if len(context_str) > 150:
                context_str = context_str[:147] + "..."
            
            full_message = f"{base}\n\nContext: {context_str}"
            
            # Hard cap at 200 chars total
            if len(full_message) > 200:
                return base  # Fall back to base if too long
            
            return full_message
        
        return base
    
    def _fallback_acknowledgment(self, context: str) -> str:
        """Fallback acknowledgment"""
        import random
        if 'mood' in context.lower():
            responses = ["Got it!", "Logged!", "Thanks for sharing", "Noted!"]
            return random.choice(responses)
        elif 'activity' in context.lower():
            responses = ["Nice!", "Logged!", "Got it!", "Awesome!"]
            return random.choice(responses)
        else:
            responses = ["Got it!", "Thanks!", "Cool!", "Noted!"]
            return random.choice(responses)


# Global instance
_response_phraser = None

def get_response_phraser() -> ResponsePhraser:
    """Get or create global ResponsePhraser instance"""
    global _response_phraser
    if _response_phraser is None:
        _response_phraser = ResponsePhraser()
    return _response_phraser



def phrase_activity_suggestion(
    state: str,
    activity_titles: list,
    category: str = 'general'
) -> str:
    """
    Generate natural response mentioning EXACT activities from suggestions
    Args:
        state: User's mood/state ('bored', 'stressed', etc.)
        activity_titles: ["Stretching", "Meditation", "Breathing"]
        category: Mood category for tone adjustment (optional)
    Returns:
        Natural response mentioning 1-2 activities from the list
    Key Features:
    - LLM receives ONLY: state + max 2 titles + tone
    - Validates that at least one title appears in response
    - Falls back to template if validation fails
    """
    if not activity_titles:
        return "I hear you. What would help you feel better?"
    
    # Take only first 2 activities for natural phrasing
    top_activities = activity_titles[:2]
    
    # Determine tone based on mood state
    tone_map = {
        'stressed': 'empathetic and calming',
        'anxious': 'reassuring and gentle', 
        'sad': 'supportive and understanding',
        'angry': 'understanding and grounding',
        'bored': 'energizing and encouraging',
        'tired': 'gentle and supportive',
        'restless': 'channeling and focusing',
        'lonely': 'warm and connecting',
        'happy': 'celebratory and momentum-building',
        'excited': 'enthusiastic and channeling',
        'calm': 'maintaining and deepening',
        'energetic': 'directing and purposeful'
    }
    tone = tone_map.get(state, 'supportive and warm')
    
    # LLM prompt (minimal, focused)
    prompt = f"""User is feeling {state}. 
Suggest trying one or two of these activities: {', '.join(top_activities)}.
Tone: {tone} 
Length: Max 2 sentences
Style: Natural, conversational
Must mention at least one activity by name
Response:"""
    
    try:
        llm = get_llm_service()
        response = llm.call(
            prompt=prompt,
            max_tokens=50,
            temperature=0.7
        )
        response = response.strip()
        
        # CRITICAL VALIDATION: Ensure at least one title appears
        if not any(title.lower() in response.lower() for title in top_activities):
            logger.warning(f"⚠️  LLM response doesn't mention activities: {response}")
            # Fallback to template
            return f"I hear you. Want to try {top_activities[0].lower()}?"
        
        logger.info(f"✅ Generated matched response for {state}: {response[:50]}...")
        return response
        
    except Exception as e:
        logger.error(f"❌ LLM phrasing failed: {e}")
        # Fallback to template
        if len(top_activities) >= 2:
            return f"I hear you. Want to try {top_activities[0].lower()} or {top_activities[1].lower()}?"
        else:
            return f"I hear you. Want to try {top_activities[0].lower()}?"



def phrase_contextual_suggestion(
    user_message: str,
    feeling: str,
    activities: list,
    tone: str,
    context_summary: dict = None,
    pattern_insight: str = None,
    triggered_insights: list = None  # NEW: Structured insight objects
) -> str:
    """
    Generate contextual response with activity suggestions
    
    Args:
        user_message: Original user message ("I am tired")
        feeling: Extracted feeling ("tired", "exhausted")
        activities: List of activity names ["Stretching", "Meditation"]
        tone: Tone to use ("gentle and supportive", "empathetic and calming")
        context_summary: Optional context (intent, intensity)
        pattern_insight: Optional pattern insight text (DEPRECATED - use triggered_insights)
        triggered_insights: NEW - List of structured insight dicts from InsightGenerator
        
    Returns:
        Natural response introducing activities with context
        
    Example:
        "I hear you. When you're tired, these activities can help recharge."
    """
    if not activities:
        return "I hear you. What would help you feel better?"
    
    # NEW: Build insight section from structured insights (deterministic)
    insight_section = ""
    if triggered_insights and len(triggered_insights) > 0:
        # Take only the first (highest priority) insight
        insight = triggered_insights[0]
        insight_type = insight.get('insight_type')
        data = insight.get('data', {})
        
        # Convert structured insight to natural language hint for LLM
        if insight_type == 'prolonged_stress_pattern':
            days = data.get('consecutive_days', 0)
            insight_section = f"Pattern: User has been stressed for {days} consecutive days"
        
        elif insight_type == 'activity_decline':
            drop_pct = data.get('drop_percentage', 0)
            insight_section = f"Pattern: User's activity has dropped {drop_pct}% this week"
        
        elif insight_type == 'proven_solution_available':
            activity_name = data.get('activity_name', 'an activity')
            times = data.get('times_done', 0)
            insight_section = f"Pattern: {activity_name} has worked well for user before ({times} times)"
        
        elif insight_type == 'stress_inactivity_cycle':
            days = data.get('stressed_days', 0)
            drop = data.get('activity_drop', 0)
            insight_section = f"Pattern: {days} days stressed + {drop}% activity drop (concerning cycle)"
        
        elif insight_type == 'activity_streak':
            streak = data.get('streak_days', 0)
            insight_section = f"Celebration: User has {streak}-day activity streak"
    
    # Fallback to legacy pattern_insight if no structured insights
    elif pattern_insight:
        insight_section = f"Pattern: {pattern_insight}"
    
    # Build prompt
    prompt = f"""You are MoodCapture, a supportive wellness assistant.

User said: "{user_message}"
Detected feeling: {feeling}
{insight_section}

We're about to suggest these activities to help:
{', '.join(activities)}

Generate a brief, {tone} response (1-2 sentences) that:
1. Acknowledges how they're feeling
2. {f"Naturally mentions the pattern (don't use percentages or numbers unless it sounds natural)" if insight_section else "Introduces the activity suggestions naturally"}

Examples for {tone} tone:
- "I hear you. When you're {feeling}, these activities can help recharge."
- "That sounds draining. I've noticed you've been feeling this way for a few days now."
- "Feeling {feeling}? Let's find something to help you feel better."

IMPORTANT:
- Keep it warm, brief, and natural
- Use ONE emoji if appropriate
- Don't sound analytical or data-driven
- Don't mention specific numbers unless natural
- Focus on support, not analysis

Response:"""
    
    try:
        llm = get_llm_service()
        response = llm.call(
            prompt=prompt,
            system_message=f"You are a supportive wellness assistant. Be {tone} and brief. Sound human, not analytical.",
            temperature=0.7,
            max_tokens=80
        )
        
        logger.info(f"✅ Generated contextual response: {response[:50]}...")
        return response.strip()
        
    except Exception as e:
        logger.error(f"❌ Contextual phrasing failed: {e}")
        # Fallback based on number of activities
        if len(activities) == 1:
            return f"Try {activities[0]} to feel better!"
        elif len(activities) == 2:
            return f"Try {activities[0]} or {activities[1]} to recharge!"
        else:
            return f"Here are some quick activities: {activities[0]}, {activities[1]}, or {activities[2]}. Which sounds good?"


def phrase_empathetic_response(
    user_message: str,
    mood_context: str = None
) -> str:
    """
    Generate empathetic response without activity suggestions
    
    Args:
        user_message: Original user message ("I am tired")
        mood_context: Optional mood context
        
    Returns:
        Warm, supportive response
        
    Example:
        "That sounds rough. Take it easy today 💙"
    """
    prompt = f"""You're a supportive friend responding to someone who said: "{user_message}"

Respond naturally and warmly (1-2 sentences) like you're texting a friend:

Examples:
- "That sounds rough. Take it easy today 💙"
- "Ugh, I feel you. Be kind to yourself 💙"  
- "That's tough. Make sure you rest when you can 💙"
- "I hear you. Take some time for yourself 💙"

Keep it natural and supportive. Use ONE emoji.

Response:"""
    
    try:
        llm = get_llm_service()
        response = llm.call(
            prompt=prompt,
            system_message="You're a supportive friend. Be natural and warm.",
            temperature=0.7,
            max_tokens=50
        )
        
        logger.info(f"✅ Generated empathetic response: {response[:50]}...")
        return response.strip()
        
    except Exception as e:
        logger.error(f"❌ Empathetic phrasing failed: {e}")
        return "That sounds tough. Take care of yourself! 💙"
