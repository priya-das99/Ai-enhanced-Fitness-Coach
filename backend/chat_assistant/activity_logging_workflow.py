"""
Activity Logging Workflow

Multi-step workflow for logging activities with structured data:
1. Select category
2. Select activity
3. Select date
4. Select time
5. Enter duration
6. Confirm and save
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.services.activity_catalog_service import ActivityCatalogService


class ActivityLoggingWorkflow:
    """Handles the activity logging conversation flow"""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.catalog_service = ActivityCatalogService(conn)
    
    def start_logging(self, user_id: int) -> Dict:
        """Step 1: Show activity categories"""
        categories = self.catalog_service.get_categories()
        
        return {
            'message': 'Which type of activity did you do? 🎯',
            'buttons': [
                {
                    'text': f"{cat['icon']} {cat['name']}",
                    'action': f"log_activity_category:{cat['id']}"
                }
                for cat in categories
            ],
            'workflow': 'activity_logging',
            'step': 'select_category'
        }
    
    def select_category(self, user_id: int, category: str, state: Dict) -> Dict:
        """Step 2: Show activities in selected category"""
        activities = self.catalog_service.get_activities_by_category(category)
        
        if not activities:
            return {
                'message': f'No activities found in {category} category.',
                'workflow': 'activity_logging',
                'step': 'error'
            }
        
        # Save category to state
        state['activity_category'] = category
        
        category_names = {
            'wellbeing': 'Well-being',
            'popular': 'Most Popular',
            'exercise': 'Exercise'
        }
        
        return {
            'message': f'Great! Which {category_names.get(category, category)} activity? 💪',
            'buttons': [
                {
                    'text': f"{act['icon']} {act['name']}",
                    'action': f"log_activity_select:{act['id']}"
                }
                for act in activities
            ],
            'workflow': 'activity_logging',
            'step': 'select_activity',
            'state': state
        }
    
    def select_activity(self, user_id: int, activity_id: str, state: Dict) -> Dict:
        """Step 3: Ask for date"""
        activity = self.catalog_service.get_activity_by_id(activity_id)
        
        if not activity:
            return {
                'message': 'Activity not found.',
                'workflow': 'activity_logging',
                'step': 'error'
            }
        
        # Save activity to state
        state['activity_id'] = activity_id
        state['activity_name'] = activity['name']
        state['activity_icon'] = activity['icon']
        state['default_duration'] = activity['default_duration']
        
        return {
            'message': f'When did you do {activity["icon"]} {activity["name"]}? 📅',
            'buttons': [
                {'text': '📅 Today', 'action': 'log_activity_date:today'},
                {'text': '📅 Yesterday', 'action': 'log_activity_date:yesterday'},
                {'text': '📅 2 days ago', 'action': 'log_activity_date:2days'},
                {'text': '📅 Choose date', 'action': 'log_activity_date:custom'}
            ],
            'workflow': 'activity_logging',
            'step': 'select_date',
            'state': state
        }
    
    def select_date(self, user_id: int, date_option: str, state: Dict) -> Dict:
        """Step 4: Ask for time or custom date"""
        # Handle custom date request
        if date_option == 'custom':
            state['awaiting_custom_date'] = True
            return {
                'message': 'Please enter the date (e.g., "March 15" or "2 weeks ago"):',
                'workflow': 'activity_logging',
                'step': 'awaiting_custom_date',
                'state': state
            }
        
        # Calculate date
        if date_option == 'today':
            date = datetime.now().date()
            date_display = 'today'
        elif date_option == 'yesterday':
            date = (datetime.now() - timedelta(days=1)).date()
            date_display = 'yesterday'
        elif date_option == '2days':
            date = (datetime.now() - timedelta(days=2)).date()
            date_display = '2 days ago'
        else:
            # Default to today if unknown option
            date = datetime.now().date()
            date_display = 'today'
        
        # Save date to state
        state['activity_date'] = date.isoformat()
        state['date_display'] = date_display
        
        activity_name = state.get('activity_name', 'this activity')
        activity_icon = state.get('activity_icon', '📋')
        
        return {
            'message': f'What time did you start {activity_icon} {activity_name} {date_display}? ⏰',
            'buttons': [
                {'text': '⏰ Just now', 'action': 'log_activity_time:now'},
                {'text': '🌅 Morning (9 AM)', 'action': 'log_activity_time:morning'},
                {'text': '☀️ Afternoon (2 PM)', 'action': 'log_activity_time:afternoon'},
                {'text': '🌆 Evening (6 PM)', 'action': 'log_activity_time:evening'},
                {'text': '🌙 Night (9 PM)', 'action': 'log_activity_time:night'},
                {'text': '🕐 Custom time', 'action': 'log_activity_time:custom'}
            ],
            'workflow': 'activity_logging',
            'step': 'select_time',
            'state': state
        }
    
    def select_time(self, user_id: int, time_option: str, state: Dict) -> Dict:
        """Step 5: Ask for duration or custom time"""
        # Handle custom time request
        if time_option == 'custom':
            state['awaiting_custom_time'] = True
            activity_name = state.get('activity_name', 'this activity')
            activity_icon = state.get('activity_icon', '📋')
            return {
                'message': f'What time did you start {activity_icon} {activity_name}? (e.g., "10:30 AM" or "3:45 PM"):',
                'workflow': 'activity_logging',
                'step': 'awaiting_custom_time',
                'state': state
            }
        
        # Calculate start time
        date_str = state.get('activity_date', datetime.now().date().isoformat())
        date = datetime.fromisoformat(date_str)
        
        if time_option == 'now':
            start_time = datetime.now()
        elif time_option == 'morning':
            start_time = datetime.combine(date, datetime.min.time()).replace(hour=9, minute=0)
        elif time_option == 'afternoon':
            start_time = datetime.combine(date, datetime.min.time()).replace(hour=14, minute=0)
        elif time_option == 'evening':
            start_time = datetime.combine(date, datetime.min.time()).replace(hour=18, minute=0)
        elif time_option == 'night':
            start_time = datetime.combine(date, datetime.min.time()).replace(hour=21, minute=0)
        else:
            start_time = datetime.now()
        
        # Save start time to state
        state['start_time'] = start_time.isoformat()
        
        activity_name = state.get('activity_name', 'this activity')
        activity_icon = state.get('activity_icon', '📋')
        default_duration = state.get('default_duration', 30)
        
        # Suggest durations
        durations = [
            default_duration,
            default_duration - 15 if default_duration > 15 else 15,
            default_duration + 15,
            default_duration + 30
        ]
        durations = sorted(set([d for d in durations if d > 0]))
        
        return {
            'message': f'How long did you do {activity_icon} {activity_name}? ⏱️',
            'buttons': [
                {'text': f'⏱️ {d} minutes', 'action': f'log_activity_duration:{d}'}
                for d in durations[:4]
            ] + [
                {'text': '✏️ Custom duration', 'action': 'log_activity_duration:custom'}
            ],
            'workflow': 'activity_logging',
            'step': 'select_duration',
            'state': state
        }
    
    def select_duration(self, user_id: int, duration: int, state: Dict) -> Dict:
        """Step 6: Confirm and save"""
        # Get all data from state
        activity_id = state.get('activity_id')
        activity_name = state.get('activity_name')
        activity_icon = state.get('activity_icon', '📋')
        activity_category = state.get('activity_category')
        start_time_str = state.get('start_time')
        date_display = state.get('date_display', 'today')
        
        if not all([activity_id, start_time_str]):
            return {
                'message': 'Sorry, something went wrong. Please try again.',
                'workflow': 'activity_logging',
                'step': 'error'
            }
        
        # Parse start time
        start_time = datetime.fromisoformat(start_time_str)
        end_time = start_time + timedelta(minutes=duration)
        
        # Calculate day_of_week and time_of_day
        day_of_week = start_time.strftime('%A')
        hour = start_time.hour
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        
        # Save to database (user_activity_history table)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_activity_history 
            (user_id, activity_id, activity_name, activity_type, 
             duration_minutes, start_time, end_time, timestamp,
             day_of_week, time_of_day, completed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            activity_id,
            activity_name,
            activity_category,
            duration,
            start_time.isoformat(),
            end_time.isoformat(),
            datetime.now().isoformat(),
            day_of_week,
            time_of_day,
            1,  # completed = True
            None  # notes
        ))
        
        self.conn.commit()
        
        # Format response
        time_display = start_time.strftime('%I:%M %p')
        end_time_display = end_time.strftime('%I:%M %p')
        date_formatted = start_time.strftime('%B %d, %Y')
        
        message = f"""✅ Logged {activity_icon} {activity_name}!

