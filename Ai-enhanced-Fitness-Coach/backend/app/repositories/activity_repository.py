# app/repositories/activity_repository.py
# Activity data access layer

from app.core.database import get_db
from typing import List, Dict
from datetime import datetime, timedelta

class ActivityRepository:
    """Repository for activity database operations"""
    
    def log_activity(self, user_id: int, activity_type: str, value: float, 
                     unit: str, notes: str = "") -> int:
        """Log a health activity"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO health_activities 
                   (user_id, activity_type, value, unit, notes) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, activity_type, value, unit, notes)
            )
            return cursor.lastrowid
    
    def get_today_activities(self, user_id: int) -> List[Dict]:
        """Get today's activities for a user"""
        today = datetime.now().date()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM health_activities 
                   WHERE user_id = ? AND DATE(timestamp) = ? 
                   ORDER BY timestamp DESC""",
                (user_id, today)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_activity_summary(self, user_id: int, activity_type: str, days: int = 7) -> Dict:
        """Get activity summary for specified days"""
        start_date = datetime.now() - timedelta(days=days)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT 
                    COUNT(*) as count,
                    SUM(value) as total,
                    AVG(value) as average,
                    MIN(value) as min,
                    MAX(value) as max
                   FROM health_activities 
                   WHERE user_id = ? AND activity_type = ? AND timestamp >= ?""",
                (user_id, activity_type, start_date)
            )
            row = cursor.fetchone()
            return dict(row) if row else {}
