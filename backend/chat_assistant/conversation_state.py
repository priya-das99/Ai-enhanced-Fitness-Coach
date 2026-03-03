# conversation_state.py
# State management for chat conversations - saves to database

from db import get_connection
import json

# State definitions
class ConversationState:
    IDLE = 'idle'
    ASKING_MOOD = 'asking_mood'
    ASKING_REASON = 'asking_reason'
    SUGGESTING_ACTION = 'suggesting_action'
    MOOD_LOGGED = 'mood_logged'

def _ensure_session(user_id):
    """Ensure user has an active session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user has an active session
    cursor.execute('''
        SELECT id FROM chat_sessions
        WHERE user_id = ? AND session_end IS NULL
        ORDER BY session_start DESC
        LIMIT 1
    ''', (user_id,))
    
    session = cursor.fetchone()
    
    if not session:
        # Create new session
        cursor.execute('''
            INSERT INTO chat_sessions (user_id, session_start)
            VALUES (?, datetime('now'))
        ''', (user_id,))
        conn.commit()
    
    conn.close()

def get_state(user_id):
    """Get current conversation state for user from database"""
    _ensure_session(user_id)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get state from user's temp data
    cursor.execute('''
        SELECT id FROM chat_sessions
        WHERE user_id = ? AND session_end IS NULL
        ORDER BY session_start DESC
        LIMIT 1
    ''', (user_id,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        # For now, use in-memory for state (can be enhanced later)
        # State is temporary and doesn't need persistence
        return _memory_states.get(user_id, ConversationState.IDLE)
    
    return ConversationState.IDLE

def set_state(user_id, state):
    """Set conversation state for user"""
    _ensure_session(user_id)
    _memory_states[user_id] = state

def reset_state(user_id):
    """Reset user to IDLE state"""
    _memory_states[user_id] = ConversationState.IDLE

def save_user_data(user_id, key, value):
    """Store temporary user data during conversation"""
    _ensure_session(user_id)
    
    if user_id not in _memory_data:
        _memory_data[user_id] = {}
    _memory_data[user_id][key] = value

def get_user_data(user_id, key):
    """Retrieve temporary user data"""
    return _memory_data.get(user_id, {}).get(key)

def clear_user_data(user_id):
    """Clear temporary data for user"""
    if user_id in _memory_data:
        del _memory_data[user_id]

# In-memory storage for temporary conversation state
# (These are temporary and don't need database persistence)
_memory_states = {}
_memory_data = {}
