# app/services/activity_service.py
# Activity business logic

from app.repositories.activity_repository import ActivityRepository
from typing import Dict, List

class ActivityService:
    """Service for activity operations"""
    
    def __init__(self):
        self.activity_repo = ActivityRepository()
    
    def handle_button_click(self, user_id: int, activity_id: str) -> Dict:
        """Handle activity button click"""
        from chat_assistant.activity_chat_handler import ActivityChatHandler
        
        activity_handler = ActivityChatHandler()
        return activity_handler.handle_activity_button_click(user_id, activity_id)
    
    def get_today_activities(self, user_id: int) -> List[Dict]:
        """Get today's activities"""
        from chat_assistant.health_activity_logger import HealthActivityLogger
        
        logger = HealthActivityLogger()
        return logger.get_today_activities(user_id)
    
    def get_activity_summary(self, user_id: int, activity_type: str, days: int = 7) -> Dict:
        """Get activity summary"""
        from chat_assistant.health_activity_logger import HealthActivityLogger
        
        logger = HealthActivityLogger()
        return logger.get_activity_summary(user_id, activity_type, days)
    
    def log_activity(self, user_id: int, activity_type: str, value: float, 
                     unit: str, notes: str = "") -> int:
        """Log a health activity"""
        return self.activity_repo.log_activity(user_id, activity_type, value, unit, notes)
