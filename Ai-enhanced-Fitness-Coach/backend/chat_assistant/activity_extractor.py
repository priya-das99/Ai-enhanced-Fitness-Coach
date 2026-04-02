"""
Activity Extractor - LLM-based extraction of activity details from natural language

Extracts:
- Activity type
- Date (today, yesterday, specific date)
- Time (morning, afternoon, evening, specific time)
- Duration (minutes)
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from chat_assistant.llm_service import LLMService


class ActivityExtractor:
    """Extracts activity details from natural language"""
    
    def __init__(self):
        self.llm_service = LLMService()
        
        # Activity keywords mapping
        self.activity_keywords = {
            'book_reading': ['book', 'reading', 'read'],
            'meditation': ['meditat', 'mindful'],
            'journaling': ['journal', 'writing', 'wrote'],
            'breathing': ['breath', 'breathing exercise'],
            'hiking': ['hik', 'trek', 'trail'],
            'swimming': ['swim', 'pool'],
            'badminton': ['badminton'],
            'football': ['football', 'soccer'],
            'calisthenics': ['calisthenics', 'bodyweight'],
            'running': ['run', 'jog', 'running'],
            'gym': ['gym', 'workout', 'weight'],
            'yoga': ['yoga'],
            'cycling': ['cycl', 'bike', 'biking'],
            'walking': ['walk']
        }
    
    def extract_from_message(self, message: str) -> Dict:
        """
        Extract activity details from user message
        
        Returns:
        {
            'activity_id': str or None,
            'date': 'today'/'yesterday'/date or None,
            'time': 'morning'/'afternoon'/'evening'/'now' or None,
            'duration': int or None,
            'confidence': float (0-1)
        }
        """
        message_lower = message.lower()
        
        # Extract activity
        activity_id = self._extract_activity(message_lower)
        
        # Extract date
        date = self._extract_date(message_lower)
        
        # Extract time
        time = self._extract_time(message_lower)
        
        # Extract duration
        duration = self._extract_duration(message_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(activity_id, date, time, duration)
        
        return {
            'activity_id': activity_id,
            'date': date,
            'time': time,
            'duration': duration,
            'confidence': confidence
        }
    
    def _extract_activity(self, message: str) -> Optional[str]:
        """Extract activity from message using keywords"""
        for activity_id, keywords in self.activity_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return activity_id
        return None
    
    def _extract_date(self, message: str) -> Optional[str]:
        """Extract date from message"""
        if 'today' in message or 'just' in message:
            return 'today'
        elif 'yesterday' in message:
            return 'yesterday'
        elif '2 days ago' in message or 'two days ago' in message:
            return '2days'
        elif 'this morning' in message or 'this afternoon' in message or 'this evening' in message:
            return 'today'
        
        # Check for specific dates (e.g., "on Monday", "last week")
        if 'monday' in message or 'tuesday' in message or 'wednesday' in message:
            return 'custom'  # Will need to handle this
        
        return None
    
    def _extract_time(self, message: str) -> Optional[str]:
        """Extract time from message"""
        if 'just now' in message or 'just finished' in message or 'just did' in message:
            return 'now'
        elif 'morning' in message or 'am' in message:
            return 'morning'
        elif 'afternoon' in message or 'pm' in message and ('1' in message or '2' in message or '3' in message):
            return 'afternoon'
        elif 'evening' in message or 'pm' in message and ('6' in message or '7' in message or '8' in message):
            return 'evening'
        elif 'night' in message or 'pm' in message and ('9' in message or '10' in message):
            return 'night'
        
        return None
    
    def _extract_duration(self, message: str) -> Optional[int]:
        """Extract duration in minutes from message"""
        # Look for patterns like "30 minutes", "1 hour", "45 min"
        
        # Pattern: X minutes/mins/min
        minute_pattern = r'(\d+)\s*(?:minute|minutes|mins|min)'
        match = re.search(minute_pattern, message)
        if match:
            return int(match.group(1))
        
        # Pattern: X hours/hour/hr
        hour_pattern = r'(\d+)\s*(?:hour|hours|hr|hrs)'
        match = re.search(hour_pattern, message)
        if match:
            return int(match.group(1)) * 60
        
        # Pattern: X.5 hours (e.g., "1.5 hours")
        decimal_hour_pattern = r'(\d+\.?\d*)\s*(?:hour|hours)'
        match = re.search(decimal_hour_pattern, message)
        if match:
            return int(float(match.group(1)) * 60)
        
        # Pattern: "for an hour"
        if 'for an hour' in message or 'for 1 hour' in message:
            return 60
        
        # Pattern: "for half an hour"
        if 'half an hour' in message or 'half hour' in message:
            return 30
        
        return None
    
    def _calculate_confidence(self, activity_id, date, time, duration) -> float:
        """Calculate confidence score based on extracted information"""
        score = 0.0
        
        if activity_id:
            score += 0.4  # Activity is most important
        if date:
            score += 0.2
        if time:
            score += 0.2
        if duration:
            score += 0.2
        
        return score
    
    def extract_with_llm(self, message: str, available_activities: list) -> Dict:
        """
        Use LLM to extract activity details (fallback for complex cases)
        """
        activity_list = ', '.join([f"{a['id']} ({a['name']})" for a in available_activities])
        
        prompt = f"""Extract activity logging details from this message:
"{message}"

Available activities: {activity_list}

Return JSON with:
{{
    "activity_id": "activity_id or null",
    "date": "today/yesterday/2days or null",
    "time": "morning/afternoon/evening/night/now or null",
    "duration": number (minutes) or null
}}

Only use activity IDs from the available list. If unsure, return null.
"""
        
        try:
            result = self.llm_service.call_structured(
                prompt=prompt,
                schema={
                    "activity_id": {"type": "string", "nullable": True},
                    "date": {"type": "string", "nullable": True},
                    "time": {"type": "string", "nullable": True},
                    "duration": {"type": "integer", "nullable": True}
                }
            )
            
            result['confidence'] = 0.8  # LLM extraction has high confidence
            return result
            
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return {
                'activity_id': None,
                'date': None,
                'time': None,
                'duration': None,
                'confidence': 0.0
            }
    
    def format_confirmation_message(self, extracted: Dict, activity_name: str) -> str:
        """Format a confirmation message for extracted details"""
        parts = [f"I understood: {activity_name}"]
        
        if extracted.get('date'):
            date_display = {
                'today': 'today',
                'yesterday': 'yesterday',
                '2days': '2 days ago'
            }.get(extracted['date'], extracted['date'])
            parts.append(f"on {date_display}")
        
        if extracted.get('time'):
            time_display = {
                'now': 'just now',
                'morning': 'in the morning',
                'afternoon': 'in the afternoon',
                'evening': 'in the evening',
                'night': 'at night'
            }.get(extracted['time'], extracted['time'])
            parts.append(time_display)
        
        if extracted.get('duration'):
            parts.append(f"for {extracted['duration']} minutes")
        
        message = ' '.join(parts) + '.'
        
        # Add what's missing
        missing = []
        if not extracted.get('date'):
            missing.append('date')
        if not extracted.get('time'):
            missing.append('time')
        if not extracted.get('duration'):
            missing.append('duration')
        
        if missing:
            message += f"\n\nI'll ask you for the {', '.join(missing)}."
        
        return message
