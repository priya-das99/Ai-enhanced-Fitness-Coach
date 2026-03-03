"""
LLM Insight Generator
Generates natural, empathetic insight messages using LLM
"""

from chat_assistant.llm_service import get_llm_service
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LLMInsightGenerator:
    """Generate natural insights using LLM"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.message_cache = {}
    
    def generate_insight_message(
        self, 
        pattern_type: str,
        pattern_data: Dict,
        user_context: Dict,
        priority: str = 'medium'
    ) -> str:
        """
        Generate natural, empathetic message for a pattern
        
        Args:
            pattern_type: Type of pattern (e.g., 'stress_inactivity_cycle')
            pattern_data: Pattern details
            user_context: User context (baseline, best activities, etc.)
            priority: 'high', 'medium', or 'low'
        
        Returns:
            Natural language message
        """
        
        # Check cache for common patterns (except high priority)
        if priority != 'high':
            cache_key = self._get_cache_key(pattern_type, pattern_data)
            if cache_key in self.message_cache:
                logger.info(f"Using cached message for pattern: {pattern_type}")
                return self.message_cache[cache_key]
        
        # Build prompt
        prompt = self._build_prompt(pattern_type, pattern_data, user_context, priority)
        
        try:
            # Call LLM
            message = self.llm_service.call(
                prompt,
                temperature=0.7,
                max_tokens=150
            )
            
            # Clean up message
            message = message.strip().strip('"')
            
            # Cache if not high priority
            if priority != 'high':
                self.message_cache[cache_key] = message
            
            logger.info(f"Generated LLM insight for pattern: {pattern_type}")
            return message
            
        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}")
            # Fallback to template
            return self._get_fallback_message(pattern_type, pattern_data)
    
    def _build_prompt(
        self, 
        pattern_type: str, 
        pattern_data: Dict, 
        user_context: Dict,
        priority: str
    ) -> str:
        """Build LLM prompt for insight generation"""
        
        # Tone based on priority
        tone_map = {
            'high': 'concerned but supportive and caring',
            'medium': 'encouraging and friendly',
            'low': 'celebratory and warm'
        }
        
        tone = tone_map.get(priority, 'supportive')
        
        # Build context summary
        context_summary = self._format_context(user_context)
        
        # Build pattern summary
        pattern_summary = self._format_pattern(pattern_type, pattern_data)
        
        # Determine if we should end with a question
        # For celebrations (activity_streak), don't ask questions - just celebrate!
        ending_instruction = "End with encouragement or a question" if pattern_type != 'activity_streak' else "End with encouragement (NOT a question)"
        
        prompt = f"""You are a supportive wellness coach generating a personalized message for a user.

User Context:
{context_summary}

Pattern Detected:
{pattern_summary}

Generate a {tone} message that:
1. Acknowledges the pattern naturally (don't just state facts)
2. Shows empathy and understanding
3. Offers hope or encouragement
4. Keeps it brief (2-3 sentences maximum)
5. Feels personal and caring, not clinical
6. Uses "I've noticed" or "I see" rather than "You have"

Important:
- Be warm and human
- Don't lecture or judge
- Focus on support, not criticism
- {ending_instruction}

Generate only the message, no extra text:"""
        
        return prompt
    
    def _format_context(self, user_context: Dict) -> str:
        """Format user context for prompt"""
        lines = []
        
        if user_context.get('days_active'):
            lines.append(f"- Using app for: {user_context['days_active']} days")
        
        if user_context.get('baseline_activities'):
            lines.append(f"- Typical activity level: {user_context['baseline_activities']} activities/week")
        
        if user_context.get('best_activity'):
            best = user_context['best_activity']
            lines.append(f"- Most effective activity: {best['name']} (rated {best['avg_rating']}/5)")
        
        return '\n'.join(lines) if lines else "- New user"
    
    def _format_pattern(self, pattern_type: str, pattern_data: Dict) -> str:
        """Format pattern data for prompt"""
        
        if pattern_type == 'stress_inactivity_cycle':
            return f"""Type: Prolonged stress with declining activity
- Stressed for: {pattern_data.get('stressed_days', 0)} consecutive days
- Recent activities: {pattern_data.get('current_activities', 0)}
- Usual activities: {pattern_data.get('baseline_activities', 0)}
- Reason: {pattern_data.get('reason', 'unknown')}"""
        
        elif pattern_type == 'activity_streak':
            return f"""Type: Positive activity streak
- Streak: {pattern_data.get('streak', 0)} consecutive days
- Total activities: {pattern_data.get('total_activities', 0)}"""
        
        elif pattern_type == 'low_activity':
            return f"""Type: Activity level drop
- This week: {pattern_data.get('current_week', 0)} activities
- Usual: {pattern_data.get('baseline', 0)} activities/week
- Drop: {pattern_data.get('drop_percentage', 0)}%"""
        
        elif pattern_type == 'proven_solution':
            return f"""Type: Activity that works well for user
- Activity: {pattern_data.get('activity_name', 'unknown')}
- Times done: {pattern_data.get('times_done', 0)}
- Average rating: {pattern_data.get('avg_rating', 0)}/5
- Context: {pattern_data.get('context', 'general')}"""
        
        else:
            return f"Type: {pattern_type}\nDetails: {json.dumps(pattern_data)}"
    
    def _get_cache_key(self, pattern_type: str, pattern_data: Dict) -> str:
        """Generate cache key for pattern"""
        # Simple cache key based on pattern type and key values
        key_parts = [pattern_type]
        
        if pattern_type == 'stress_inactivity_cycle':
            key_parts.append(str(pattern_data.get('stressed_days', 0)))
        elif pattern_type == 'activity_streak':
            key_parts.append(str(pattern_data.get('streak', 0)))
        elif pattern_type == 'low_activity':
            key_parts.append(str(pattern_data.get('drop_percentage', 0) // 10))
        
        return '_'.join(key_parts)
    
    def _get_fallback_message(self, pattern_type: str, pattern_data: Dict) -> str:
        """Fallback template messages if LLM fails"""
        
        templates = {
            'stress_inactivity_cycle': f"I've noticed you've been stressed for {pattern_data.get('stressed_days', 0)} days and less active than usual. Let's work on this together.",
            
            'activity_streak': f"🔥 You're on a {pattern_data.get('streak', 0)}-day streak! That's amazing - keep it going!",
            
            'low_activity': f"Your activity level has dropped this week. That's okay - let's start small and rebuild your routine.",
            
            'proven_solution': f"{pattern_data.get('activity_name', 'This activity')} has been working really well for you. Want to try it again?"
        }
        
        return templates.get(pattern_type, "How are you feeling today?")
