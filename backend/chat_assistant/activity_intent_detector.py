# activity_intent_detector.py
# Detect health activity intents from natural language

import re
from .health_activity_logger import HealthActivityLogger

class ActivityIntentDetector:
    """Detect and extract health activity information from user messages"""
    
    def __init__(self):
        self.logger = HealthActivityLogger()
        
        # Number patterns
        self.number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'a': 1, 'an': 1
        }
    
    def extract_number(self, text):
        """Extract numeric value from text"""
        text_lower = text.lower()
        
        # Try to find digit numbers first (with or without units attached)
        # Match patterns like: 500, 500ml, 500 ml, 2.5, 2.5kg
        digit_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ml|l|kg|lbs|oz|glasses?|hours?|minutes?|mins?)?', text_lower)
        if digit_match:
            return float(digit_match.group(1))
        
        # Try word numbers
        for word, num in self.number_words.items():
            if f' {word} ' in f' {text_lower} ':
                return num
        
        return None
    
    def detect_water_intake(self, text):
        """Detect water intake from text"""
        text_lower = text.lower()
        
        # Check for water-related keywords
        water_keywords = ['water', 'drink', 'drank', 'glass', 'glasses', 'bottle', 'bottles', 'hydrat']
        if not any(keyword in text_lower for keyword in water_keywords):
            return None
        
        # Make sure it's actually about water/drinking
        # Avoid false positives from words like "drank" in other contexts
        if 'water' in text_lower or 'glass' in text_lower or 'bottle' in text_lower or 'hydrat' in text_lower:
            # Extract quantity
            value = self.extract_number(text)
            if value:
                # Detect unit - check for ml, liters, or default to glasses
                unit = 'glasses'
                if 'ml' in text_lower or 'milliliter' in text_lower:
                    unit = 'ml'
                elif 'liter' in text_lower or 'litre' in text_lower or ' l ' in text_lower:
                    unit = 'liters'
                elif 'oz' in text_lower or 'ounce' in text_lower:
                    unit = 'oz'
                
                return {
                    'activity_type': 'water',
                    'value': value,
                    'unit': unit,
                    'notes': text
                }
        
        return None
    
    def detect_sleep(self, text):
        """Detect sleep from text"""
        text_lower = text.lower()
        
        # Check for sleep-related keywords
        sleep_keywords = ['sleep', 'slept', 'rest', 'nap', 'napped']
        if not any(keyword in text_lower for keyword in sleep_keywords):
            return None
        
        # Extract hours
        value = self.extract_number(text)
        if value:
            return {
                'activity_type': 'sleep',
                'value': value,
                'unit': 'hours',
                'notes': text
            }
        
        return None
    
    def detect_weight(self, text):
        """Detect weight update from text"""
        text_lower = text.lower()
        
        # Check for weight-related keywords
        weight_keywords = ['weight', 'weigh', 'kg', 'pounds', 'lbs']
        if not any(keyword in text_lower for keyword in weight_keywords):
            return None
        
        # Extract value
        value = self.extract_number(text)
        if value:
            # Detect unit
            unit = 'kg'
            if 'pound' in text_lower or 'lbs' in text_lower or 'lb' in text_lower:
                unit = 'lbs'
            
            return {
                'activity_type': 'weight',
                'value': value,
                'unit': unit,
                'notes': text
            }
        
        return None
    
    def detect_exercise(self, text):
        """Detect exercise from text"""
        text_lower = text.lower()
        
        # Check for exercise-related keywords (must be explicit)
        exercise_keywords = ['exercise', 'exercised', 'workout', 'gym', 'run', 'ran', 'walk', 'walked', 'jog', 'jogged', 'train', 'training']
        if not any(keyword in text_lower for keyword in exercise_keywords):
            return None
        
        # Extract duration (look for minutes/hours context)
        value = self.extract_number(text)
        if value:
            # Check if it's actually about duration
            if 'minute' in text_lower or 'hour' in text_lower or 'min' in text_lower:
                return {
                    'activity_type': 'exercise',
                    'value': value,
                    'unit': 'minutes',
                    'notes': text
                }
        
        return None
    
    def detect_all_activities(self, text):
        """Detect all possible activities from text"""
        activities = []
        
        # Try each detector
        detectors = [
            self.detect_water_intake,
            self.detect_sleep,
            self.detect_weight,
            self.detect_exercise
        ]
        
        for detector in detectors:
            result = detector(text)
            if result:
                activities.append(result)
        
        return activities
    
    def should_suggest_activities(self, text, mood_logged=False):
        """Determine if we should suggest predefined activities"""
        # If mood is already logged and no specific activity detected
        if mood_logged:
            activities = self.detect_all_activities(text)
            if not activities:
                return True
        
        return False
