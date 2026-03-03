# challenges_workflow.py
# Enhanced workflow for viewing and managing challenges with smart suggestions

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState, ConversationState
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ChallengesWorkflow(BaseWorkflow):
    """
    Enhanced Challenges workflow with:
    - Context-aware challenge suggestions
    - Action buttons for challenge completion
    - Progress tracking and encouragement
    - Integration with user's activity history
    
    Triggers:
    - "show my challenges"
    - "what challenges do I have"
    - "my progress"
    - "how am I doing"
    - "challenges"
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="challenges",
            handled_intents=['challenges', 'view_challenges', 'create_challenge', 'challenge_progress']
        )
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Show user their challenges with smart suggestions and action buttons"""
        logger.info(f"Starting enhanced challenges workflow for user {user_id}")
        
        # Store user_id for use in helper methods
        self._current_user_id = user_id
        
        try:
            from app.services.challenge_service import ChallengeService
            challenge_service = ChallengeService()
            
            summary = challenge_service.get_challenges_summary(user_id)
            
            active = summary['active_challenges']
            available = summary['available_challenges']
            points = summary['total_points']
            completed = summary['challenges_completed']
            
            # Detect query type
            message_lower = message.lower()
            is_progress_query = any(word in message_lower for word in 
                                   ['how am i', 'how\'s my', 'my progress', 'doing with', 'status'])
            is_specific_challenge = any(word in message_lower for word in
                                       ['meditation', 'steps', 'mood', 'squats', 'sleep', 'meals'])
            
            # Build response based on query type
            if not active and not available:
                message_text = "No challenges available right now. Check back soon! 🎯"
                buttons = []
            elif not active:
                message_text = f"You have {len(available)} challenge(s) available to join! Want to take one on? 💪"
                buttons = self._create_available_challenge_buttons(available[:3])
            else:
                # Check for specific challenge query
                if is_specific_challenge:
                    message_text, buttons = self._create_specific_challenge_response(
                        message_lower, active, user_id
                    )
                elif is_progress_query:
                    message_text = self._create_progress_response(active, points, completed)
                    buttons = self._create_action_buttons_for_pending(active)
                else:
                    message_text = self._create_list_response(active, points, completed)
                    buttons = self._create_action_buttons_for_pending(active)
            
            return self._complete_workflow(
                message=message_text,
                buttons=buttons,
                challenges=active,
                available_challenges=available,
                user_points=points
            )
            
        except Exception as e:
            logger.error(f"Error in challenges workflow: {e}", exc_info=True)
            return self._complete_workflow(
                message="I couldn't load your challenges right now. Try again later! 😊"
            )
    
    def _create_specific_challenge_response(self, message_lower: str, active: list, user_id: int) -> tuple:
        """Create response for specific challenge query"""
        # Find the challenge they're asking about
        challenge_keywords = {
            'meditation': ['meditation', 'meditate', 'mindful'],
            'steps': ['steps', 'walk', 'walking'],
            'mood': ['mood', 'feeling', 'log mood'],
            'squats': ['squats', 'squat', 'exercise'],
            'sleep': ['sleep', 'rest', 'sleeping'],
            'meals': ['meals', 'food', 'eating']
        }
        
        target_challenge = None
        for challenge in active:
            challenge_type = challenge['challenge_type']
            keywords = challenge_keywords.get(challenge_type, [])
            if any(keyword in message_lower for keyword in keywords):
                target_challenge = challenge
                break
        
        if not target_challenge:
            # Fallback to general response
            return self._create_list_response(active, 0, 0), self._create_action_buttons_for_pending(active)
        
        # Build specific response
        progress = target_challenge['progress']
        duration_days = target_challenge['duration_days']
        # Use actual days completed from database
        days_completed = target_challenge.get('days_completed', 0)
        days_left = duration_days - days_completed
        
        if progress >= 100:
            message = f"🎉 Amazing! You've completed the '{target_challenge['title']}' challenge!\n\n"
            message += f"You earned {target_challenge['points']} points. Keep up the great work!"
            buttons = []
        elif progress >= 75:
            message = f"🔥 You're crushing it! {days_completed}/{duration_days} days done on '{target_challenge['title']}'.\n\n"
            message += f"Just {days_left} more day{'s' if days_left > 1 else ''} to go! You've got this! 💪"
            buttons = [self._create_action_button_for_challenge(target_challenge)]
        elif progress >= 50:
            message = f"💪 Great progress! You're halfway through '{target_challenge['title']}'.\n\n"
            message += f"{days_completed}/{duration_days} days completed. Keep the momentum going!"
            buttons = [self._create_action_button_for_challenge(target_challenge)]
        elif progress >= 25:
            message = f"👍 Nice start on '{target_challenge['title']}'!\n\n"
            message += f"{days_completed}/{duration_days} days done. You're building a great habit!"
            buttons = [self._create_action_button_for_challenge(target_challenge)]
        else:
            message = f"🌱 You're working on '{target_challenge['title']}'.\n\n"
            message += f"{days_completed}/{duration_days} days completed. Every step counts!"
            buttons = [self._create_action_button_for_challenge(target_challenge)]
        
        return message, buttons
    
    def _create_action_button_for_challenge(self, challenge: dict) -> dict:
        """Create action button for a specific challenge"""
        challenge_type = challenge['challenge_type']
        
        button_map = {
            'meditation': {
                'id': 'start_meditation',
                'name': '🧘 Start Meditation',
                'user_message': 'Start meditation session'
            },
            'steps': {
                'id': 'track_steps',
                'name': '👟 Track Steps',
                'user_message': 'Log my steps'
            },
            'mood': {
                'id': 'log_mood',
                'name': '😊 Log Mood',
                'user_message': 'Log my mood'
            },
            'squats': {
                'id': 'track_squats',
                'name': '💪 Track Squats',
                'user_message': 'Log squats workout'
            },
            'sleep': {
                'id': 'log_sleep',
                'name': '😴 Log Sleep',
                'user_message': 'Log my sleep'
            },
            'meals': {
                'id': 'log_meals',
                'name': '🍽️ Log Meals',
                'user_message': 'Log my meals'
            }
        }
        
        return button_map.get(challenge_type, {
            'id': f'challenge_{challenge_type}',
            'name': f'Complete {challenge_type.title()}',
            'user_message': f'Complete {challenge_type} challenge'
        })
    
    def _create_action_buttons_for_pending(self, active: list) -> list:
        """Create action buttons for challenges that need attention today"""
        buttons = []
        
        # Find challenges that are active and not completed
        for challenge in active[:3]:  # Max 3 buttons
            if challenge['progress'] < 100:
                button = self._create_action_button_for_challenge(challenge)
                buttons.append(button)
        
        return buttons
    
    def _create_available_challenge_buttons(self, available: list) -> list:
        """Create buttons to join available challenges"""
        buttons = []
        
        for challenge in available:
            buttons.append({
                'id': f'join_challenge_{challenge["id"]}',
                'name': f'Join: {challenge["title"][:30]}...',
                'user_message': f'Join {challenge["title"]}'
            })
        
        return buttons
    
    def _create_progress_response(self, active, points, completed):
        """Create a progress-focused response with insights"""
        from app.services.insight_generator import get_insight_generator
        from app.services.pattern_detector import PatternDetector
        
        message_text = ""
        
        # Try to get insights first
        try:
            insight_gen = get_insight_generator()
            pattern_detector = PatternDetector()
            
            # Get all patterns
            patterns = pattern_detector.detect_all_patterns(self._current_user_id)
            
            # Generate insights
            insights = insight_gen.generate_insights(self._current_user_id)
            
            if insights:
                # Format top 3 insights
                insight_messages = []
                for insight in insights[:3]:
                    msg = self._format_insight(insight, patterns)
                    if msg:
                        insight_messages.append(msg)
                
                if insight_messages:
                    message_text = "\n".join(insight_messages) + "\n\n"
                    logger.info(f"Added {len(insight_messages)} insights to progress response")
        except Exception as e:
            logger.error(f"Failed to get insights: {e}", exc_info=True)
        
        # Add challenge progress
        message_text += f"🎯 Challenges:\n"
        message_text += f"Total Points: {points} | Completed: {completed}\n\n"
        
        # Group by progress level
        almost_done = [ch for ch in active if ch['progress'] >= 80]
        in_progress = [ch for ch in active if 30 <= ch['progress'] < 80]
        just_started = [ch for ch in active if ch['progress'] < 30]
        
        if almost_done:
            message_text += "🔥 Almost There:\n"
            for ch in almost_done:
                message_text += f"  • {ch['title']}: {ch['progress']:.0f}%\n"
            message_text += "\n"
        
        if in_progress:
            message_text += "📈 Making Progress:\n"
            for ch in in_progress:
                message_text += f"  • {ch['title']}: {ch['progress']:.0f}%\n"
            message_text += "\n"
        
        if just_started:
            message_text += "🌱 Just Getting Started:\n"
            for ch in just_started:
                message_text += f"  • {ch['title']}: {ch['progress']:.0f}%\n"
            message_text += "\n"
        
        # Add motivation
        if almost_done:
            message_text += "You're crushing it! Finish strong! 💪"
        elif in_progress:
            message_text += "Great momentum! Keep it up! 🚀"
        else:
            message_text += "Every journey starts with a single step! 🌟"
        
        return message_text
    
    def _format_insight(self, insight, patterns) -> str:
        """Format an insight object into a readable message"""
        insight_type = insight.insight_type
        data = insight.data
        severity = insight.severity
        
        # Choose emoji based on severity
        emoji_map = {
            'high': '🔴',
            'moderate': '🟡',
            'low': '🟢'
        }
        emoji = emoji_map.get(severity, '💡')
        
        messages = []
        
        if insight_type == 'prolonged_stress_pattern':
            days = data['consecutive_days']
            reason = data.get('recurring_reason', 'various reasons')
            messages.append(f"{emoji} You've been stressed for {days} consecutive days, mostly about {reason}.")
            messages.append("This prolonged stress is affecting your wellbeing.")
        
        elif insight_type == 'activity_decline':
            drop_pct = data['drop_percentage']
            current = data['current_week']
            baseline = data['baseline']
            messages.append(f"{emoji} Your activity has declined {drop_pct:.0f}% - from {baseline} activities to just {current}")
            messages.append("in the last week.")
        
        elif insight_type == 'stress_inactivity_cycle':
            days = data['stressed_days']
            drop = data['activity_drop']
            messages.append(f"{emoji} You've been stressed for {days} days and your activity dropped {drop:.0f}%.")
            messages.append("Let's work together to break this pattern.")
        
        elif insight_type == 'proven_solution_available':
            activity = data['activity_name']
            rating = data['avg_rating']
            messages.append(f"💡 {activity} helped you before (rated {rating}/5) - would you like to try that?")
        
        elif insight_type == 'activity_streak':
            streak = data['streak_days']
            messages.append(f"🔥 You're on a {streak}-day activity streak! Keep it going!")
        
        elif insight_type == 'improvement_trend':
            improvements = data.get('improvements', [])
            for improvement in improvements:
                imp_type = improvement['type']
                pct = improvement['percentage']
                current = improvement['current']
                baseline = improvement['baseline']
                
                if imp_type == 'activity':
                    messages.append(f"📈 You're {pct:.0f}% more active this week! ({current} activities vs {baseline:.1f} baseline)")
                elif imp_type == 'sleep':
                    messages.append(f"💤 Your sleep improved {pct:.0f}% this week! ({current:.1f}h vs {baseline:.1f}h baseline)")
                elif imp_type == 'water':
                    messages.append(f"💧 Your water intake improved {pct:.0f}% this week! ({current:.1f} glasses vs {baseline:.1f} baseline)")
        
        # Add health patterns if available
        if patterns and 'health_patterns' in patterns:
            health = patterns['health_patterns']
            
            # Water decline
            if health.get('water_decline'):
                water_current = health.get('water_current_avg', 0)
                water_baseline = health.get('water_baseline_avg', 0)
                drop_pct = health.get('water_decline_pct', 0)
                messages.append(f"{emoji} Your water intake has dropped {drop_pct:.0f}% - averaging only {water_current:.1f} glasses per day,")
                messages.append(f"down from {water_baseline:.1f}. Dehydration can worsen stress.")
            
            # Sleep decline
            if health.get('sleep_decline'):
                sleep_current = health.get('sleep_current_avg', 0)
                sleep_baseline = health.get('sleep_baseline_avg', 0)
                messages.append(f"😴 Your sleep has decreased to {sleep_current:.1f} hours, down from {sleep_baseline:.1f} hours.")
        
        return "\n".join(messages) if messages else None
    
    def _create_list_response(self, active, points, completed):
        """Create a list-focused response"""
        message_text = f"You have {len(active)} active challenge(s)! 🎯\n\n"
        message_text += f"Total Points: {points} | Completed: {completed}\n\n"
        
        for ch in active[:3]:  # Show top 3
            message_text += f"📌 {ch['title']}\n"
            message_text += f"   Progress: {ch['progress']:.0f}%\n"
            message_text += f"   Duration: {ch['duration_days']} days\n"
            message_text += f"   Reward: {ch['points']} points\n\n"
        
        return message_text
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Challenges workflow is single-step"""
        return self.start(message, state, user_id)
