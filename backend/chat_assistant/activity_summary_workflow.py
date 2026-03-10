# chat_assistant/activity_summary_workflow.py
# Workflow for handling activity summary queries

from .workflow_base import BaseWorkflow, WorkflowResponse
from .unified_state import WorkflowState
from app.services.user_context_service import get_context_service
import logging

logger = logging.getLogger(__name__)

class ActivitySummaryWorkflow(BaseWorkflow):
    """
    Handles activity summary and history queries.
    
    Triggers:
    - "What did I do today?"
    - "Show me my activities"
    - "How much water did I drink?"
    - "Did I exercise today?"
    - "What's my progress?"
    """
    
    def __init__(self):
        super().__init__(
            workflow_name="activity_summary",
            handled_intents=['activity_summary', 'activity_history', 'daily_summary']
        )
        self.context_service = get_context_service()
    
    def start(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Handle activity summary requests"""
        logger.info(f"Starting activity summary workflow for user {user_id}")
        
        message_lower = message.lower()
        
        try:
            # Detect query type
            if self._is_daily_summary_request(message_lower):
                response = self._handle_daily_summary(user_id)
            
            elif self._is_specific_activity_request(message_lower):
                activity_type = self._extract_activity_type(message_lower)
                response = self._handle_specific_activity(user_id, activity_type)
            
            elif self._is_progress_request(message_lower):
                response = self._handle_progress_query(user_id)
            
            else:
                # Default to daily summary
                response = self._handle_daily_summary(user_id)
            
            return self._complete_workflow(message=response)
        
        except Exception as e:
            logger.error(f"Error in activity summary workflow: {e}", exc_info=True)
            return self._complete_workflow(
                message="I couldn't retrieve your activity summary right now. Please try again! 😊"
            )
    
    def _is_daily_summary_request(self, message: str) -> bool:
        """Check if user wants daily summary"""
        keywords = [
            'what did i do', 'show my activities', 'today\'s activities',
            'what have i logged', 'my activities today', 'activity summary'
        ]
        return any(keyword in message for keyword in keywords)
    
    def _is_specific_activity_request(self, message: str) -> bool:
        """Check if user asking about specific activity"""
        activity_keywords = ['water', 'sleep', 'exercise', 'workout', 'mood']
        question_words = ['how much', 'how many', 'did i', 'have i']
        
        has_activity = any(keyword in message for keyword in activity_keywords)
        has_question = any(word in message for word in question_words)
        
        return has_activity and has_question
    
    def _is_progress_request(self, message: str) -> bool:
        """Check if user asking about progress"""
        keywords = ['progress', 'how am i doing', 'my status', 'where am i']
        return any(keyword in message for keyword in keywords)
    
    def _extract_activity_type(self, message: str) -> str:
        """Extract activity type from message"""
        if 'water' in message or 'drink' in message or 'hydrat' in message:
            return 'water'
        elif 'sleep' in message or 'slept' in message or 'rest' in message:
            return 'sleep'
        elif 'exercise' in message or 'workout' in message or 'gym' in message:
            return 'exercise'
        elif 'mood' in message or 'feeling' in message:
            return 'mood'
        else:
            return 'water'  # Default
    
    def _handle_daily_summary(self, user_id: int) -> str:
        """Generate daily summary response"""
        summary = self.context_service.get_daily_summary(user_id)
        
        if summary['total_activities'] == 0:
            return ("You haven't logged any activities today yet! 🌟\n\n"
                   "Start tracking your wellness journey:\n"
                   "• Log your mood 😊\n"
                   "• Track water intake 💧\n"
                   "• Record sleep 😴\n"
                   "• Log exercise 🏃")
        
        message = "📊 Here's your activity summary for today:\n\n"
        
        # Water
        water = summary['water']
        if water['value'] > 0:
            message += f"💧 Water: {water['value']:.0f}/{water['target']:.0f} {water['unit']}\n"
        
        # Sleep
        sleep = summary['sleep']
        if sleep['value'] > 0:
            message += f"😴 Sleep: {sleep['value']:.1f}/{sleep['target']:.0f} {sleep['unit']}\n"
        
        # Exercise
        exercise = summary['exercise']
        if exercise['value'] > 0:
            message += f"🏃 Exercise: {exercise['value']:.0f}/{exercise['target']:.0f} {exercise['unit']}\n"
        
        # Mood
        if summary['mood']['logged']:
            message += f"😊 Mood: {summary['mood']['emoji']}\n"
        
        message += f"\n✨ Total activities logged: {summary['total_activities']}"
        
        # Add encouragement
        if summary['total_activities'] >= 3:
            message += "\n\nGreat job staying on track! 🌟"
        elif summary['total_activities'] >= 1:
            message += "\n\nGood start! Keep it up! 💪"
        
        return message
    
    def _handle_specific_activity(self, user_id: int, activity_type: str) -> str:
        """Handle query about specific activity"""
        
        if activity_type == 'mood':
            summary = self.context_service.get_daily_summary(user_id)
            mood = summary['mood']
            
            if mood['logged']:
                return f"You logged your mood as {mood['emoji']} today! 😊"
            else:
                return "You haven't logged your mood today yet. How are you feeling? 😊"
        
        else:
            # Water, sleep, exercise
            progress = self.context_service.get_challenge_progress_today(user_id, activity_type)
            
            if not progress:
                # No active challenge, just show what they logged
                summary = self.context_service.get_daily_summary(user_id)
                activity_data = summary.get(activity_type, {})
                
                if activity_data.get('value', 0) > 0:
                    return f"You've logged {activity_data['value']:.1f} {activity_data['unit']} of {activity_type} today! 👍"
                else:
                    return f"You haven't logged any {activity_type} today yet."
            
            # Has active challenge
            current = progress['current']
            target = progress['target']
            unit = progress['unit']
            remaining = progress['remaining']
            percentage = progress['percentage']
            
            if progress['completed']:
                return (f"🎉 Yes! You've completed your {activity_type} goal for today!\n\n"
                       f"Target: {target} {unit} | Completed: {current} {unit}\n\n"
                       f"Great job! Keep up the momentum! 💪")
            
            elif current == 0:
                return (f"You haven't logged any {activity_type} today yet.\n\n"
                       f"Your goal: {target} {unit}\n\n"
                       f"Let's get started! 🚀")
            
            else:
                return (f"You're making progress on {activity_type}! 📈\n\n"
                       f"Today: {current}/{target} {unit} ({percentage:.0f}%)\n"
                       f"Remaining: {remaining} {unit}\n\n"
                       f"You've got this! 🔥")
    
    def _handle_progress_query(self, user_id: int) -> str:
        """Handle general progress query"""
        all_progress = self.context_service.get_all_challenges_progress(user_id)
        
        if not all_progress:
            return ("You don't have any active challenges yet.\n\n"
                   "Want to start tracking your wellness goals? 🎯")
        
        message = "📊 Your Challenge Progress:\n\n"
        
        completed = [p for p in all_progress if p['completed']]
        in_progress = [p for p in all_progress if not p['completed']]
        
        if completed:
            message += "✅ Completed Today:\n"
            for p in completed:
                message += f"  • {p['challenge_title']}: {p['current']}/{p['target']} {p['unit']} ✓\n"
            message += "\n"
        
        if in_progress:
            message += "📈 In Progress:\n"
            for p in in_progress:
                message += f"  • {p['challenge_title']}: {p['current']}/{p['target']} {p['unit']} ({p['percentage']:.0f}%)\n"
            message += "\n"
        
        # Add encouragement
        if len(completed) == len(all_progress):
            message += "🎉 All challenges completed! You're crushing it! 🌟"
        elif len(completed) > 0:
            message += "💪 Great progress! Keep going!"
        else:
            message += "🚀 Let's make some progress today!"
        
        return message
    
    def process(self, message: str, state: WorkflowState, user_id: int) -> WorkflowResponse:
        """Activity summary workflow is single-step"""
        return self.start(message, state, user_id)
