"""
Ranking Context Logger Service

Logs complete ranking context for:
- Debugging personalization
- Analyzing ranking quality
- Improving weights over time
- A/B testing algorithms
"""

import sqlite3
from typing import List, Dict, Optional
import json
from datetime import datetime


class RankingContextLogger:
    """Log and analyze suggestion ranking decisions"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mood_capture.db')
        self.db_path = db_path
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def log_ranking(
        self,
        user_id: int,
        mood_emoji: Optional[str],
        reason: Optional[str],
        algorithm_name: str,
        ranked_suggestions: List[Dict],
        user_context: Dict
    ) -> int:
        """
        Log complete ranking context
        
        Args:
            user_id: User identifier
            mood_emoji: Current mood
            reason: Mood reason
            algorithm_name: Name/version of ranking algorithm
            ranked_suggestions: List of dicts with keys:
                - suggestion_key
                - final_score
                - recency_score
                - frequency_score
                - acceptance_score
                - mood_match_score
                - time_match_score
                - diversity_penalty
                - signals (dict of all signals used)
            user_context: Dict of user state (metrics, history, etc.)
        
        Returns:
            ranking_context_id for later updates
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Insert ranking context
        cursor.execute("""
            INSERT INTO suggestion_ranking_context
            (user_id, mood_emoji, reason, ranking_timestamp,
             ranking_algorithm, total_candidates, context_snapshot)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        """, (
            user_id,
            mood_emoji,
            reason,
            algorithm_name,
            len(ranked_suggestions),
            json.dumps(user_context)
        ))
        
        ranking_context_id = cursor.lastrowid
        
        # Insert ranking details for each suggestion
        for rank, suggestion in enumerate(ranked_suggestions, 1):
            cursor.execute("""
                INSERT INTO suggestion_ranking_details
                (ranking_context_id, suggestion_key, rank_position,
                 final_score, recency_score, frequency_score,
                 acceptance_score, mood_match_score, time_match_score,
                 diversity_penalty, signals_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ranking_context_id,
                suggestion['suggestion_key'],
                rank,
                suggestion.get('final_score', 0),
                suggestion.get('recency_score'),
                suggestion.get('frequency_score'),
                suggestion.get('acceptance_score'),
                suggestion.get('mood_match_score'),
                suggestion.get('time_match_score'),
                suggestion.get('diversity_penalty'),
                json.dumps(suggestion.get('signals', {}))
            ))
        
        conn.commit()
        conn.close()
        
        return ranking_context_id
    
    def log_user_selection(
        self,
        ranking_context_id: int,
        selected_suggestion_key: str
    ) -> bool:
        """Update ranking context with user's actual selection"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the rank of selected suggestion
        cursor.execute("""
            SELECT rank_position
            FROM suggestion_ranking_details
            WHERE ranking_context_id = ? AND suggestion_key = ?
        """, (ranking_context_id, selected_suggestion_key))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        selected_rank = result[0]
        
        # Update context
        cursor.execute("""
            UPDATE suggestion_ranking_context
            SET selected_suggestion_key = ?,
                selected_rank = ?
            WHERE id = ?
        """, (selected_suggestion_key, selected_rank, ranking_context_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def analyze_ranking_quality(self, days: int = 30) -> Dict:
        """
        Analyze how often users pick top-ranked suggestions
        
        Returns distribution of selected ranks
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                selected_rank,
                COUNT(*) as selections,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
            FROM suggestion_ranking_context
            WHERE selected_suggestion_key IS NOT NULL
            AND ranking_timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY selected_rank
            ORDER BY selected_rank
        """, (days,))
        
        distribution = {}
        for row in cursor.fetchall():
            distribution[f"rank_{row[0]}"] = {
                'count': row[1],
                'percentage': round(row[2], 2)
            }
        
        conn.close()
        return distribution
    
    def analyze_signal_effectiveness(self, signal_name: str, days: int = 30) -> Dict:
        """
        Analyze correlation between a signal score and user selection
        
        Args:
            signal_name: e.g., 'mood_match_score', 'recency_score'
            days: Look back period
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                srd.suggestion_key,
                AVG(srd.{signal_name}) as avg_signal_score,
                COUNT(CASE WHEN src.selected_suggestion_key = srd.suggestion_key THEN 1 END) as times_selected,
                COUNT(*) as times_shown
            FROM suggestion_ranking_details srd
            JOIN suggestion_ranking_context src ON srd.ranking_context_id = src.id
            WHERE src.ranking_timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY srd.suggestion_key
            HAVING times_shown >= 5
            ORDER BY times_selected DESC, avg_signal_score DESC
        """
        
        cursor.execute(query, (days,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'suggestion_key': row[0],
                'avg_signal_score': round(row[1], 3) if row[1] else None,
                'times_selected': row[2],
                'times_shown': row[3],
                'selection_rate': round(row[2] / row[3], 3)
            })
        
        conn.close()
        return results
    
    def compare_algorithms(self, algo1: str, algo2: str, days: int = 30) -> Dict:
        """Compare performance of two ranking algorithms"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ranking_algorithm,
                COUNT(*) as total_rankings,
                COUNT(selected_suggestion_key) as selections_made,
                AVG(selected_rank) as avg_selected_rank,
                SUM(CASE WHEN selected_rank = 1 THEN 1 ELSE 0 END) * 100.0 / 
                    COUNT(selected_suggestion_key) as rank1_percentage
            FROM suggestion_ranking_context
            WHERE ranking_algorithm IN (?, ?)
            AND ranking_timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY ranking_algorithm
        """, (algo1, algo2, days))
        
        comparison = {}
        for row in cursor.fetchall():
            comparison[row[0]] = {
                'total_rankings': row[1],
                'selections_made': row[2],
                'avg_selected_rank': round(row[3], 2) if row[3] else None,
                'rank1_percentage': round(row[4], 2) if row[4] else None
            }
        
        conn.close()
        return comparison
    
    def get_underperforming_suggestions(self, min_shown: int = 10) -> List[Dict]:
        """Find suggestions that rank high but aren't selected"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                srd.suggestion_key,
                AVG(srd.rank_position) as avg_rank,
                COUNT(*) as times_shown,
                COUNT(CASE WHEN src.selected_suggestion_key = srd.suggestion_key THEN 1 END) as times_selected,
                AVG(srd.final_score) as avg_score
            FROM suggestion_ranking_details srd
            JOIN suggestion_ranking_context src ON srd.ranking_context_id = src.id
            WHERE srd.rank_position <= 3
            GROUP BY srd.suggestion_key
            HAVING times_shown >= ?
            AND times_selected * 1.0 / times_shown < 0.1
            ORDER BY avg_rank ASC, times_shown DESC
        """, (min_shown,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'suggestion_key': row[0],
                'avg_rank': round(row[1], 2),
                'times_shown': row[2],
                'times_selected': row[3],
                'selection_rate': round(row[3] / row[2], 3),
                'avg_score': round(row[4], 3)
            })
        
        conn.close()
        return results
    
    def get_ranking_context(self, ranking_context_id: int) -> Optional[Dict]:
        """Retrieve full ranking context for debugging"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get context
        cursor.execute("""
            SELECT user_id, mood_emoji, reason, ranking_timestamp,
                   ranking_algorithm, total_candidates, selected_suggestion_key,
                   selected_rank, context_snapshot
            FROM suggestion_ranking_context
            WHERE id = ?
        """, (ranking_context_id,))
        
        context_row = cursor.fetchone()
        if not context_row:
            conn.close()
            return None
        
        # Get ranking details
        cursor.execute("""
            SELECT suggestion_key, rank_position, final_score,
                   recency_score, frequency_score, acceptance_score,
                   mood_match_score, time_match_score, diversity_penalty,
                   signals_used
            FROM suggestion_ranking_details
            WHERE ranking_context_id = ?
            ORDER BY rank_position
        """, (ranking_context_id,))
        
        details = []
        for row in cursor.fetchall():
            details.append({
                'suggestion_key': row[0],
                'rank': row[1],
                'final_score': row[2],
                'recency_score': row[3],
                'frequency_score': row[4],
                'acceptance_score': row[5],
                'mood_match_score': row[6],
                'time_match_score': row[7],
                'diversity_penalty': row[8],
                'signals': json.loads(row[9]) if row[9] else {}
            })
        
        conn.close()
        
        return {
            'ranking_context_id': ranking_context_id,
            'user_id': context_row[0],
            'mood_emoji': context_row[1],
            'reason': context_row[2],
            'timestamp': context_row[3],
            'algorithm': context_row[4],
            'total_candidates': context_row[5],
            'selected_suggestion': context_row[6],
            'selected_rank': context_row[7],
            'user_context': json.loads(context_row[8]) if context_row[8] else {},
            'ranked_suggestions': details
        }
