# activity_intent_detector.py
# Detect health activity intents from natural language with unit conversion

import re
from .health_activity_logger import HealthActivityLogger
from .unit_converter import get_unit_converter
import logging

logger = logging.getLogger(__name__)

class ActivityIntentDetector:
    """Detect and extract health activity information from user messages with smart unit conversion"""
    
    def __init__(self):
        self.logger = HealthActivityLogger()
        self.unit_converter = get_unit_converter()
        
        # Number patterns
        self.number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'a': 1, 'an': 1, 'half': 0.5, 'quarter': 0.25
        }
    
    def extract_number(self, text):
        """Extract numeric value from text with decimal support"""
        text_lower = text.lower()
        
        # Try to find digit numbers first (with or without units attached)
        # Match patterns like: 500, 500ml, 500 ml, 2.5, 2.5kg, 1.5 liters
        digit_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ml|l|liters?|litres?|kg|lbs?|pounds?|oz|ounces?|glasses?|bottles?|cups?|hours?|hrs?|h|minutes?|mins?|m)?', text_lower)
        if digit_match:
            return float(digit_match.group(1))
        
        # Try word numbers
        for word, num in self.number_words.items():
            if f' {word} ' in f' {text_lower} ':
                return num
        
        return None
    
    def extract_unit(self, text, activity_type=None):
        """
        Extract unit from text with activity context
        
        Args:
            text: User input text
            activity_type: Optional activity type for context
            
        Returns:
            Detected unit or None if no explicit unit found
        """
        text_lower = text.lower()
        
        # Unit patterns with word boundaries to avoid false matches
        unit_patterns = {
            # Water units (order matters - check specific units first)
            r'\b(ml|milliliters?|millilitres?)\b': 'ml', 
            r'\b(liters?|litres?)\b': 'liters',
            r'\b\bl\b': 'liters',  # Single 'l' with word boundaries
            r'\b(glasses?|glass)\b': 'glasses',
            r'\b(bottles?|bottle)\b': 'bottles',
            r'\b(cups?|cup)\b': 'cups',
            r'\b(oz|ounces?|ounce)\b': 'oz',
            
            # Sleep units
            r'\b(hours?|hrs?)\b': 'hours',
            r'\b\bh\b': 'hours',  # Single 'h' with word boundaries
            r'\b(minutes?|mins?)\b': 'minutes',
            r'\b\bm\b': 'minutes',  # Single 'm' with word boundaries (but be careful)
            
            # Exercise units  
            r'\b(minutes?|mins?)\b': 'minutes',
            r'\b(hours?|hrs?)\b': 'hours',
            
            # Weight units
            r'\b(kg|kilograms?|kilogram)\b': 'kg',
            r'\b(lbs?|pounds?|pound|lb)\b': 'lbs'
        }
        
        # Find the first matching unit
        for pattern, unit in unit_patterns.items():
            if re.search(pattern, text_lower):
                return unit
                
        # CRITICAL FIX: Return None if no explicit unit found
        # Do NOT default to standard unit - let caller handle missing units
        return None
    
    def detect_water_intake(self, text):
        """Detect water intake from text with unit conversion"""
        text_lower = text.lower()
        
        # Check for water-related keywords
        water_keywords = ['water', 'drink', 'drank', 'glass', 'glasses', 'bottle', 'bottles', 'hydrat', 'fluid']
        if not any(keyword in text_lower for keyword in water_keywords):
            return None
        
        # Make sure it's actually about water/drinking
        if any(keyword in text_lower for keyword in ['water', 'glass', 'bottle', 'hydrat', 'fluid']):
            # Extract quantity and unit
            value = self.extract_number(text)
            if value:
                # Extract unit from text
                detected_unit = self.extract_unit(text, 'water')
                
                # CRITICAL FIX: Handle missing units
                if detected_unit is None:
                    # No unit specified - return incomplete detection for clarification
                    return {
                        'activity_type': 'water',
                        'value': value,
                        'unit': None,
                        'original_value': value,
                        'original_unit': None,
                        'notes': text,
                        'needs_unit_clarification': True
                    }
                
                # Convert to standard unit (glasses)
                converted_value, standard_unit = self.unit_converter.convert_to_standard_unit(
                    'water', value, detected_unit
                )
                
                # Create conversion message for user feedback
                conversion_msg = self.unit_converter.format_conversion_message(
                    value, detected_unit, converted_value, standard_unit
                )
                
                notes = text
                if conversion_msg:
                    notes += f" {conversion_msg}"
                
                logger.info(f"Water detected: {value} {detected_unit} → {converted_value} {standard_unit}")
                
                return {
                    'activity_type': 'water',
                    'value': converted_value,
                    'unit': standard_unit,
                    'original_value': value,
                    'original_unit': detected_unit,
                    'notes': notes
                }
        
        return None
    
    def detect_sleep(self, text):
        """Detect sleep from text with unit conversion"""
        text_lower = text.lower()
        
        # Check for sleep-related keywords
        sleep_keywords = ['sleep', 'slept', 'rest', 'nap', 'napped', 'bedtime', 'bed']
        if not any(keyword in text_lower for keyword in sleep_keywords):
            return None
        
        # Extract value and unit
        value = self.extract_number(text)
        if value:
            detected_unit = self.extract_unit(text, 'sleep')
            
            # CRITICAL FIX: Handle missing units
            if detected_unit is None:
                # No unit specified - return incomplete detection for clarification
                return {
                    'activity_type': 'sleep',
                    'value': value,
                    'unit': None,
                    'original_value': value,
                    'original_unit': None,
                    'notes': text,
                    'needs_unit_clarification': True
                }
            
            # Convert to standard unit (hours)
            converted_value, standard_unit = self.unit_converter.convert_to_standard_unit(
                'sleep', value, detected_unit
            )
            
            # Create conversion message
            conversion_msg = self.unit_converter.format_conversion_message(
                value, detected_unit, converted_value, standard_unit
            )
            
            notes = text
            if conversion_msg:
                notes += f" {conversion_msg}"
            
            logger.info(f"Sleep detected: {value} {detected_unit} → {converted_value} {standard_unit}")
            
            return {
                'activity_type': 'sleep',
                'value': converted_value,
                'unit': standard_unit,
                'original_value': value,
                'original_unit': detected_unit,
                'notes': notes
            }
        
        return None
    
    def detect_weight(self, text):
        """Detect weight update from text with unit conversion"""
        text_lower = text.lower()
        
        # Check for weight-related keywords
        weight_keywords = ['weight', 'weigh', 'kg', 'pounds', 'lbs', 'scale']
        if not any(keyword in text_lower for keyword in weight_keywords):
            return None
        
        # Extract value and unit
        value = self.extract_number(text)
        if value:
            detected_unit = self.extract_unit(text, 'weight')
            
            # CRITICAL FIX: Handle missing units
            if detected_unit is None:
                # No unit specified - return incomplete detection for clarification
                return {
                    'activity_type': 'weight',
                    'value': value,
                    'unit': None,
                    'original_value': value,
                    'original_unit': None,
                    'notes': text,
                    'needs_unit_clarification': True
                }
            
            # Convert to standard unit (kg)
            converted_value, standard_unit = self.unit_converter.convert_to_standard_unit(
                'weight', value, detected_unit
            )
            
            # Create conversion message
            conversion_msg = self.unit_converter.format_conversion_message(
                value, detected_unit, converted_value, standard_unit
            )
            
            notes = text
            if conversion_msg:
                notes += f" {conversion_msg}"
            
            logger.info(f"Weight detected: {value} {detected_unit} → {converted_value} {standard_unit}")
            
            return {
                'activity_type': 'weight',
                'value': converted_value,
                'unit': standard_unit,
                'original_value': value,
                'original_unit': detected_unit,
                'notes': notes
            }
        
        return None
    
    def detect_exercise(self, text):
        """Detect exercise from text with enhanced sport detection and unit conversion"""
        try:
            from .enhanced_exercise_detector import get_enhanced_exercise_detector
            
            enhanced_detector = get_enhanced_exercise_detector()
            result = enhanced_detector.detect_exercise_with_context(text)
            
            if result and not result.get('needs_duration'):
                # Complete exercise detection with duration
                return result
            elif result and result.get('needs_duration'):
                # Exercise detected but no duration - return for clarification
                return {
                    'activity_type': 'exercise',
                    'activity_name': result.get('activity_name', 'exercise'),
                    'value': None,
                    'unit': 'minutes',
                    'notes': text,
                    'needs_clarification': True
                }
            
            return None
            
        except ImportError:
            # Fallback to original detection if enhanced detector not available
            return self._detect_exercise_fallback(text)
    
    def _detect_exercise_fallback(self, text):
        """Fallback exercise detection method (original implementation)"""
        text_lower = text.lower()
        
        # Expanded exercise keywords including sports and activities
        exercise_keywords = [
            # Traditional exercise
            'exercise', 'exercised', 'workout', 'gym', 'train', 'training',
            'run', 'ran', 'running', 'walk', 'walked', 'walking', 'jog', 'jogged', 'jogging',
            
            # Sports
            'badminton', 'tennis', 'football', 'soccer', 'basketball', 'volleyball',
            'cricket', 'baseball', 'hockey', 'golf', 'swimming', 'swim', 'swam',
            'cycling', 'bike', 'biking', 'biked',
            
            # Fitness activities
            'yoga', 'pilates', 'aerobics', 'zumba', 'dancing', 'dance', 'danced',
            'hiking', 'climbing', 'lifting', 'weights', 'cardio', 'stretching',
            'crossfit', 'spinning', 'rowing', 'boxing', 'martial arts',
            
            # Activity verbs
            'played', 'did', 'practiced', 'attended'
        ]
        
        # Check for exercise-related keywords
        if not any(keyword in text_lower for keyword in exercise_keywords):
            return None
        
        # Extract duration
        value = self.extract_number(text)
        if value:
            detected_unit = self.extract_unit(text, 'exercise')
            
            # Convert to standard unit (minutes)
            converted_value, standard_unit = self.unit_converter.convert_to_standard_unit(
                'exercise', value, detected_unit
            )
            
            # Create conversion message
            conversion_msg = self.unit_converter.format_conversion_message(
                value, detected_unit, converted_value, standard_unit
            )
            
            notes = text
            if conversion_msg:
                notes += f" {conversion_msg}"
            
            logger.info(f"Exercise detected: {value} {detected_unit} → {converted_value} {standard_unit}")
            
            return {
                'activity_type': 'exercise',
                'value': converted_value,
                'unit': standard_unit,
                'original_value': value,
                'original_unit': detected_unit,
                'notes': notes
            }
        
        return None
    
    def detect_all_activities(self, text):
        """Detect all possible activities from text with confidence scoring"""
        activities = []
        
        # Try each detector with confidence scoring
        detectors = [
            ('water', self.detect_water_intake),
            ('sleep', self.detect_sleep),
            ('weight', self.detect_weight),
            ('exercise', self.detect_exercise)
        ]
        
        for activity_type, detector in detectors:
            result = detector(text)
            if result:
                # Add confidence scoring based on detection quality
                confidence = self._calculate_confidence(text, activity_type, result)
                result['confidence'] = confidence
                activities.append(result)
        
        # Sort by confidence (highest first)
        activities.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return activities
    
    def _calculate_confidence(self, text, activity_type, result):
        """
        Calculate confidence score for activity detection
        
        Args:
            text: Original user message
            activity_type: Type of activity detected
            result: Detection result dict
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        text_lower = text.lower()
        confidence = 0.0
        
        # Base confidence for having a value
        if result.get('value') is not None:
            confidence += 0.4
        
        # Keyword match scoring
        keyword_scores = {
            'water': {
                'high': ['water', 'drank', 'drink', 'hydrat'],
                'medium': ['glass', 'bottle', 'fluid', 'liquid']
            },
            'sleep': {
                'high': ['sleep', 'slept', 'rest'],
                'medium': ['nap', 'bed', 'bedtime']
            },
            'weight': {
                'high': ['weight', 'weigh', 'scale'],
                'medium': ['kg', 'lbs', 'pounds']
            },
            'exercise': {
                'high': ['exercise', 'workout', 'gym', 'train'],
                'medium': ['run', 'walk', 'played', 'sport']
            }
        }
        
        if activity_type in keyword_scores:
            # High confidence keywords
            for keyword in keyword_scores[activity_type].get('high', []):
                if keyword in text_lower:
                    confidence += 0.3
                    break
            
            # Medium confidence keywords
            for keyword in keyword_scores[activity_type].get('medium', []):
                if keyword in text_lower:
                    confidence += 0.2
                    break
        
        # Unit detection bonus
        if result.get('unit') is not None:
            confidence += 0.2
        
        # Complete data bonus
        if not result.get('needs_unit_clarification') and not result.get('needs_clarification'):
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def should_suggest_activities(self, text, mood_logged=False):
        """Determine if we should suggest predefined activities"""
        # If mood is already logged and no specific activity detected
        if mood_logged:
            activities = self.detect_all_activities(text)
            if not activities:
                return True
        
        return False
