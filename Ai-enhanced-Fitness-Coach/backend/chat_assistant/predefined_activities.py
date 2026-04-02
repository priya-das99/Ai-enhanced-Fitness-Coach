# predefined_activities.py
# Predefined activity suggestions based on mood
# NOTE: This file is DEPRECATED and should not be used
# Health activities (water, sleep, exercise, weight) are handled by activity_workflow
# Wellness activities (breathing, meditation, etc.) are handled by content_service

class PredefinedActivities:
    """
    DEPRECATED: This class should not be used for suggestions
    
    Health activities are handled by:
    - activity_workflow.py (for logging water, sleep, exercise, weight)
    - Persistent buttons in chat UI
    
    Wellness activities are handled by:
    - content_service.py (breathing, meditation, journaling, etc.)
    - Intelligent suggestions based on mood and context
    """
    
    # Keep for backward compatibility but don't use for suggestions
    ACTIVITIES = {}
    
    @staticmethod
    def get_suggestions_for_mood(mood):
        """
        DEPRECATED: Returns empty list
        Use content_service.py for wellness activity suggestions instead
        """
        return []
    
    @staticmethod
    def get_all_activities():
        """DEPRECATED: Returns empty list"""
        return []
    
    @staticmethod
    def get_activity_by_id(activity_id):
        """DEPRECATED: Returns None"""
        return None
