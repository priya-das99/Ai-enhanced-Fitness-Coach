# app/services/chat_cleanup_service.py
# Automatic chat history cleanup and optimization

from app.repositories.chat_repository import ChatRepository
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ChatCleanupService:
    """
    Service for managing chat history storage
    
    Strategies:
    1. Keep recent messages (last 30 days) in full
    2. Summarize older messages (30-90 days)
    3. Delete very old messages (90+ days)
    4. Keep only important messages for long-term
    """
    
    def __init__(self):
        self.chat_repo = ChatRepository()
    
    def cleanup_old_messages(self, retention_days: int = 90) -> dict:
        """
        Clean up messages older than retention period
        
        Args:
            retention_days: Days to keep messages (default 90)
        
        Returns:
            Cleanup statistics
        """
        from app.core.database import get_db
        
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Count messages to delete
            cursor.execute('''
                SELECT COUNT(*) FROM chat_messages 
                WHERE DATE(timestamp) < ?
            ''', (cutoff_date,))
            count_to_delete = cursor.fetchone()[0]
            
            # Delete old messages
            cursor.execute('''
                DELETE FROM chat_messages 
                WHERE DATE(timestamp) < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} messages older than {retention_days} days")
        
        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date
        }
    
    def cleanup_user_messages(self, user_id: int, keep_recent: int = 100) -> int:
        """
        Keep only recent N messages per user
        
        Args:
            user_id: User ID
            keep_recent: Number of recent messages to keep
        
        Returns:
            Number of messages deleted
        """
        from app.core.database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get ID of the Nth most recent message
            cursor.execute('''
                SELECT id FROM chat_messages
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1 OFFSET ?
            ''', (user_id, keep_recent))
            
            result = cursor.fetchone()
            if not result:
                return 0  # User has fewer than keep_recent messages
            
            cutoff_id = result[0]
            
            # Delete messages older than cutoff
            cursor.execute('''
                DELETE FROM chat_messages
                WHERE user_id = ? AND id < ?
            ''', (user_id, cutoff_id))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        return deleted_count
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics for chat messages"""
        from app.core.database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Total messages
            cursor.execute('SELECT COUNT(*) FROM chat_messages')
            total_messages = cursor.fetchone()[0]
            
            # Messages per user
            cursor.execute('''
                SELECT user_id, COUNT(*) as count
                FROM chat_messages
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_users = cursor.fetchall()
            
            # Messages by age
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN DATE(timestamp) >= DATE('now', '-7 days') THEN 1 ELSE 0 END) as last_7_days,
                    SUM(CASE WHEN DATE(timestamp) >= DATE('now', '-30 days') THEN 1 ELSE 0 END) as last_30_days,
                    SUM(CASE WHEN DATE(timestamp) >= DATE('now', '-90 days') THEN 1 ELSE 0 END) as last_90_days
                FROM chat_messages
            ''')
            age_stats = cursor.fetchone()
            
            # Estimated size (rough calculation)
            estimated_size_mb = (total_messages * 0.25) / 1024  # 0.25 KB per message
        
        return {
            'total_messages': total_messages,
            'estimated_size_mb': round(estimated_size_mb, 2),
            'messages_last_7_days': age_stats[0] if age_stats else 0,
            'messages_last_30_days': age_stats[1] if age_stats else 0,
            'messages_last_90_days': age_stats[2] if age_stats else 0,
            'top_users': [{'user_id': row[0], 'message_count': row[1]} for row in top_users]
        }
    
    def optimize_database(self) -> dict:
        """Optimize database by vacuuming and analyzing"""
        from app.core.database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Vacuum to reclaim space
            cursor.execute('VACUUM')
            
            # Analyze for query optimization
            cursor.execute('ANALYZE chat_messages')
            
            conn.commit()
        
        logger.info("Database optimized")
        return {'status': 'optimized'}
    
    def archive_old_messages(self, archive_days: int = 90) -> dict:
        """
        Archive old messages to separate table (optional feature)
        
        This moves old messages to an archive table for long-term storage
        while keeping the main table fast.
        """
        from app.core.database import get_db
        
        cutoff_date = (datetime.now() - timedelta(days=archive_days)).strftime('%Y-%m-%d')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Create archive table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages_archive (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    timestamp DATETIME,
                    metadata TEXT,
                    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Move old messages to archive
            cursor.execute('''
                INSERT INTO chat_messages_archive 
                    (id, user_id, message, sender, timestamp, metadata)
                SELECT id, user_id, message, sender, timestamp, metadata
                FROM chat_messages
                WHERE DATE(timestamp) < ?
            ''', (cutoff_date,))
            
            archived_count = cursor.rowcount
            
            # Delete from main table
            cursor.execute('''
                DELETE FROM chat_messages
                WHERE DATE(timestamp) < ?
            ''', (cutoff_date,))
            
            conn.commit()
        
        logger.info(f"Archived {archived_count} messages older than {archive_days} days")
        
        return {
            'archived_count': archived_count,
            'cutoff_date': cutoff_date
        }


# Scheduled cleanup function
def run_scheduled_cleanup():
    """
    Run scheduled cleanup tasks
    
    Call this from a cron job or scheduler:
    - Daily: Clean messages older than 90 days
    - Weekly: Optimize database
    """
    service = ChatCleanupService()
    
    # Clean old messages
    cleanup_result = service.cleanup_old_messages(retention_days=90)
    
    # Optimize database
    optimize_result = service.optimize_database()
    
    # Get stats
    stats = service.get_storage_stats()
    
    logger.info(f"Scheduled cleanup completed: {cleanup_result}")
    logger.info(f"Storage stats: {stats}")
    
    return {
        'cleanup': cleanup_result,
        'optimize': optimize_result,
        'stats': stats
    }
