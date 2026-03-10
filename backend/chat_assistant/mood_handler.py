# mood_handler.py
# Handles mood logging flow - saves to database

from datetime import datetime, date
from app.core.database import get_db

# Emoji to mood value mapping
MOOD_EMOJIS = {
    '😄': 5,  # Awesome
    '😊': 4,  # Pretty Good
    '🙂': 4,  # Pretty Good (alternative)
    '😐': 3,  # Okay
    '😟': 2,  # Not good
    '😢': 1,  # Horrible
}

# Positive moods (don't need reason)
POSITIVE_MOODS = ['😄', '😊', '🙂']

# Negative/neutral moods (ask for reason or suggest activities)
NEGATIVE_MOODS = ['😐', '😟', '😢']

def validate_mood_emoji(emoji):
    """Validate if emoji is a valid mood selector"""
    return emoji in MOOD_EMOJIS

def is_positive_mood(emoji):
    """Check if mood is positive (doesn't need reason)"""
    return emoji in POSITIVE_MOODS

def is_negative_mood(emoji):
    """Check if mood is negative/neutral (needs reason)"""
    return emoji in NEGATIVE_MOODS

def get_mood_value(emoji):
    """Convert emoji to numeric mood value"""
    return MOOD_EMOJIS.get(emoji)

def save_mood_log(user_id, mood_emoji, reason=None, intensity=None, stress_level=None, 
                  energy_level=None, confidence_level=None, tags=None):
    """
    Save mood log entry to database with enhanced metrics
    
    Args:
        user_id: User ID
        mood_emoji: Mood emoji (😄😊😐😟😢)
        reason: Optional reason for mood
        intensity: Optional mood intensity (1-10)
        stress_level: Optional stress level (1-10)
        energy_level: Optional energy level (1-10)
        confidence_level: Optional confidence level (1-10)
        tags: Optional list of tags
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        mood_value = get_mood_value(mood_emoji)
        
        # Use local timestamp
        local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert tags list to JSON string if provided
        import json
        tags_json = json.dumps(tags) if tags else None
        
        cursor.execute('''
            INSERT INTO mood_logs 
            (user_id, mood, mood_emoji, mood_intensity, stress_level, 
             energy_level, confidence_level, reason, reason_category, tags, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, str(mood_value), mood_emoji, intensity, stress_level,
              energy_level, confidence_level, reason, None, tags_json, local_timestamp))
        
        mood_id = cursor.lastrowid
        conn.commit()
    
    # Update challenge progress for mood logging
    try:
        from app.repositories.challenge_repository import ChallengeRepository
        challenge_repo = ChallengeRepository()
        challenge_repo.update_challenge_progress(user_id, 'mood', 1)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to update challenge progress: {e}")
    
    return {
        'id': mood_id,
        'user_id': user_id,
        'mood_emoji': mood_emoji,
        'mood_value': mood_value,
        'reason': reason,
        'intensity': intensity,
        'stress_level': stress_level,
        'energy_level': energy_level,
        'confidence_level': confidence_level,
        'tags': tags,
        'timestamp': local_timestamp
    }

def get_user_mood_logs(user_id, limit=10):
    """Get recent mood logs for user from database"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, mood, mood_emoji, reason, timestamp,
                   mood_intensity, stress_level, energy_level, confidence_level, tags
            FROM mood_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
    
    import json
    logs = []
    for row in rows:
        logs.append({
            'id': row[0],
            'user_id': row[1],
            'mood_value': row[2],
            'mood_emoji': row[3],
            'reason': row[4],
            'timestamp': row[5],
            'intensity': row[6],
            'stress_level': row[7],
            'energy_level': row[8],
            'confidence_level': row[9],
            'tags': json.loads(row[10]) if row[10] else None
        })
    
    return logs

def has_logged_mood_today(user_id):
    """Check if user has logged mood today"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM mood_logs
            WHERE user_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
    
    return count > 0

def get_last_mood_log_time(user_id):
    """Get timestamp of last mood log for user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp FROM mood_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
    
    if row:
        return datetime.fromisoformat(row[0])
    
    return None
