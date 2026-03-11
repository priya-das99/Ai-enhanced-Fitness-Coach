# enhanced_exercise_detector.py
# Advanced exercise detection with sports, activities, and context awareness

import re
import logging
from typing import Dict, List, Optional, Tuple
from .unit_converter import get_unit_converter

logger = logging.getLogger(__name__)

class EnhancedExerciseDetector:
    """
    Advanced exercise detection system that recognizes:
    1. Traditional exercises (gym, running, walking)
    2. Sports (badminton, tennis, football, etc.)
    3. Fitness activities (yoga, pilates, dancing)
    4. Casual activities (played, did, practiced)
    5. Context patterns (played X for Y minutes)
    """
    
    def __init__(self):
        self.unit_converter = get_unit_converter()
        
        # Comprehensive exercise vocabulary
        self.EXERCISE_CATEGORIES = {
            'traditional_exercise': [
                'exercise', 'exercised', 'workout', 'gym', 'training', 'train', 'trained',
                'fitness', 'cardio', 'strength', 'lifting', 'weights', 'weightlifting'
            ],
            
            'running_walking': [
                'run', 'ran', 'running', 'jog', 'jogged', 'jogging',
                'walk', 'walked', 'walking', 'hike', 'hiked', 'hiking'
            ],
            
            'racket_sports': [
                'badminton', 'tennis', 'squash', 'table tennis', 'ping pong',
                'racquetball', 'paddle tennis'
            ],
            
            'team_sports': [
                'football', 'soccer', 'basketball', 'volleyball', 'cricket',
                'baseball', 'hockey', 'rugby', 'handball', 'netball'
            ],
            
            'individual_sports': [
                'swimming', 'swim', 'swam', 'cycling', 'bike', 'biking', 'biked',
                'golf', 'boxing', 'wrestling', 'fencing', 'archery', 'bowling'
            ],
            
            'fitness_classes': [
                'yoga', 'pilates', 'aerobics', 'zumba', 'spinning', 'crossfit',
                'kickboxing', 'martial arts', 'karate', 'taekwondo', 'judo'
            ],
            
            'dance_activities': [
                'dancing', 'dance', 'danced', 'ballet', 'salsa', 'hip hop',
                'ballroom', 'contemporary', 'jazz dance'
            ],
            
            'outdoor_activities': [
                'climbing', 'rock climbing', 'mountaineering', 'skiing', 'snowboarding',
                'surfing', 'kayaking', 'rowing', 'sailing', 'skateboarding'
            ],
            
            'stretching_recovery': [
                'stretching', 'stretch', 'stretched', 'flexibility', 'mobility',
                'warm up', 'cool down', 'recovery'
            ]
        }
        
        # Activity verbs that indicate exercise
        self.ACTIVITY_VERBS = [
            'played', 'did', 'practiced', 'attended', 'went', 'participated',
            'competed', 'performed', 'engaged in', 'took part in'
        ]
        
        # Duration indicators
        self.DURATION_PATTERNS = [
            r'for\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)',
            r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)\s+of',
            r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)\s*$',
            r'(\d+(?:\.\d+)?)\s*-\s*(minute|min|hour|hr)\s+',
        ]
        
        # Context patterns for "played X for Y" structure
        self.CONTEXT_PATTERNS = [
            r'played\s+(\w+(?:\s+\w+)?)\s+for\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)',
            r'did\s+(\w+(?:\s+\w+)?)\s+for\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)',
            r'went\s+(\w+(?:\s+\w+)?)\s+for\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)',
            r'practiced\s+(\w+(?:\s+\w+)?)\s+for\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|h|m)',
        ]
    
    def get_all_exercise_keywords(self) -> List[str]:
        """Get flattened list of all exercise keywords"""
        keywords = []
        for category in self.EXERCISE_CATEGORIES.values():
            keywords.extend(category)
        keywords.extend(self.ACTIVITY_VERBS)
        return keywords
    
    def detect_exercise_activity(self, text: str) -> Optional[str]:
        """
        Detect what type of exercise/sport is mentioned
        
        Returns:
            Activity name or None
        """
        text_lower = text.lower()
        
        # Check each category for matches
        for category, activities in self.EXERCISE_CATEGORIES.items():
            for activity in activities:
                if re.search(r'\b' + re.escape(activity) + r'\b', text_lower):
                    return activity
        
        # Check for context patterns (played X, did X)
        for pattern in self.CONTEXT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                activity_name = match.group(1).strip()
                # Validate that it's likely an exercise/sport
                if self._is_likely_exercise_activity(activity_name):
                    return activity_name
        
        return None
    
    def _is_likely_exercise_activity(self, activity: str) -> bool:
        """
        Check if an activity name is likely an exercise/sport
        
        Args:
            activity: Activity name extracted from context
            
        Returns:
            True if likely an exercise activity
        """
        activity_lower = activity.lower()
        
        # Check against known activities
        all_activities = self.get_all_exercise_keywords()
        if activity_lower in all_activities:
            return True
        
        # Check for partial matches
        for known_activity in all_activities:
            if known_activity in activity_lower or activity_lower in known_activity:
                return True
        
        # Common sport/exercise patterns
        exercise_indicators = [
            'ball', 'sport', 'game', 'class', 'session', 'training',
            'fitness', 'gym', 'club', 'team', 'match', 'practice'
        ]
        
        for indicator in exercise_indicators:
            if indicator in activity_lower:
                return True
        
        return False
    
    def extract_duration(self, text: str) -> Optional[Tuple[float, str]]:
        """
        Extract duration from text using multiple patterns
        
        Returns:
            Tuple of (value, unit) or None
        """
        text_lower = text.lower()
        
        # Try each duration pattern
        for pattern in self.DURATION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2)
                    return value, unit
                except (ValueError, IndexError):
                    continue
        
        # Try context patterns that include duration
        for pattern in self.CONTEXT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(2))
                    unit = match.group(3)
                    return value, unit
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def detect_exercise_with_context(self, text: str) -> Optional[Dict]:
        """
        Main detection method that combines activity and duration detection
        
        Args:
            text: User input text
            
        Returns:
            Dict with exercise details or None
        """
        text_lower = text.lower()
        
        # First, check if any exercise-related keywords are present
        has_exercise_keyword = False
        detected_activity = None
        
        # Check for direct exercise keywords
        all_keywords = self.get_all_exercise_keywords()
        for keyword in all_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                has_exercise_keyword = True
                detected_activity = keyword
                break
        
        # Check for context patterns (played X, did X)
        if not has_exercise_keyword:
            for pattern in self.CONTEXT_PATTERNS:
                match = re.search(pattern, text_lower)
                if match:
                    activity_name = match.group(1).strip()
                    if self._is_likely_exercise_activity(activity_name):
                        has_exercise_keyword = True
                        detected_activity = activity_name
                        break
        
        # If no exercise keywords found, return None
        if not has_exercise_keyword:
            return None
        
        # Extract duration
        duration_info = self.extract_duration(text)
        if not duration_info:
            # No duration found - this might be a general exercise mention
            # Return basic info for clarification
            return {
                'activity_type': 'exercise',
                'activity_name': detected_activity,
                'value': None,
                'unit': None,
                'needs_duration': True,
                'original_text': text
            }
        
        value, unit = duration_info
        
        # Convert to standard unit (minutes)
        converted_value, standard_unit = self.unit_converter.convert_to_standard_unit(
            'exercise', value, unit
        )
        
        # Create conversion message
        conversion_msg = self.unit_converter.format_conversion_message(
            value, unit, converted_value, standard_unit
        )
        
        notes = text
        if conversion_msg:
            notes += f" {conversion_msg}"
        
        logger.info(f"Exercise detected: {detected_activity} - {value} {unit} → {converted_value} {standard_unit}")
        
        return {
            'activity_type': 'exercise',
            'activity_name': detected_activity,
            'value': converted_value,
            'unit': standard_unit,
            'original_value': value,
            'original_unit': unit,
            'notes': notes,
            'needs_duration': False
        }
    
    def get_exercise_suggestions(self, detected_activity: str = None) -> List[str]:
        """
        Get exercise suggestions based on detected activity or general suggestions
        
        Args:
            detected_activity: Optional detected activity for related suggestions
            
        Returns:
            List of exercise suggestions
        """
        if not detected_activity:
            return [
                "Try a 30-minute walk",
                "Do 15 minutes of stretching", 
                "Practice yoga for 20 minutes",
                "Go for a 45-minute bike ride"
            ]
        
        # Activity-specific suggestions
        activity_lower = detected_activity.lower()
        
        if any(sport in activity_lower for sport in ['badminton', 'tennis', 'squash']):
            return [
                "Great racket sport choice!",
                "Try playing for 45-60 minutes for good cardio",
                "Don't forget to warm up and cool down"
            ]
        elif any(sport in activity_lower for sport in ['football', 'soccer', 'basketball']):
            return [
                "Team sports are excellent for fitness!",
                "Aim for 60-90 minutes of play",
                "Great for both cardio and coordination"
            ]
        elif 'yoga' in activity_lower or 'pilates' in activity_lower:
            return [
                "Excellent for flexibility and strength!",
                "20-60 minutes is a good session length",
                "Perfect for stress relief too"
            ]
        else:
            return [
                f"Great choice with {detected_activity}!",
                "Keep up the regular activity",
                "Consistency is key for fitness"
            ]


# Global instance
_enhanced_detector = None

def get_enhanced_exercise_detector() -> EnhancedExerciseDetector:
    """Get or create global EnhancedExerciseDetector instance"""
    global _enhanced_detector
    if _enhanced_detector is None:
        _enhanced_detector = EnhancedExerciseDetector()
    return _enhanced_detector