📅 Date: {date_formatted} ({date_display})
⏰ Time: {time_display} - {end_time_display}
⏱️ Duration: {duration} minutes

Great job! Keep it up! 🎉"""
        
        return {
            'message': message,
            'workflow': 'activity_logging',
            'step': 'complete',
            'state': {}  # Clear state
        }
    
    def handle_custom_duration(self, user_id: int, duration_text: str, state: Dict) -> Dict:
        """Handle custom duration input"""
        try:
            # Extract number from text
            duration = int(''.join(filter(str.isdigit, duration_text)))
            
            if duration <= 0 or duration > 600:  # Max 10 hours
                return {
                    'message': 'Please enter a duration between 1 and 600 minutes.',
                    'workflow': 'activity_logging',
                    'step': 'select_duration',
                    'state': state
                }
            
            return self.select_duration(user_id, duration, state)
            
        except (ValueError, TypeError):
            return {
                'message': 'Please enter a valid number of minutes (e.g., "45" or "45 minutes").',
                'workflow': 'activity_logging',
                'step': 'select_duration',
                'state': state
            }
    
    def cancel_logging(self, user_id: int) -> Dict:
        """Cancel the logging workflow"""
        return {
            'message': 'Activity logging cancelled. Let me know if you want to log something later!',
            'workflow': 'activity_logging',
            'step': 'cancelled',
            'state': {}
        }
    
    def handle_custom_date(self, user_id: int, date_text: str, state: Dict) -> Dict:
        """Parse custom date input"""
        import re
        from dateutil import parser
        
        try:
            # Try to parse the date
            parsed_date = parser.parse(date_text, fuzzy=True).date()
            
            # Validate date is reasonable (not too far in past, not in future)
            today = datetime.now().date()
            days_ago = (today - parsed_date).days
            
            # Don't allow future dates
            if parsed_date > today:
                return {
                    'message': '⚠️ That date is in the future. Please enter a past date or today.',
                    'workflow': 'activity_logging',
                    'step': 'awaiting_custom_date',
                    'state': state
                }
            
            # Don't allow dates more than 1 year ago
            if days_ago > 365:
                return {
                    'message': '⚠️ That date is more than a year ago. Please enter a more recent date.',
                    'workflow': 'activity_logging',
                    'step': 'awaiting_custom_date',
                    'state': state
                }
            
            # Save date and continue to time selection
            state['activity_date'] = parsed_date.isoformat()
            state['date_display'] = parsed_date.strftime('%B %d, %Y')
            state.pop('awaiting_custom_date', None)
            
            activity_name = state.get('activity_name', 'this activity')
            activity_icon = state.get('activity_icon', '📋')
            
            return {
                'message': f'What time did you start {activity_icon} {activity_name} on {state["date_display"]}? ⏰',
                'buttons': [
                    {'text': '⏰ Just now', 'action': 'log_activity_time:now'},
                    {'text': '🌅 Morning (9 AM)', 'action': 'log_activity_time:morning'},
                    {'text': '☀️ Afternoon (2 PM)', 'action': 'log_activity_time:afternoon'},
                    {'text': '🌆 Evening (6 PM)', 'action': 'log_activity_time:evening'},
                    {'text': '🌙 Night (9 PM)', 'action': 'log_activity_time:night'},
                    {'text': '🕐 Custom time', 'action': 'log_activity_time:custom'}
                ],
                'workflow': 'activity_logging',
                'step': 'select_time',
                'state': state
            }
            
        except (ValueError, TypeError) as e:
            return {
                'message': '❌ I couldn\'t understand that date. Please try again with a format like:\n• "March 15"\n• "last Monday"\n• "3 days ago"\n• "yesterday"',
                'workflow': 'activity_logging',
                'step': 'awaiting_custom_date',
                'state': state
            }
    
    def handle_custom_time(self, user_id: int, time_text: str, state: Dict) -> Dict:
        """Parse custom time input"""
        import re
        from dateutil import parser
        
        try:
            # Try to parse the time
            parsed_time = parser.parse(time_text, fuzzy=True)
            
            # Get the date from state
            date_str = state.get('activity_date', datetime.now().date().isoformat())
            date = datetime.fromisoformat(date_str)
            
            # Combine date with parsed time
            start_time = datetime.combine(date, parsed_time.time())
            
            # Don't allow future times
            if start_time > datetime.now():
                return {
                    'message': 'Please enter a time in the past.',
                    'workflow': 'activity_logging',
                    'step': 'awaiting_custom_time',
                    'state': state
                }
            
            # Save time and continue to duration selection
            state['start_time'] = start_time.isoformat()
            state.pop('awaiting_custom_time', None)
            
            activity_name = state.get('activity_name', 'this activity')
            activity_icon = state.get('activity_icon', '📋')
            default_duration = state.get('default_duration', 30)
            
            # Suggest durations
            durations = [
                default_duration,
                default_duration - 15 if default_duration > 15 else 15,
                default_duration + 15,
                default_duration + 30
            ]
            durations = sorted(set([d for d in durations if d > 0]))
            
            return {
                'message': f'How long did you do {activity_icon} {activity_name}? ⏱️',
                'buttons': [
                    {'text': f'⏱️ {d} minutes', 'action': f'log_activity_duration:{d}'}
                    for d in durations[:4]
                ] + [
                    {'text': '✏️ Custom duration', 'action': 'log_activity_duration:custom'}
                ],
                'workflow': 'activity_logging',
                'step': 'select_duration',
                'state': state
            }
            
        except (ValueError, TypeError):
            return {
                'message': 'I couldn\'t understand that time. Please try again (e.g., "10:30 AM", "3:45 PM", or "14:00"):',
                'workflow': 'activity_logging',
                'step': 'awaiting_custom_time',
                'state': state
            }
