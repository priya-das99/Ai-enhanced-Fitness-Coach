"""
Suggestion Interaction Tracker V2

Updated to work with fixed schema (no boolean redundancy)
"""

import sqlite3
from datetime import datetime
from typing import Optional
import json


class SuggestionInteractionTrackerV2:
    """Track detailed suggestion interactions - V2 with fixed schema"""
    
    def __init__(self, db_path: str = "mood_capture.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def track_shown(
        self, 
        user_id: int, 
        suggestion_key: str,
        mood_emoji: Optional[str] = None,
        reason: Optional[str] = None
    ) -> int:
        """Track when a suggestion is shown to user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO suggestion_history 
            (user_id, suggestion_key, mood_emoji, reason, 
             shown_at, interaction_type)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'shown')
        """, (user_id, suggestion_key, mood_emoji, reason))
        
        suggestion_history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return suggestion_history_id
    
    def track_accepted(
        self, 
        user_id: int, 
        suggestion_key: str
    ) -> bool:
        """Track when user accepts a suggestion"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Update most recent shown instance
        cursor.execute("""
            UPDATE suggestion_history 
            SET interaction_type = 'accepted',
                interacted_at = CURRENT_TIMESTAMP
            WHERE user_id = ? 
            AND suggestion_key = ?
            AND interaction_type = 'shown'
            ORDER BY shown_at DESC 
            LIMIT 1
        """, (user_id, suggestion_key))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_updated > 0
    
    def track_rejected(
        self, 
        user_id: int, 
        suggestion_key: str
    ) -> bool:
        """Track when user explicitly rejects a suggestion"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE suggestion_history 
            SET interaction_type = 'rejected',
                interacted_at = CURRENT_TIMESTAMP
            WHERE user_id = ? 
            AND suggestion_key = ?
            AND interaction_type = 'shown'
            ORDER BY shown_at DESC 
            LIMIT 1
        """, (user_id, suggestion_key))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_updated > 0
    
    def mark_session_suggestions_as_ignored(
        self, 
        user_id: int, 
        session_start_time: datetime
    ) -> int:
        """Mark all uninteracted suggestions from a session as ignored"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE suggestion_history 
            SET interaction_type = 'ignored',
                interacted_at = CURRENT_TIMESTAMP
            WHERE user_id = ? 
            AND shown_at >= ?
            AND interaction_type = 'shown'
        """, (user_id, session_start_time))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_updated
    
    def mark_as_expired(
        self, 
        user_id: int, 
        suggestion_key: str
    ) -> bool:
        """Mark suggestion as expired (e.g., time-sensitive suggestion)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE suggestion_history 
            SET interaction_type = 'expired',
                interacted_at = CURRENT_TIMESTAMP
            WHERE user_id = ? 
            AND suggestion_key = ?
            AND interaction_type = 'shown'
            ORDER BY shown_at DESC 
            LIMIT 1
        """, (user_id, suggestion_key))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_updated > 0
    
    def get_interaction_stats(self, user_id: int) -> dict:
        """Get user's interaction statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                interaction_type,
                COUNT(*) as count
            FROM suggestion_history
            WHERE user_id = ?
            GROUP BY interaction_type
        """, (user_id,))
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Calculate rates
        total = sum(stats.values())
        if total > 0:
            stats['acceptance_rate'] = stats.get('accepted', 0) / total
            stats['rejection_rate'] = stats.get('rejected', 0) / total
            stats['ignore_rate'] = stats.get('ignored', 0) / total
        
        conn.close()
        return stats
    
    def get_suggestion_performance(self, suggestion_key: str) -> dict:
        """Get performance metrics for a specific suggestion"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shown,
                SUM(CASE WHEN interaction_type = 'accepted' THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN interaction_type = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN interaction_type = 'ignored' THEN 1 ELSE 0 END) as ignored
            FROM suggestion_history
            WHERE suggestion_key = ?
        """, (suggestion_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        total = row[0] or 1  # Avoid division by zero
        return {
            'suggestion_key': suggestion_key,
            'total_shown': row[0],
            'accepted': row[1],
            'rejected': row[2],
            'ignored': row[3],
            'acceptance_rate': row[1] / total,
            'rejection_rate': row[2] / total,
            'ignore_rate': row[3] / total
        }
