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
        activity_keywords = ['water', 'sleep', 'exercise', 'workout', 'mood', 'weight', 'weigh']
        
        # Add common sports and exercise activities
        exercise_activities = [
            'badminton', 'tennis', 'football', 'soccer', 'basketball', 'volleyball',
            'cricket', 'baseball', 'hockey', 'swimming', 'running', 'jogging',
            'cycling', 'biking', 'yoga', 'pilates', 'dancing', 'boxing',
            'martial arts', 'karate', 'judo', 'taekwondo', 'wrestling',
            'golf', 'bowling', 'ping pong', 'table tennis', 'squash',
            'climbing', 'hiking', 'walking', 'cardio', 'strength training',
            'weightlifting', 'crossfit', 'aerobics', 'zumba', 'spinning'
        ]
        
        question_words = ['how much', 'how many', 'did i', 'have i', 'what\'s my', 'show me my', 'how long', 'show my']
        
        has_activity = any(keyword in message for keyword in activity_keywords)
        has_exercise_activity = any(activity in message.lower() for activity in exercise_activities)
        has_question = any(word in message for word in question_words)
        
        return (has_activity or has_exercise_activity) and has_question
    
    def _is_progress_request(self, message: str) -> bool:
        """Check if user asking about progress"""
        keywords = ['progress', 'how am i doing', 'my status', 'where am i']
        return any(keyword in message for keyword in keywords)
    
    def _extract_activity_type(self, message: str) -> str:
        """Extract activity type from message"""
        message_lower = message.lower()
        
        if 'water' in message or 'drink' in message or 'hydrat' in message:
            return 'water'
        elif 'sleep' in message or 'slept' in message or 'rest' in message:
            return 'sleep'
        elif 'weight' in message or 'weigh' in message or 'kg' in message or 'pounds' in message:
            return 'weight'
        elif 'mood' in message or 'feeling' in message:
            return 'mood'
        elif 'steps' in message or 'walking' in message or 'walk' in message:
            return 'steps'
        elif 'calories' in message or 'calorie' in message or 'energy' in message:
            return 'calories'
        elif 'meal' in message or 'food' in message or 'eat' in message or 'ate' in message or 'nutrition' in message:
            return 'meal'
        elif 'exercise' in message or 'workout' in message or 'gym' in message:
            return 'exercise'
        else:
            # Check for specific sports and exercise activities
            exercise_activities = [
                'badminton', 'tennis', 'football', 'soccer', 'basketball', 'volleyball',
                'cricket', 'baseball', 'hockey', 'swimming', 'running', 'jogging',
                'cycling', 'biking', 'yoga', 'pilates', 'dancing', 'boxing',
                'martial arts', 'karate', 'judo', 'taekwondo', 'wrestling',
                'golf', 'bowling', 'ping pong', 'table tennis', 'squash',
                'climbing', 'hiking', 'cardio', 'strength training',
                'weightlifting', 'crossfit', 'aerobics', 'zumba', 'spinning'
            ]
            
            for activity in exercise_activities:
                if activity in message_lower:
                    return 'exercise'
            
            return 'water'  # Default
    
    def _extract_exercise_name_from_notes(self, notes: str) -> str:
        """Extract exercise name from notes field"""
        if not notes:
            return ""
        
        notes_lower = notes.lower()
        
        # Common exercise patterns
        exercise_patterns = [
            (r'played (\w+)', r'\1'),
            (r'did (\w+)', r'\1'),
            (r'went (\w+)', r'\1'),
            (r'(\w+) for \d+', r'\1'),
            (r'i (\w+)', r'\1'),
        ]
        
        import re
        for pattern, replacement in exercise_patterns:
            match = re.search(pattern, notes_lower)
            if match:
                exercise_name = match.group(1)
                # Capitalize first letter
                return exercise_name.capitalize()
        
        # If no pattern matches, try to find common exercise names directly
        common_exercises = [
            'badminton', 'tennis', 'football', 'soccer', 'basketball', 'volleyball',
            'cricket', 'baseball', 'hockey', 'swimming', 'running', 'jogging',
            'cycling', 'biking', 'yoga', 'pilates', 'dancing', 'boxing',
            'golf', 'bowling', 'squash', 'climbing', 'hiking'
        ]
        
        for exercise in common_exercises:
            if exercise in notes_lower:
                return exercise.capitalize()
        
        return ""

    def _get_detailed_exercise_records(self, user_id: int, target_date: str = None) -> list:
        """Get detailed exercise records for today"""
        from db import get_connection
        from datetime import date
        
        if not target_date:
            target_date = date.today().isoformat()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value, unit, notes, timestamp
            FROM health_activities
            WHERE user_id = ? AND activity_type = 'exercise' AND DATE(timestamp) = ?
            ORDER BY timestamp DESC
        ''', (user_id, target_date))
        
        records = cursor.fetchall()
        conn.close()
        
        exercises = []
        for record in records:
            value, unit, notes, timestamp = record
            
            # Extract exercise name from notes
            exercise_name = "exercise"
            if notes:
                # Look for patterns like "I played badminton for 30 minutes"
                import re
                patterns = [
                    r'played (\w+)',
                    r'did (\w+)',
                    r'went (\w+)',
                    r'(\w+) for \d+',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, notes.lower())
                    if match:
                        exercise_name = match.group(1)
                        break
                
                # If no pattern found, try to extract first meaningful word
                if exercise_name == "exercise" and notes:
                    words = notes.lower().split()
                    exercise_words = ['badminton', 'tennis', 'swimming', 'running', 'cycling', 'yoga', 'gym', 'workout']
                    for word in words:
                        if word in exercise_words:
                            exercise_name = word
                            break
            
            exercises.append({
                'name': exercise_name,
                'value': value,
                'unit': unit,
                'notes': notes,
                'timestamp': timestamp
            })
        
        return exercises
    
    def _handle_daily_summary(self, user_id: int) -> str:
        """Generate daily summary response"""
        summary = self.context_service.get_daily_summary(user_id)
        
        if summary['total_activities'] == 0:
            return ("You haven't logged any activities today yet! 🌟\n\n"
                   "Start tracking your wellness journey:\n"
                   "• Log your mood 😊\n"
                   "• Track water intake 💧\n"
                   "• Record sleep 😴\n"
                   "• Log exercise 🏃\n"
                   "• Track weight ⚖️")
        
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
            exercise_line = f"🏃 Exercise: {exercise['value']:.0f}/{exercise['target']:.0f} {exercise['unit']}"
            
            # Add specific exercise details
            detailed_exercises = self._get_detailed_exercise_records(user_id)
            if detailed_exercises:
                exercise_details = []
                for record in detailed_exercises:
                    notes = record.get('notes', '')
                    value = record.get('value', 0)
                    unit = record.get('unit', 'minutes')
                    
                    # Extract exercise name from notes
                    exercise_name = self._extract_exercise_name_from_notes(notes)
                    if exercise_name:
                        exercise_details.append(f"{exercise_name}: {value:.0f} {unit}")
                    else:
                        exercise_details.append(f"{value:.0f} {unit}")
                
                if exercise_details:
                    exercise_line += f" ({', '.join(exercise_details)})"
            
            message += exercise_line + "\n"
        
        # Weight - NEW: Add weight data to summary
        weight = summary.get('weight', {})
        if weight.get('value', 0) > 0:
            message += f"⚖️ Weight: {weight['value']:.1f} {weight.get('unit', 'kg')}\n"
        
        # Steps - NEW: Add steps data to summary
        steps = summary.get('steps', {})
        if steps.get('value', 0) > 0:
            message += f"👟 Steps: {steps['value']:.0f}/{steps.get('target', 10000):.0f} {steps.get('unit', 'steps')}\n"
        
        # Calories - NEW: Add calories data to summary
        calories = summary.get('calories', {})
        if calories.get('value', 0) > 0:
            message += f"🔥 Calories: {calories['value']:.0f}/{calories.get('target', 2000):.0f} {calories.get('unit', 'calories')}\n"
        
        # Meal - NEW: Add meal data to summary
        meal = summary.get('meal', {})
        if meal.get('value', 0) > 0:
            message += f"🍽️ Meals: {meal['value']:.0f}/{meal.get('target', 3):.0f} {meal.get('unit', 'servings')}\n"
        
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
        
        elif activity_type == 'weight':
            # Handle weight queries specifically
            summary = self.context_service.get_daily_summary(user_id)
            weight = summary.get('weight', {})
            
            if weight.get('value', 0) > 0:
                return f"Your current weight is {weight['value']:.1f} {weight.get('unit', 'kg')}! ⚖️"
            else:
                return "You haven't logged your weight today yet. Want to track it? ⚖️"
        
        elif activity_type == 'steps':
            # Handle steps queries specifically
            summary = self.context_service.get_daily_summary(user_id)
            steps = summary.get('steps', {})
            
            if steps.get('value', 0) > 0:
                return f"You've taken {steps['value']:.0f} {steps.get('unit', 'steps')} today! 👟"
            else:
                return "You haven't logged your steps today yet. Want to track your walking? 👟"
        
        elif activity_type == 'calories':
            # Handle calories queries specifically
            summary = self.context_service.get_daily_summary(user_id)
            calories = summary.get('calories', {})
            
            if calories.get('value', 0) > 0:
                return f"You've consumed {calories['value']:.0f} {calories.get('unit', 'calories')} today! 🔥"
            else:
                return "You haven't logged your calories today yet. Want to track your energy intake? 🔥"
        
        elif activity_type == 'meal':
            # Handle meal queries specifically
            summary = self.context_service.get_daily_summary(user_id)
            meal = summary.get('meal', {})
            
            if meal.get('value', 0) > 0:
                return f"You've logged {meal['value']:.0f} {meal.get('unit', 'servings')} today! 🍽️"
            else:
                return "You haven't logged your meals today yet. Want to track your nutrition? 🍽️"
        
        else:
            # Water, sleep, exercise - use challenge progress if available
            if activity_type == 'exercise':
                # Special handling for exercise to show detailed records
                exercises = self._get_detailed_exercise_records(user_id)
                summary = self.context_service.get_daily_summary(user_id)
                exercise_data = summary.get('exercise', {})
                total_minutes = exercise_data.get('value', 0)
                target = exercise_data.get('target', 30)
                
                if not exercises:
                    return "You haven't logged any exercise today yet. Ready to get moving? 🏃"
                
                # Build detailed response
                if len(exercises) == 1:
                    exercise = exercises[0]
                    if exercise['name'] != 'exercise':
                        return f"You played {exercise['name']} for {exercise['value']:.0f} {exercise['unit']} today! 🏸 Total exercise: {total_minutes:.0f}/{target} minutes"
                    else:
                        return f"You've logged {exercise['value']:.0f} {exercise['unit']} of exercise today! 💪 Total: {total_minutes:.0f}/{target} minutes"
                else:
                    # Multiple exercises
                    exercise_list = []
                    for exercise in exercises:
                        if exercise['name'] != 'exercise':
                            exercise_list.append(f"{exercise['name']} ({exercise['value']:.0f} {exercise['unit']})")
                        else:
                            exercise_list.append(f"exercise ({exercise['value']:.0f} {exercise['unit']})")
                    
                    exercises_text = ", ".join(exercise_list)
                    return f"Today you did: {exercises_text}. Total: {total_minutes:.0f}/{target} minutes 🏃"
            
            # For other activities (water, sleep), use existing logic
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
