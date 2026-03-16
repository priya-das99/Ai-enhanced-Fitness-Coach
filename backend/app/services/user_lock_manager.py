# app/services/user_lock_manager.py
# Per-user async locks to prevent concurrent request processing

import asyncio
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class UserLockManager:
    """
    Manages per-user async locks to ensure sequential message processing.
    
    This prevents race conditions when a user sends multiple messages rapidly:
    - User A's messages are processed sequentially
    - User B's messages are processed in parallel (different lock)
    
    Pattern used by production chatbot systems.
    """
    
    def __init__(self):
        self._locks: Dict[int, asyncio.Lock] = {}
        self._cleanup_lock = asyncio.Lock()
    
    def get_lock(self, user_id: int) -> asyncio.Lock:
        """
        Get or create lock for user.
        
        Args:
            user_id: User ID
            
        Returns:
            asyncio.Lock for this user
        """
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
            logger.debug(f"Created lock for user {user_id}")
        
        return self._locks[user_id]
    
    async def cleanup_idle_locks(self, max_locks: int = 1000):
        """
        Clean up locks for inactive users to prevent memory leak.
        
        Args:
            max_locks: Maximum number of locks to keep
        """
        async with self._cleanup_lock:
            if len(self._locks) > max_locks:
                # Remove unlocked locks (users not actively chatting)
                idle_users = [
                    user_id for user_id, lock in self._locks.items()
                    if not lock.locked()
                ]
                
                # Keep most recent locks, remove oldest
                to_remove = idle_users[:-max_locks]
                for user_id in to_remove:
                    del self._locks[user_id]
                
                logger.info(f"Cleaned up {len(to_remove)} idle user locks")
    
    def get_stats(self) -> dict:
        """Get lock statistics for monitoring"""
        return {
            'total_locks': len(self._locks),
            'active_locks': sum(1 for lock in self._locks.values() if lock.locked())
        }


# Global singleton instance
_lock_manager = UserLockManager()


def get_lock_manager() -> UserLockManager:
    """Get the global lock manager instance"""
    return _lock_manager
