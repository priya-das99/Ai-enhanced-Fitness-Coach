# unit_converter.py
# Comprehensive unit conversion system with aliases

import logging

logger = logging.getLogger(__name__)

class UnitConverter:
    """
    Scalable unit conversion system for health activities
    Converts all units to standardized values for consistent storage
    """
    
    # Standard unit conversions (to base unit)
    CONVERSIONS = {
        "water": {
            "liters": 4,        # 1 liter = 4 glasses (250ml per glass)
            "ml": 0.004,        # 1 ml = 0.004 glasses
            "bottles": 2,       # 1 bottle = 2 glasses (500ml bottle)
            "glasses": 1,       # 1 glass = 1 glass (base unit)
            "cups": 1,          # 1 cup ≈ 1 glass
            "oz": 0.125         # 1 oz = 0.125 glasses (8 oz = 1 glass)
        },
        "sleep": {
            "hours": 1,         # 1 hour = 1 hour (base unit)
            "minutes": 0.0167   # 1 minute = 0.0167 hours (1/60)
        },
        "exercise": {
            "minutes": 1,       # 1 minute = 1 minute (base unit)
            "hours": 60,        # 1 hour = 60 minutes
            "hrs": 60           # Alternative hour format
        },
        "weight": {
            "kg": 1,            # 1 kg = 1 kg (base unit)
            "pounds": 0.453592, # 1 pound = 0.453592 kg
            "lbs": 0.453592,    # 1 lb = 0.453592 kg
            "lb": 0.453592      # Alternative lb format
        }
    }
    
    # Unit aliases - normalize user input variations
    UNIT_ALIASES = {
        # Water aliases
        "liter": "liters",
        "litre": "liters", 
        "l": "liters",
        "glass": "glasses",
        "bottle": "bottles",
        "cup": "cups",
        "ounce": "oz",
        "ounces": "oz",
        
        # Sleep aliases
        "hour": "hours",
        "hr": "hours",
        "hrs": "hours",
        "h": "hours",
        "minute": "minutes",
        "min": "minutes",
        "mins": "minutes",
        "m": "minutes",
        
        # Exercise aliases  
        "minute": "minutes",
        "min": "minutes",
        "mins": "minutes",
        "m": "minutes",
        "hour": "hours",
        "hr": "hours", 
        "hrs": "hours",
        "h": "hours",
        
        # Weight aliases
        "kilogram": "kg",
        "kilograms": "kg",
        "pound": "pounds",
        "lb": "lbs",
        "lbs": "lbs"
    }
    
    # Standard units for each activity (what we store in database)
    STANDARD_UNITS = {
        "water": "glasses",
        "sleep": "hours", 
        "exercise": "minutes",
        "weight": "kg"
    }
    
    def normalize_unit(self, unit: str) -> str:
        """
        Normalize unit variations to standard format
        
        Args:
            unit: Raw unit from user input (e.g., "liter", "hr", "min")
            
        Returns:
            Normalized unit (e.g., "liters", "hours", "minutes")
        """
        if not unit:
            return unit
            
        unit_lower = unit.lower().strip()
        
        # Remove plural 's' for lookup if not found directly
        normalized = self.UNIT_ALIASES.get(unit_lower)
        if normalized:
            return normalized
            
        # Try without 's' for plural forms not in aliases
        if unit_lower.endswith('s') and len(unit_lower) > 1:
            singular = unit_lower[:-1]
            normalized = self.UNIT_ALIASES.get(singular)
            if normalized:
                return normalized
        
        # Return original if no alias found
        return unit_lower
    
    def convert_to_standard_unit(self, activity: str, value: float, unit: str) -> tuple:
        """
        Convert value and unit to standard format for database storage
        
        Args:
            activity: Activity type (water, sleep, exercise, weight)
            value: Numeric value from user
            unit: Unit from user input
            
        Returns:
            tuple: (converted_value, standard_unit)
        """
        if not activity or not unit or value is None:
            return value, unit
            
        # Normalize the unit first
        normalized_unit = self.normalize_unit(unit)
        
        # Get conversion rules for this activity
        if activity not in self.CONVERSIONS:
            logger.warning(f"No conversion rules for activity: {activity}")
            return value, unit
            
        # Get multiplier for unit conversion
        multiplier = self.CONVERSIONS[activity].get(normalized_unit)
        if multiplier is None:
            logger.warning(f"No conversion for {activity} unit: {normalized_unit}")
            return value, unit
            
        # Convert to standard unit
        converted_value = round(value * multiplier, 2)
        standard_unit = self.STANDARD_UNITS[activity]
        
        logger.info(f"Converted: {value} {unit} → {converted_value} {standard_unit}")
        
        return converted_value, standard_unit
    
    def get_standard_unit(self, activity: str) -> str:
        """Get the standard unit for an activity type"""
        return self.STANDARD_UNITS.get(activity, "units")
    
    def is_valid_unit(self, activity: str, unit: str) -> bool:
        """Check if unit is valid for given activity"""
        if activity not in self.CONVERSIONS:
            return False
            
        normalized_unit = self.normalize_unit(unit)
        return normalized_unit in self.CONVERSIONS[activity]
    
    def get_supported_units(self, activity: str) -> list:
        """Get list of supported units for an activity"""
        if activity not in self.CONVERSIONS:
            return []
            
        return list(self.CONVERSIONS[activity].keys())
    
    def format_conversion_message(self, original_value: float, original_unit: str, 
                                converted_value: float, standard_unit: str) -> str:
        """
        Create user-friendly message showing the conversion
        
        Args:
            original_value: Original value from user
            original_unit: Original unit from user  
            converted_value: Converted value
            standard_unit: Standard unit
            
        Returns:
            Formatted message explaining the conversion (empty if no conversion)
        """
        if original_unit.lower() == standard_unit.lower():
            # No conversion needed
            return ""
        
        # Format values nicely (remove .0 for whole numbers)
        orig_val = int(original_value) if original_value == int(original_value) else original_value
        conv_val = int(converted_value) if converted_value == int(converted_value) else converted_value
        
        # Create natural conversion messages based on activity type
        if standard_unit == "kg" and original_unit in ["lbs", "pounds"]:
            return f"That's about {conv_val} kg"
        elif standard_unit == "glasses" and original_unit == "liters":
            return f"That's {conv_val} glasses"
        elif standard_unit == "glasses" and original_unit == "ml":
            return f"That's {conv_val} glasses"
        elif standard_unit == "minutes" and original_unit in ["hours", "hrs"]:
            return f"That's {conv_val} minutes"
        elif standard_unit == "hours" and original_unit in ["minutes", "mins"]:
            return f"That's {conv_val} hours"
        else:
            # Generic fallback
            return f"That's {conv_val} {standard_unit}"


# Global instance
_unit_converter = None

def get_unit_converter() -> UnitConverter:
    """Get or create global UnitConverter instance"""
    global _unit_converter
    if _unit_converter is None:
        _unit_converter = UnitConverter()
    return _unit_converter