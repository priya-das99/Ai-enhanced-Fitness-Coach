# app/repositories/challenge_repository.py
# Challenge data access layer

from app.core.database import get_db
from typing import List, Dict, Optional
from datetime import datetime, date

class ChallengeRepository:
    """Repository for challenge operations"""
    
    def get_user_active_challenges(self, user_id: int) -> List[Dict]:
        """Get user's active challenges with progress"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.challenge_type,
                    c.duration_days,
                    c.points,
                    uc.progress,
                    uc.status,
                    uc.started_at,
                    (SELECT COUNT(*) FROM challenge_progress cp 
                     WHERE cp.user_challenge_id = uc.id AND cp.target_met = 1) as days_completed
                FROM challenges c
                JOIN user_challenges uc ON c.id = uc.challenge_id
                WHERE uc.user_id = ? 
                AND uc.status = 'active'
                AND c.is_active = 1
                ORDER BY uc.started_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'challenge_type': row[3],
                    'duration_days': row[4],
                    'points': row[5],
                    'progress': row[6],
                    'status': row[7],
                    'started_at': row[8],
                    'days_completed': row[9]
                }
                for row in rows
            ]
    
    def get_challenge_progress_today(self, user_id: int, challenge_type: str) -> Optional[Dict]:
        """Check if user made progress on a challenge type today"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    cp.value_achieved,
                    cp.target_met
                FROM challenge_progress cp
                JOIN user_challenges uc ON cp.user_challenge_id = uc.id
                JOIN challenges c ON uc.challenge_id = c.id
                WHERE uc.user_id = ?
                AND c.challenge_type = ?
                AND DATE(cp.date) = DATE('now', 'localtime')
                AND uc.status = 'active'
                LIMIT 1
            ''', (user_id, challenge_type))
            
            row = cursor.fetchone()
            if row:
                return {
                    'value_achieved': row[0],
                    'target_met': row[1]
                }
            return None
    
    def update_challenge_progress(self, user_id: int, challenge_type: str, value: float) -> bool:
        """Update progress for a challenge when user logs activity"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get active challenge of this type
            cursor.execute('''
                SELECT uc.id, c.duration_days
                FROM user_challenges uc
                JOIN challenges c ON uc.challenge_id = c.id
                WHERE uc.user_id = ? 
                AND c.challenge_type = ?
                AND uc.status = 'active'
                AND c.is_active = 1
                LIMIT 1
            ''', (user_id, challenge_type))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            user_challenge_id, duration_days = result
            # Assume target is met if value > 0 (simplified logic)
            target_met = value > 0
            
            # Insert or update today's progress (using localtime)
            cursor.execute('''
                INSERT INTO challenge_progress (user_challenge_id, date, value_achieved, target_met)
                VALUES (?, DATE('now', 'localtime'), ?, ?)
                ON CONFLICT(user_challenge_id, date) 
                DO UPDATE SET value_achieved = ?, target_met = ?
            ''', (user_challenge_id, value, target_met, value, target_met))
            
            # Update user_challenges progress
            cursor.execute('''
                SELECT COUNT(*) FROM challenge_progress
                WHERE user_challenge_id = ? AND target_met = 1
            ''', (user_challenge_id,))
            days_completed = cursor.fetchone()[0]
            
            progress = (days_completed / duration_days) * 100 if duration_days > 0 else 0
            
            cursor.execute('''
                UPDATE user_challenges
                SET progress = ?
                WHERE id = ?
            ''', (progress, user_challenge_id))
            
            # Check if challenge is completed
            if days_completed >= duration_days:
                self._complete_challenge(cursor, user_challenge_id, user_id)
            
            conn.commit()
            return True
    
    def _complete_challenge(self, cursor, user_challenge_id: int, user_id: int):
        """Mark challenge as completed and award points"""
        # Get challenge points
        cursor.execute('''
            SELECT c.points
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.id = ?
        ''', (user_challenge_id,))
        
        points = cursor.fetchone()[0]
        
        # Update challenge status (removed points_earned column reference)
        cursor.execute('''
            UPDATE user_challenges
            SET status = 'completed', 
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user_challenge_id,))
        
        # Update user points
        cursor.execute('''
            INSERT INTO user_points (user_id, total_points, challenges_completed)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                total_points = total_points + ?,
                challenges_completed = challenges_completed + 1
        ''', (user_id, points, points))
    
    def get_user_points(self, user_id: int) -> Dict:
        """Get user's total points and stats"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT total_points, challenges_completed, current_streak, longest_streak
                FROM user_points
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'total_points': row[0],
                    'challenges_completed': row[1],
                    'current_streak': row[2],
                    'longest_streak': row[3]
                }
            return {
                'total_points': 0,
                'challenges_completed': 0,
                'current_streak': 0,
                'longest_streak': 0
            }
    
    def get_available_challenges(self, user_id: int) -> List[Dict]:
        """Get challenges user can join"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.challenge_type,
                    c.duration_days,
                    c.points
                FROM challenges c
                WHERE c.is_active = 1
                AND c.id NOT IN (
                    SELECT challenge_id FROM user_challenges 
                    WHERE user_id = ? AND status IN ('active', 'completed')
                )
                ORDER BY c.created_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'challenge_type': row[3],
                    'duration_days': row[4],
                    'points': row[5]
                }
                for row in rows
            ]
    
    def join_challenge(self, user_id: int, challenge_id: int) -> bool:
        """User joins a challenge"""
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO user_challenges (user_id, challenge_id, status)
                    VALUES (?, ?, 'active')
                ''', (user_id, challenge_id))
                conn.commit()
                return True
            except:
                return False
