"""
LLM Token Usage Tracker
Tracks all LLM calls, token usage, and costs in real-time
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def get_connection():
    return sqlite3.connect('backend/mood_capture.db')

class LLMTokenTracker:
    """Tracks LLM token usage and costs"""
    
    # Pricing (as of 2024 for GPT-3.5-turbo)
    COST_PER_1K_INPUT_TOKENS = 0.0005  # $0.50 per 1M tokens
    COST_PER_1K_OUTPUT_TOKENS = 0.0015  # $1.50 per 1M tokens
    
    @staticmethod
    def create_table():
        """Create llm_usage_log table if it doesn't exist"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                call_type TEXT,  -- 'intent_detection', 'response_generation', 'insight_generation'
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                estimated_cost REAL,
                latency_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                context_data TEXT,  -- JSON with additional context
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp 
            ON llm_usage_log(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_llm_usage_user 
            ON llm_usage_log(user_id, timestamp)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ LLM usage tracking table created")
    
    @staticmethod
    def log_llm_call(
        user_id: Optional[int],
        call_type: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        context_data: Optional[Dict] = None
    ):
        """
        Log an LLM API call
        
        Args:
            user_id: User ID (None for system calls)
            call_type: Type of call ('intent_detection', 'response_generation', 'insight_generation')
            model: Model used (e.g., 'gpt-3.5-turbo')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Response time in milliseconds
            success: Whether call succeeded
            error_message: Error message if failed
            context_data: Additional context (message, intent, etc.)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * LLMTokenTracker.COST_PER_1K_INPUT_TOKENS
        output_cost = (output_tokens / 1000) * LLMTokenTracker.COST_PER_1K_OUTPUT_TOKENS
        estimated_cost = input_cost + output_cost
        
        cursor.execute('''
            INSERT INTO llm_usage_log (
                user_id, call_type, model, input_tokens, output_tokens,
                total_tokens, estimated_cost, latency_ms, success,
                error_message, context_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, call_type, model, input_tokens, output_tokens,
            total_tokens, estimated_cost, latency_ms, success,
            error_message, json.dumps(context_data) if context_data else None
        ))
        
        conn.commit()
        conn.close()
        
        # Log to console
        logger.info(
            f"🤖 LLM Call: {call_type} | "
            f"Tokens: {input_tokens}→{output_tokens} ({total_tokens} total) | "
            f"Cost: ${estimated_cost:.4f} | "
            f"Latency: {latency_ms}ms"
        )
    
    @staticmethod
    def get_usage_stats(days: int = 7) -> Dict:
        """
        Get usage statistics for the last N days
        
        Returns:
            {
                "total_calls": 150,
                "total_tokens": 75000,
                "total_cost": 0.05,
                "avg_latency_ms": 850,
                "by_call_type": {...},
                "by_day": [...]
            }
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(latency_ms) as avg_latency,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
            FROM llm_usage_log
            WHERE DATE(timestamp) >= ?
        ''', (since_date,))
        
        overall = cursor.fetchone()
        
        # By call type
        cursor.execute('''
            SELECT 
                call_type,
                COUNT(*) as calls,
                SUM(total_tokens) as tokens,
                SUM(estimated_cost) as cost,
                AVG(latency_ms) as avg_latency
            FROM llm_usage_log
            WHERE DATE(timestamp) >= ?
            GROUP BY call_type
        ''', (since_date,))
        
        by_call_type = {}
        for row in cursor.fetchall():
            by_call_type[row[0]] = {
                "calls": row[1],
                "tokens": row[2],
                "cost": row[3],
                "avg_latency_ms": row[4]
            }
        
        # By day
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as calls,
                SUM(total_tokens) as tokens,
                SUM(estimated_cost) as cost
            FROM llm_usage_log
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (since_date,))
        
        by_day = []
        for row in cursor.fetchall():
            by_day.append({
                "date": row[0],
                "calls": row[1],
                "tokens": row[2],
                "cost": row[3]
            })
        
        conn.close()
        
        return {
            "period_days": days,
            "total_calls": overall[0] or 0,
            "total_tokens": overall[1] or 0,
            "total_cost": overall[2] or 0.0,
            "avg_latency_ms": overall[3] or 0,
            "successful_calls": overall[4] or 0,
            "success_rate": (overall[4] / overall[0] * 100) if overall[0] > 0 else 0,
            "by_call_type": by_call_type,
            "by_day": by_day
        }
    
    @staticmethod
    def get_user_usage(user_id: int, days: int = 30) -> Dict:
        """Get LLM usage for a specific user"""
        conn = get_connection()
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost
            FROM llm_usage_log
            WHERE user_id = ? AND DATE(timestamp) >= ?
        ''', (user_id, since_date))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_calls": result[0] or 0,
            "total_tokens": result[1] or 0,
            "total_cost": result[2] or 0.0
        }
    
    @staticmethod
    def get_recent_calls(limit: int = 20) -> List[Dict]:
        """Get recent LLM calls for debugging"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id, user_id, call_type, model, input_tokens, output_tokens,
                total_tokens, estimated_cost, latency_ms, success,
                error_message, timestamp
            FROM llm_usage_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        calls = []
        for row in cursor.fetchall():
            calls.append({
                "id": row[0],
                "user_id": row[1],
                "call_type": row[2],
                "model": row[3],
                "input_tokens": row[4],
                "output_tokens": row[5],
                "total_tokens": row[6],
                "estimated_cost": row[7],
                "latency_ms": row[8],
                "success": bool(row[9]),
                "error_message": row[10],
                "timestamp": row[11]
            })
        
        conn.close()
        return calls

# Initialize table on import
try:
    LLMTokenTracker.create_table()
except Exception as e:
    logger.error(f"Failed to create LLM tracking table: {e}")
