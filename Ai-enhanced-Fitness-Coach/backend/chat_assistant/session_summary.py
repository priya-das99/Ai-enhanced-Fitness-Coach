# session_summary.py
# Semantic memory layer - captures meaning, not messages

from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SessionFocus:
    """Constrained focus values - prevents semantic drift"""
    HYDRATION = "hydration"
    MOOD = "mood"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    WEIGHT = "weight"
    NONE = None
    
    @classmethod
    def is_valid(cls, focus: Optional[str]) -> bool:
        """Check if focus value is valid"""
        return focus in [cls.HYDRATION, cls.MOOD, cls.SLEEP, 
                        cls.EXERCISE, cls.WEIGHT, cls.NONE]


class SessionSummary:
    """
    Semantic memory - captures meaning, not raw dialogue
    
    Purpose:
    - Ground LLM with semantic context
    - Reduce token usage
    - Improve consistency
    
    Design principles:
    - Text output for LLM (not JSON)
    - Constrained focus (enum values)
    - Preferences persist, focus expires
    - Max 150 chars
    """
    
    MAX_SUMMARY_LENGTH = 150
    STALENESS_THRESHOLD = timedelta(hours=1)
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_focus: Optional[str] = None
        self.preferences: Dict[str, str] = {}
        self.last_updated = datetime.now()
    
    def set_focus(self, focus: Optional[str]):
        """
        Set current focus with validation
        
        Args:
            focus: Must be SessionFocus constant or None
        """
        if not SessionFocus.is_valid(focus):
            logger.warning(f"User {self.user_id}: Invalid focus '{focus}', ignoring")
            return
        
        self.current_focus = focus
        self.last_updated = datetime.now()
        logger.info(f"User {self.user_id}: Focus set to '{focus}'")
    
    def set_preference(self, key: str, value: str):
        """
        Set explicit user preference
        
        Args:
            key: Preference key (e.g., 'water_unit')
            value: Preference value (e.g., 'glasses')
        """
        self.preferences[key] = value
        self.last_updated = datetime.now()
        logger.info(f"User {self.user_id}: Preference '{key}' = '{value}'")
    
    def is_stale(self) -> bool:
        """Check if summary is older than threshold"""
        return (datetime.now() - self.last_updated) > self.STALENESS_THRESHOLD
    
    def clear_if_stale(self):
        """
        Clear focus if stale, keep preferences
        
        Rationale:
        - Focus is contextual → expires after 1 hour
        - Preferences are behavioral → persist until overridden
        """
        if self.is_stale():
            logger.info(f"User {self.user_id}: Summary stale, clearing focus")
            self.current_focus = None
            # Preferences intentionally kept - assumed stable
    
    def to_prompt(self) -> str:
        """
        Generate natural language summary for LLM (max 150 chars)
        
        Returns:
            1-2 sentence summary or empty string
        """
        if not self.current_focus and not self.preferences:
            return ""
        
        parts = []
        
        # Focus as natural language
        if self.current_focus:
            focus_text = {
                SessionFocus.HYDRATION: "hydration tracking",
                SessionFocus.MOOD: "mood logging",
                SessionFocus.SLEEP: "sleep tracking",
                SessionFocus.EXERCISE: "exercise logging",
                SessionFocus.WEIGHT: "weight tracking"
            }.get(self.current_focus, self.current_focus)
            parts.append(f"The user is focused on {focus_text}")
        
        # Preferences as natural language (not raw keys)
        if self.preferences:
            pref_phrases = []
            
            if "water_unit" in self.preferences:
                pref_phrases.append(f"prefers logging water in {self.preferences['water_unit']}")
            
            if "sleep_unit" in self.preferences:
                pref_phrases.append(f"tracks sleep in {self.preferences['sleep_unit']}")
            
            if pref_phrases:
                parts.append(" and ".join(pref_phrases))
        
        summary = ". ".join(parts) + "."
        
        # Enforce 150 char cap
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[:self.MAX_SUMMARY_LENGTH - 3] + "..."
        
        return summary
    
    def clear(self):
        """Clear all summary data"""
        self.current_focus = None
        self.preferences = {}
        self.last_updated = datetime.now()
        logger.info(f"User {self.user_id}: Summary cleared")
    
    def __repr__(self) -> str:
        """Debug representation"""
        return (f"SessionSummary(user={self.user_id}, focus={self.current_focus}, "
                f"prefs={self.preferences}, age={(datetime.now() - self.last_updated).seconds}s)")
