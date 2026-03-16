"""
Predefined responses for common questions (0 tokens).
Checked BEFORE calling LLM to save costs.
Always includes action CTA.
"""

from typing import Optional


class ResponseTemplates:
    """
    Template responses for frequently asked questions.
    - 0 LLM tokens
    - Instant response
    - Always includes action nudge
    """
    
    TEMPLATES = {
        "breathing": {
            "how_long": "Usually 3-5 minutes works well. Want to try one?",
            "when": "Anytime you're feeling stressed. Ready to give it a shot?",
            "benefits": "It's great for stress and focus. Let's do a quick session!",
            "how_to": "I can guide you through it. Ready?",
            "night": "Perfect for winding down. Want to try one?",
            "work": "Great for work breaks! Let's do a quick one.",
            "anxiety": "Breathing really helps with anxiety. Want to try?"
        },
        "sleep": {
            "how_much": "Most people need 7-9 hours. Want to track yours?",
            "tips": "Regular schedule helps. Want to log tonight's sleep?",
            "cant_sleep": "That's rough. Let's track your sleep patterns.",
            "quality": "Quality matters as much as hours. Let's track it.",
            "tired": "Sleep tracking might help figure out why. Log last night?",
            "insomnia": "Let's start tracking your sleep to see what's going on."
        },
        "exercise": {
            "how_long": "Start with 5-10 minutes. Ready for a quick workout?",
            "what_type": "Let's start simple. Want to try a 5-minute bodyweight workout?",
            "benefits": "Boosts energy and mood. Let's get moving with a quick session!",
            "beginner": "Perfect! I'll guide you through a beginner-friendly workout.",
            "time": "Even 5 minutes makes a difference. Want to try a quick session?",
            "home": "No equipment needed! Ready for a bodyweight workout?"
        },
        "hydration": {
            "how_much": "Aim for 8 glasses daily. Let's log your water intake today.",
            "benefits": "Hydration boosts energy and focus. Let's track yours.",
            "reminder": "I can help you track water intake. Want to log how much you've had today?",
            "thirsty": "Let's log your water intake so I can help you stay hydrated."
        },
        "meditation": {
            "how_long": "Start with 3-5 minutes. Ready for a guided meditation?",
            "benefits": "Reduces stress and improves focus. Let's try a quick session.",
            "how_to": "I'll guide you through it! Ready to start?",
            "beginner": "Perfect for beginners! Want to try a 3-minute guided session?"
        },
        "nutrition": {
            "tips": "Let's log your meals so I can give personalized nutrition insights.",
            "healthy": "Tracking your meals helps identify patterns. Want to log today's meals?",
            "diet": "Let's start by logging what you eat. Ready to track today?"
        },
        "stress": {
            "relief": "Let's try a quick stress-relief activity. Ready?",
            "manage": "Stress management works best with action. Want to try a breathing exercise?",
            "work": "Work stress is common. Let's do a quick 3-minute stress-relief session."
        },
        "energy": {
            "boost": "Let's boost that energy! Want to try a quick workout or hydration check?",
            "tired": "Tracking activities helps identify energy patterns. Want to log your sleep?",
            "low": "Low energy can have many causes. Let's start tracking to find patterns."
        }
    }
    
    def match_template(self, topic: str, message: str) -> Optional[str]:
        """
        Match message to template using keyword rules.
        Returns template response or None.
        """
        if topic not in self.TEMPLATES:
            return None
            
        message_lower = message.lower()
        templates = self.TEMPLATES[topic]
        
        # Keyword matching (deterministic, 0 tokens)
        # Order matters - check more specific patterns first
        
        # Sleep problems (specific)
        if any(word in message_lower for word in ["can't sleep", "insomnia", "trouble sleeping"]):
            return templates.get("cant_sleep")
        
        # Quantity questions (specific for sleep)
        if topic == "sleep" and any(word in message_lower for word in ["how much", "amount"]):
            return templates.get("how_much")
        
        # Duration/time questions
        if any(word in message_lower for word in ["how long", "duration", "time", "minutes"]):
            return templates.get("how_long")
        
        # Timing questions
        if any(word in message_lower for word in ["when", "timing", "what time"]):
            return templates.get("when")
        
        # Benefits questions
        if any(word in message_lower for word in ["benefit", "why", "help", "good for", "does it work"]):
            return templates.get("benefits")
        
        # How-to questions
        if any(word in message_lower for word in ["how", "do it", "steps", "guide", "instructions"]):
            return templates.get("how_to")
        
        # Night/evening questions
        if any(word in message_lower for word in ["night", "evening", "bed", "before sleep"]):
            return templates.get("night")
        
        # Work-related
        if any(word in message_lower for word in ["work", "office", "desk", "job"]):
            return templates.get("work")
        
        # General quantity questions
        if any(word in message_lower for word in ["how much", "amount", "quantity", "many"]):
            return templates.get("how_much")
        
        # Tips/advice
        if any(word in message_lower for word in ["tip", "advice", "suggestion", "recommend"]):
            return templates.get("tips")
        
        # Quality questions
        if any(word in message_lower for word in ["quality", "better", "improve"]):
            return templates.get("quality")
        
        # Beginner questions
        if any(word in message_lower for word in ["beginner", "start", "new", "first time"]):
            return templates.get("beginner")
        
        # Type questions
        if any(word in message_lower for word in ["what type", "which", "kind of"]):
            return templates.get("what_type")
        
        # Home/equipment
        if any(word in message_lower for word in ["home", "no equipment", "no gym"]):
            return templates.get("home")
        
        # Tired/fatigue
        if any(word in message_lower for word in ["tired", "fatigue", "exhausted"]):
            return templates.get("tired")
        
        # Anxiety/stress
        if any(word in message_lower for word in ["anxiety", "anxious", "panic"]):
            return templates.get("anxiety")
        
        # Thirsty
        if any(word in message_lower for word in ["thirsty"]):
            return templates.get("thirsty")
        
        # Reminder
        if any(word in message_lower for word in ["remind", "reminder", "alert"]):
            return templates.get("reminder")
        
        # Relief
        if any(word in message_lower for word in ["relief", "relieve", "reduce"]):
            return templates.get("relief")
        
        # Manage
        if any(word in message_lower for word in ["manage", "control", "handle"]):
            return templates.get("manage")
        
        # Boost
        if any(word in message_lower for word in ["boost", "increase", "more"]):
            return templates.get("boost")
        
        # Low energy
        if any(word in message_lower for word in ["low energy", "no energy"]):
            return templates.get("low")
        
        # Healthy/diet
        if any(word in message_lower for word in ["healthy", "diet", "nutrition"]):
            return templates.get("healthy")
            
        return None
    
    def get_template_count(self) -> int:
        """Get total number of templates"""
        return sum(len(templates) for templates in self.TEMPLATES.values())
    
    def get_topics_with_templates(self) -> list:
        """Get list of topics that have templates"""
        return list(self.TEMPLATES.keys())
