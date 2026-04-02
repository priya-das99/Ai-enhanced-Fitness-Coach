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
            
            # Get challenge summary using the proper service
            summary = challenge_service.get_challenges_summary(user_id)
            
            active = summary['active_challenges']
            available = summary['available_challenges']
            points = summary['total_points']
            completed = summary['challenges_completed']
            
            # Detect query type
            message_lower = message.lower()
            is_progress_query = any(word in message_lower for word in 
                                   ['how am i', 'how\'s my', 'my progress', 'doing with', 'status', 'progress',
                                    'how am i doing', 'how are my', 'am i doing'])
            is_specific_challenge = any(word in message_lower for word in
                                       ['meditation', 'steps', 'mood', 'squats', 'sleep', 'meals', 'water', 'hydration'])
            is_list_query = any(word in message_lower for word in
                               ['what are', 'show', 'list', 'view', 'current', 'my challenges', 'five challenges',
                                'do i have', 'have any', 'what challenges', 'any challenges'])
            is_goal_query = any(word in message_lower for word in
                               ['meet my goal', 'did i meet', 'goal', 'complete', 'how many', 'need to'])
            
            # Debug logging
            logger.info(f"Challenge query analysis for '{message}':")
            logger.info(f"  is_progress_query: {is_progress_query}")
            logger.info(f"  is_list_query: {is_list_query}")
            logger.info(f"  is_specific_challenge: {is_specific_challenge}")
            logger.info(f"  is_goal_query: {is_goal_query}")
            logger.info(f"  active challenges: {len(active)}")
            logger.info(f"  available challenges: {len(available)}")
            
            # Build response based on query type - PRIORITIZE SPECIFIC QUERIES
            logger.info(f"Challenge workflow logic:")
            logger.info(f"  active challenges: {len(active)}")
            logger.info(f"  available challenges: {len(available)}")
            logger.info(f"  is_progress_query: {is_progress_query}")
            logger.info(f"  is_list_query: {is_list_query}")
            logger.info(f"  is_specific_challenge: {is_specific_challenge}")
            logger.info(f"  is_goal_query: {is_goal_query}")
            
            if not active and not available:
                logger.info("Branch: no active and no available challenges")
                message_text = "No challenges available right now. Check back soon! 🎯"
                buttons = []
            elif is_progress_query:
                logger.info("Branch: progress query")
                # User asking about progress - show progress even if no active challenges
                if active:
                    message_text = self._create_progress_response(active, points, completed)
                    buttons = self._create_action_buttons_for_pending(active)
                else:
                    message_text = f"You don't have any active challenges yet.\n\n"
                    message_text += f"Total Points: {points} | Completed: {completed}\n\n"
                    if available:
                        message_text += f"You have {len(available)} challenge(s) available to join! Want to take one on? 💪"
                        buttons = self._create_available_challenge_buttons(available[:3])
                    else:
                        buttons = []
            elif is_list_query:
                logger.info("Branch: list query")
                # User asking to see challenges - show both active and available
                if active:
                    message_text = self._create_list_response(active, points, completed)
                    buttons = self._create_action_buttons_for_pending(active)
                elif available:
                    message_text = f"You have {len(available)} challenge(s) available to join:\n\n"
                    for i, ch in enumerate(available[:5], 1):
                        message_text += f"{i}. {ch['title']}\n"
                        message_text += f"   Duration: {ch['duration_days']} days | Reward: {ch['points']} points\n\n"
                    message_text += "Want to take one on? 💪"
                    buttons = self._create_available_challenge_buttons(available[:3])
                else:
                    message_text = "No challenges available right now. Check back soon! 🎯"
                    buttons = []
            elif is_goal_query or is_specific_challenge:
                logger.info("Branch: goal or specific challenge query")
                # User asking about specific challenge or goal
                if active:
                    if is_specific_challenge:
                        message_text, buttons = self._create_specific_challenge_response(
                            message_lower, active, user_id
                        )
                    else:
                        # Goal query - show relevant challenge progress
                        message_text, buttons = self._create_goal_response(
                            message_lower, active, user_id
                        )
                else:
                    message_text = f"You don't have any active challenges yet.\n\n"
                    if available:
                        message_text += f"You have {len(available)} challenge(s) available to join! Want to take one on? 💪"
                        buttons = self._create_available_challenge_buttons(available[:3])
                    else:
                        buttons = []
            elif not active:
                logger.info("Branch: no active challenges - show available")
                # No specific query and no active challenges - show available
                message_text = f"You have {len(available)} challenge(s) available to join! Want to take one on? 💪"
                buttons = self._create_available_challenge_buttons(available[:3])
            else:
                logger.info("Branch: default - show active challenges")
                # Default: show active challenges
                message_text = self._create_list_response(active, points, completed)
                buttons = self._create_action_buttons_for_pending(active)
            
            logger.info(f"Final response: {message_text[:100]}...")
            logger.info(f"Buttons: {len(buttons)} buttons")
            
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
            'meals': ['meals', 'food', 'eating'],
            'water': ['water', 'hydration', 'drink', 'glasses']
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
        challenge_type = target_challenge['challenge_type']
        
        # For water challenges, show glasses progress instead of days
        if challenge_type == 'water' and ('glass' in message_lower or 'water' in message_lower or 'hydration' in message_lower):
            # Get today's water progress
            try:
                from app.services.user_context_service import get_context_service
                context_service = get_context_service()
                
                # Get today's water intake
                today_water = context_service.get_today_water_intake(user_id)
                target_glasses = target_challenge.get('target_value', 8)  # Default 8 glasses
                remaining_glasses = max(0, target_glasses - today_water)
                
                if remaining_glasses == 0:
                    message = f"🎉 Amazing! You've completed your daily water goal for '{target_challenge['title']}'!\n\n"
                    message += f"Target: {target_glasses} glasses | Completed: {today_water} glasses\n\n"
                    message += "Great job staying hydrated! Keep it up! 💧"
                    buttons = []
                else:
                    message = f"💧 You're working on '{target_challenge['title']}'!\n\n"
                    message += f"Today: {today_water}/{target_glasses} glasses\n"
                    message += f"You need {remaining_glasses} more glass{'es' if remaining_glasses > 1 else ''} to reach your daily goal!\n\n"
                    message += "Stay hydrated! 🚰"
                    buttons = [{
                        'id': 'log_water',
                        'name': '💧 Log Water',
                        'user_message': 'Log water intake'
                    }]
                
                return message, buttons
                
            except Exception as e:
                logger.error(f"Error getting water progress: {e}", exc_info=True)
                # Fall through to default response
        
        # Default response for other challenges or if water query fails
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
    
    def _create_goal_response(self, message_lower: str, active: list, user_id: int) -> tuple:
        """Create response for goal-related queries (e.g., 'did I meet my goal', 'how many more')"""
        # Detect what type of goal they're asking about
        goal_keywords = {
            'water': ['water', 'hydration', 'drink', 'glasses'],
            'sleep': ['sleep', 'rest', 'sleeping', 'hours'],
            'exercise': ['exercise', 'workout', 'steps', 'activity'],
            'mood': ['mood', 'feeling'],
            'meditation': ['meditation', 'meditate', 'mindful']
        }
        
        target_challenge = None
        for challenge in active:
            challenge_type = challenge['challenge_type']
            keywords = goal_keywords.get(challenge_type, [])
            if any(keyword in message_lower for keyword in keywords):
                target_challenge = challenge
                break
        
        if not target_challenge:
            # No specific challenge found - show all active challenges
            return self._create_list_response(active, 0, 0), self._create_action_buttons_for_pending(active)
        
        # Get today's progress for this challenge
        try:
            from app.core.database import get_db
            from datetime import date
            
            # Get challenge details
            challenge_type = target_challenge['challenge_type']
            target_value = target_challenge.get('target_value', 0)
            
            # Get today's logged value
            today = date.today().isoformat()
            today_value = 0
            
            with get_db() as db:
                cursor = db.cursor()
                
                if challenge_type == 'water':
                    cursor.execute("""
                        SELECT SUM(value) as total FROM health_activities
                        WHERE user_id = ? AND activity_type = 'water'
                        AND DATE(timestamp) = ?
                    """, (user_id, today))
                    result = cursor.fetchone()
                    today_value = result['total'] if result['total'] else 0
                    
                elif challenge_type == 'sleep':
                    cursor.execute("""
                        SELECT SUM(value) as total FROM health_activities
                        WHERE user_id = ? AND activity_type = 'sleep'
                        AND DATE(timestamp) = ?
                    """, (user_id, today))
                    result = cursor.fetchone()
                    today_value = result['total'] if result['total'] else 0
                    
                elif challenge_type == 'exercise':
                    cursor.execute("""
                        SELECT SUM(value) as total FROM health_activities
                        WHERE user_id = ? AND activity_type = 'exercise'
                        AND DATE(timestamp) = ?
                    """, (user_id, today))
                    result = cursor.fetchone()
                    today_value = result['total'] if result['total'] else 0
            
            # Calculate remaining
            remaining = max(0, target_value - today_value)
            unit = target_challenge.get('target_unit', '')
            
            # Build response
            if remaining == 0:
                message = f"🎉 Yes! You've met your goal for '{target_challenge['title']}' today!\n\n"
                message += f"Target: {target_value} {unit} | Completed: {today_value} {unit}\n\n"
                message += "Great job! Keep up the momentum! 💪"
                buttons = []
            else:
                message = f"You're making progress on '{target_challenge['title']}'!\n\n"
                message += f"Today: {today_value}/{target_value} {unit}\n"
                message += f"Remaining: {remaining} {unit} more to reach your goal!\n\n"
                message += "You've got this! 🔥"
                buttons = [self._create_action_button_for_challenge(target_challenge)]
            
            return message, buttons
            
        except Exception as e:
            logger.error(f"Error getting goal progress: {e}", exc_info=True)
            # Fallback to general challenge response
            return self._create_specific_challenge_response(message_lower, active, user_id)
    
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
