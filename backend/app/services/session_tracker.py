"""
Session Tracker Service
Tracks user session to prevent fatigue and over-prompting
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import os
import logging

logger = logging.getLogger(__name__)


class SessionTracker:
    """Tracks user session activity to prevent fatigue"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mood.db')
        self.db_path = db_path
        self._session_cache = {}  # In-memory cache for current session
    
    def track_interaction(self, user_id: int, interaction_type: str, data: Dict = None):
        """
        Track a user interaction
        
        Args:
            user_id: User ID
            interaction_type: 'prompt_shown', 'button_clicked', 'prompt_ignored', 'message_sent'
            data: Additional data about the interaction
        """
        if user_id not in self._session_cache:
            self._session_cache[user_id] = {
                'prompts_shown': 0,
                'prompts_ignored': 0,
                'buttons_clicked': 0,
                'messages_sent': 0,
                'last_interaction': datetime.now(),
                'session_start': datetime.now()
            }
        
        session = self._session_cache[user_id]
        
        if interaction_type == 'prompt_shown':
            session['prompts_shown'] += 1
        elif interaction_type == 'prompt_ignored':
            session['prompts_ignored'] += 1
        elif interaction_type == 'button_clicked':
            session['buttons_clicked'] += 1
            session['prompts_ignored'] = 0  # Reset ignore counter on engagement
        elif interaction_type == 'message_sent':
            session['messages_sent'] += 1
        
        session['last_interaction'] = datetime.now()
    
    def get_session_fatigue(self, user_id: int) -> Dict:
        """
        Calculate session fatigue level
        
        Returns:
            {
                'fatigue_level': 'none' | 'low' | 'medium' | 'high',
                'should_reduce_prompts': bool,
                'should_stay_silent': bool,
                'reasons': list
            }
        """
        session = self._session_cache.get(user_id)
        
        if not session:
            return {
                'fatigue_level': 'none',
                'should_reduce_prompts': False,
                'should_stay_silent': False,
                'reasons': []
            }
        
        reasons = []
        fatigue_score = 0
        
        # Factor 1: Ignored prompts
        if session['prompts_ignored'] >= 2:
            fatigue_score += 3
            reasons.append(f"ignored {session['prompts_ignored']} prompts")
        
        # Factor 2: Too many prompts shown
        if session['prompts_shown'] >= 5:
            fatigue_score += 2
            reasons.append(f"{session['prompts_shown']} prompts shown")
        
        # Factor 3: Low engagement ratio
        if session['prompts_shown'] > 0:
            engagement_ratio = session['buttons_clicked'] / session['prompts_shown']
            if engagement_ratio < 0.3:
                fatigue_score += 2
                reasons.append(f"low engagement ({engagement_ratio:.0%})")
        
        # Factor 4: Session length
        session_duration = (datetime.now() - session['session_start']).seconds / 60
        if session_duration > 30:
            fatigue_score += 1
            reasons.append(f"long session ({session_duration:.0f} min)")
        
        # Determine fatigue level
        if fatigue_score >= 5:
            fatigue_level = 'high'
        elif fatigue_score >= 3:
            fatigue_level = 'medium'
        elif fatigue_score >= 1:
            fatigue_level = 'low'
        else:
            fatigue_level = 'none'
        
        return {
            'fatigue_level': fatigue_level,
            'should_reduce_prompts': fatigue_level in ['medium', 'high'],
            'should_stay_silent': fatigue_level == 'high',
            'reasons': reasons,
            'session_stats': session
        }
    
    def check_time_context(self, user_id: int) -> Dict:
        """
        Check time-based context
        
        Returns:
            {
                'time_of_day': 'morning' | 'afternoon' | 'evening' | 'night',
                'energy_level': 'high' | 'medium' | 'low',
                'cognitive_load': 'low' | 'medium' | 'high'
            }
        """
        current_hour = datetime.now().hour
        
        # Determine time of day
        if 5 <= current_hour < 12:
            time_of_day = 'morning'
            energy_level = 'high'
            cognitive_load = 'low'
        elif 12 <= current_hour < 17:
            time_of_day = 'afternoon'
            energy_level = 'medium'
            cognitive_load = 'medium'
        elif 17 <= current_hour < 21:
            time_of_day = 'evening'
            energy_level = 'medium'
            cognitive_load = 'medium'
        else:
            time_of_day = 'night'
            energy_level = 'low'
            cognitive_load = 'high'
        
        return {
            'time_of_day': time_of_day,
            'energy_level': energy_level,
            'cognitive_load': cognitive_load,
            'current_hour': current_hour
        }
    
    def should_show_buttons(self, user_id: int, intent_type: str) -> bool:
        """
        Decide if buttons should be shown based on session context
        
        Args:
            user_id: User ID
            intent_type: User's intent (from IntentAnalyzer)
            
        Returns:
            bool: Whether to show buttons
        """
        # Check session fatigue
        fatigue = self.get_session_fatigue(user_id)
        
        # If high fatigue, don't show buttons
        if fatigue['should_stay_silent']:
            logger.info(f"Suppressing buttons due to high session fatigue: {fatigue['reasons']}")
            return False
        
        # If venting, don't show buttons
        if intent_type == 'venting':
            return False
        
        # If medium fatigue, only show for explicit action-seeking
        if fatigue['should_reduce_prompts'] and intent_type != 'action_seeking':
            logger.info(f"Reducing prompts due to medium fatigue: {fatigue['reasons']}")
            return False
        
        # Otherwise, show buttons
        return True
    
    def reset_session(self, user_id: int):
        """Reset session for user (e.g., after long inactivity)"""
        if user_id in self._session_cache:
            del self._session_cache[user_id]
            logger.info(f"Reset session for user {user_id}")
    
    def cleanup_old_sessions(self, hours: int = 2):
        """Clean up sessions older than specified hours"""
        current_time = datetime.now()
        users_to_remove = []
        
        for user_id, session in self._session_cache.items():
            if (current_time - session['last_interaction']).seconds / 3600 > hours:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self._session_cache[user_id]
        
        if users_to_remove:
            logger.info(f"Cleaned up {len(users_to_remove)} old sessions")


def get_session_tracker() -> SessionTracker:
    """Get or create SessionTracker instance"""
    return SessionTracker()
