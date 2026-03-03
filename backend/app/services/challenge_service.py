# app/services/challenge_service.py
# Challenge business logic and conversation integration

from app.repositories.challenge_repository import ChallengeRepository
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ChallengeService:
    """Service for challenge operations and conversation integration"""
    
    def __init__(self):
        self.challenge_repo = ChallengeRepository()
    
    def get_user_challenges(self, user_id: int) -> List[Dict]:
        """Get user's active challenges"""
        return self.challenge_repo.get_user_active_challenges(user_id)
    
    def get_challenge_motivation_message(self, user_id: int, activity_type: str = None) -> Optional[str]:
        """
        Get a motivational message about user's challenges
        
        This is called during conversations to naturally remind users
        about their challenges.
        
        Args:
            user_id: User ID
            activity_type: Type of activity just logged (water, sleep, etc.)
        
        Returns:
            Motivational message or None
        """
        challenges = self.challenge_repo.get_user_active_challenges(user_id)
        
        if not challenges:
            return None
        
        # If activity_type provided, find related challenge
        if activity_type:
            for challenge in challenges:
                if challenge['challenge_type'] == activity_type:
                    return self._format_challenge_progress_message(challenge)
        
        # Otherwise, pick the challenge closest to completion
        challenges_sorted = sorted(challenges, key=lambda x: x['progress'], reverse=True)
        if challenges_sorted:
            return self._format_challenge_reminder(challenges_sorted[0])
        
        return None
    
    def _format_challenge_progress_message(self, challenge: Dict) -> str:
        """Format a progress message for a specific challenge"""
        progress = challenge['progress']
        days_completed = challenge['days_completed']
        duration_days = challenge['duration_days']
        points = challenge['points']
        
        if progress >= 100:
            return f"🎉 Congratulations! You've completed the '{challenge['title']}' challenge and earned {points} points!"
        elif progress >= 75:
            return f"🔥 You're so close! {days_completed}/{duration_days} days done on '{challenge['title']}'. Keep it up!"
        elif progress >= 50:
            return f"💪 Great progress! You're halfway through '{challenge['title']}' ({days_completed}/{duration_days} days)."
        elif progress >= 25:
            return f"👍 Nice start on '{challenge['title']}'! {days_completed}/{duration_days} days completed."
        else:
            return f"🎯 You're working on '{challenge['title']}'! {days_completed}/{duration_days} days done."
    
    def _format_challenge_reminder(self, challenge: Dict) -> str:
        """Format a gentle reminder about a challenge"""
        days_left = challenge['duration_days'] - challenge['days_completed']
        return f"💡 Reminder: You have {days_left} days left on '{challenge['title']}'. You've got this!"
    
    def update_progress_from_activity(self, user_id: int, activity_type: str, value: float) -> Optional[str]:
        """
        Update challenge progress when user logs an activity
        
        Returns motivational message if applicable
        """
        updated = self.challenge_repo.update_challenge_progress(user_id, activity_type, value)
        
        if updated:
            # Get updated challenge info
            challenges = self.challenge_repo.get_user_active_challenges(user_id)
            for challenge in challenges:
                if challenge['challenge_type'] == activity_type:
                    return self._format_challenge_progress_message(challenge)
        
        return None
    
    def get_challenges_summary(self, user_id: int) -> Dict:
        """Get a summary of user's challenges for display"""
        active_challenges = self.challenge_repo.get_user_active_challenges(user_id)
        available_challenges = self.challenge_repo.get_available_challenges(user_id)
        points_data = self.challenge_repo.get_user_points(user_id)
        
        return {
            'active_challenges': active_challenges,
            'available_challenges': available_challenges,
            'total_points': points_data['total_points'],
            'challenges_completed': points_data['challenges_completed'],
            'current_streak': points_data['current_streak']
        }
    
    def should_show_challenge_reminder(self, user_id: int) -> bool:
        """
        Determine if we should show a challenge reminder
        
        Logic: Show reminder if user has active challenges and hasn't
        made progress today on any of them
        """
        challenges = self.challenge_repo.get_user_active_challenges(user_id)
        
        if not challenges:
            return False
        
        # Check if user made progress today
        for challenge in challenges:
            progress_today = self.challenge_repo.get_challenge_progress_today(
                user_id, 
                challenge['challenge_type']
            )
            if progress_today and progress_today['target_met']:
                return False  # User already made progress today
        
        return True  # User has challenges but no progress today
    
    def join_challenge(self, user_id: int, challenge_id: int) -> Dict:
        """User joins a challenge"""
        success = self.challenge_repo.join_challenge(user_id, challenge_id)
        
        if success:
            return {
                'success': True,
                'message': "Challenge joined! Let's do this! 💪"
            }
        else:
            return {
                'success': False,
                'message': "Couldn't join challenge. You may already be participating."
            }
    
    def update_progress_from_event(self, user_id, event: dict):
        """
        Update challenge progress from activity event (Phase 2)
        
        Args:
            user_id: User ID (int or str)
            event: Event dictionary with activity_type, value, unit
        """
        try:
            # Convert user_id to int if it's a string
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            activity_type = event.get('activity_type')
            value = event.get('value')
            
            if not activity_type or value is None:
                return
            
            logger.info(f"[Phase 2] Updating challenge progress for {activity_type}: {value}")
            
            # Update progress
            updated = self.challenge_repo.update_challenge_progress(
                user_id, 
                activity_type, 
                value
            )
            
            if updated:
                logger.info(f"[Phase 2] Challenge progress updated successfully")
                
                # Check if any challenges were completed
                challenges = self.challenge_repo.get_user_active_challenges(user_id)
                for challenge in challenges:
                    if challenge['challenge_type'] == activity_type and challenge['progress'] >= 100:
                        logger.info(f"[Phase 2] 🎉 Challenge completed: {challenge['title']}")
                        # Could publish challenge_completed event here
            
        except Exception as e:
            logger.error(f"Failed to update challenge progress from event: {e}")
