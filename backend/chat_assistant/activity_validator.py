# activity_validator.py
# Comprehensive input validation for all activity types

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ActivityValidator:
    """
    Comprehensive validation system for all activity types
    Prevents unrealistic values and provides helpful user guidance
    """
    
    VALIDATION_RULES = {
        'water': {
            'min': 1,
            'max': 20,
            'typical_range': (6, 12),
            'unit': 'glasses',
            'warning_threshold': 15,
            'decimal_allowed': False,
            'context': '1 glass = ~250ml',
            'health_note': 'Typical daily intake is 6-12 glasses'
        },
        
        'sleep': {
            'min': 1,
            'max': 16,
            'typical_range': (6, 9),
            'unit': 'hours',
            'warning_threshold': 12,
            'decimal_allowed': True,
            'context': 'Includes naps and nighttime sleep',
            'health_note': 'Recommended sleep is 7-9 hours per night'
        },
        
        'exercise': {
            'min': 5,
            'max': 240,  # 4 hours max (more realistic)
            'typical_range': (15, 90),
            'unit': 'minutes',
            'warning_threshold': 120,  # 2 hours (more reasonable)
            'decimal_allowed': False,
            'context': 'Any physical activity counts',
            'health_note': 'WHO recommends 150 minutes per week (21 min/day)'
        },
        
        'weight': {
            'min': 30,
            'max': 300,
            'typical_range': (50, 120),
            'unit': 'kg',
            'warning_threshold': 200,
            'decimal_allowed': True,
            'context': 'Current body weight',
            'health_note': 'Healthy BMI range varies by height'
        },
        
        'steps': {
            'min': 100,
            'max': 50000,
            'typical_range': (5000, 15000),
            'unit': 'steps',
            'warning_threshold': 30000,
            'decimal_allowed': False,
            'context': 'Daily step count from walking/running',
            'health_note': '10,000 steps per day is a common goal'
        },
        
        'calories': {
            'min': 50,
            'max': 5000,
            'typical_range': (200, 800),
            'unit': 'calories',
            'warning_threshold': 1500,
            'decimal_allowed': False,
            'context': 'Calories burned during exercise',
            'health_note': 'Varies greatly by activity intensity and duration'
        }
    }
    
    def validate_activity_input(self, activity_type: str, value: float) -> Dict:
        """
        Comprehensive validation for all activity types
        
        Returns:
            {
                'valid': bool,
                'needs_confirmation': bool (optional),
                'message': str (if invalid or needs confirmation)
            }
        """
        rules = self.VALIDATION_RULES.get(activity_type)
        if not rules:
            # Unknown activity type - allow it (extensibility)
            logger.warning(f"No validation rules for activity type: {activity_type}")
            return {'valid': True}
        
        # Check for negative values
        if value < 0:
            return {
                'valid': False,
                'message': "Negative values don't make sense! Please enter a positive number."
            }
        
        # Check for zero
        if value == 0:
            return {
                'valid': False,
                'message': "Please enter a value greater than 0, or say 'cancel' if you don't want to log anything."
            }
        
        # Check decimal restrictions
        if not rules['decimal_allowed'] and value != int(value):
            if activity_type == 'water':
                return {
                    'valid': False,
                    'message': "Please enter whole glasses (1, 2, 3, etc.). Partial glasses are hard to track accurately."
                }
            else:
                return {
                    'valid': False,
                    'message': f"Please enter whole {rules['unit']} only (no decimals)."
                }
        
        # Check minimum limits
        if value < rules['min']:
            return {
                'valid': False,
                'message': f"Please enter at least {rules['min']} {rules['unit']}. {rules['context']}."
            }
        
        # Check maximum limits with smart suggestions
        if value > rules['max']:
            suggestion = ""
            
            # If way too high, suggest a reasonable alternative
            if value > rules['max'] * 10:
                reasonable = rules['typical_range'][1]
                suggestion = f" Did you mean {reasonable}?"
            
            # Special messages for extreme cases
            if activity_type == 'water' and value >= 100:
                liters = value * 0.25
                return {
                    'valid': False,
                    'message': f"{value} glasses would be {liters:.1f} liters! That's dangerous. Please enter 1-20 glasses.{suggestion}"
                }
            elif activity_type == 'exercise' and value >= 1000:
                hours = value / 60
                return {
                    'valid': False,
                    'message': f"{value} minutes is over {hours:.1f} hours! Please enter 5-480 minutes.{suggestion}"
                }
            elif activity_type == 'steps' and value >= 100000:
                km = value * 0.0008  # Rough conversion
                return {
                    'valid': False,
                    'message': f"{value} steps would be ~{km:.0f}km! Please enter 100-50,000 steps.{suggestion}"
                }
            elif activity_type == 'weight' and value >= 400:
                return {
                    'valid': False,
                    'message': f"{value}kg is not realistic. Please enter 30-300kg. Check your units (kg vs lbs)?{suggestion}"
                }
            else:
                return {
                    'valid': False,
                    'message': f"{value} {rules['unit']} is too high! Please enter {rules['min']}-{rules['max']} {rules['unit']}.{suggestion}"
                }
        
        # Check warning threshold (high but not invalid)
        if value >= rules['warning_threshold']:
            return {
                'valid': True,
                'needs_confirmation': True,
                'message': f"{value} {rules['unit']} is quite high! {rules['health_note']}. Are you sure?"
            }
        
        # All validation passed!
        return {'valid': True}
    
    def get_activity_info(self, activity_type: str) -> Optional[Dict]:
        """Get validation rules and info for an activity type"""
        return self.VALIDATION_RULES.get(activity_type)
    
    def get_typical_range_message(self, activity_type: str) -> str:
        """Get a helpful message about typical ranges for an activity"""
        rules = self.VALIDATION_RULES.get(activity_type)
        if not rules:
            return ""
        
        min_val, max_val = rules['typical_range']
        return f"Typical range is {min_val}-{max_val} {rules['unit']}. {rules['health_note']}"