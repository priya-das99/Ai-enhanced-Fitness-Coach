# smart_suggestions.py
# Smart LLM-powered activity suggestions with context awareness
# Phase 3: Weighted Sum Model with 5 normalized signals

from .llm_service import get_llm_service
import json
import logging
import sys
import os
import sqlite3
import math
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ranking logger
from app.services.ranking_context_logger import RankingContextLogger

logger = logging.getLogger(__name__)

# Initialize ranking logger
ranking_logger = RankingContextLogger()

# ============================================================================
# WEIGHTED SUM MODEL CONFIGURATION
# ============================================================================

# Signal weights (must sum to ~1.0 for positive signals)
WEIGHTS = {
    'reason_match': 0.30,       # Does activity solve the problem? (reduced from 0.35)
    'user_preference': 0.20,    # Does user like this activity? (reduced from 0.25)
    'reason_preference': 0.15,  # Does it work for THIS problem? (reduced from 0.20)
    'time_preference': 0.10,    # Right time of day? (reduced from 0.15)
    'mood_intensity': 0.15,     # Does effort match mood severity? (NEW)
    'fatigue_penalty': 0.40     # Recently used? (SUBTRACTED)
}

# Hard filter settings
COOLDOWN_MINUTES = 120  # 2 hours cooldown for hard filter

# Fatigue decay settings
FATIGUE_DECAY_FACTOR = 120  # Minutes for exponential decay (2 hours)

# ============================================================================
# MOOD INTENSITY MAPPING
# ============================================================================

MOOD_INTENSITY_MAP = {
    '😊': 0.2,  # Happy - light activities
    '🙂': 0.3,  # Slightly happy
    '😐': 0.5,  # Neutral - medium activities
    '😕': 0.6,  # Slightly concerned
    '😟': 0.7,  # Stressed - focused activities
    '😰': 0.9,  # Very stressed - intensive activities
    '😢': 1.0,  # Sad - deep/long activities
    '😭': 1.0,  # Very sad
    '😡': 0.8,  # Angry - physical release
    '😤': 0.7,  # Frustrated
}

EFFORT_INTENSITY_MAP = {
    'low': 0.3,     # Low effort activities (breathing, meditation)
    'medium': 0.6,  # Medium effort (short walk, stretching)
    'high': 0.9     # High effort (workout, long activities)
}

# ============================================================================
# REASON CATEGORIES (Improved matching)
# ============================================================================

REASON_CATEGORIES = {
    'work': ['work', 'job', 'office', 'deadline', 'pressure', 'boss', 'meeting', 
             'project', 'colleague', 'workload', 'career', 'professional'],
    'relationship': ['relationship', 'friend', 'family', 'partner', 'spouse', 
                     'fight', 'argument', 'conflict', 'breakup', 'divorce', 
                     'lonely', 'loneliness', 'social'],
    'health': ['tired', 'exhausted', 'sick', 'pain', 'ache', 'sleep', 'energy',
               'fatigue', 'burnout', 'physical', 'body'],
    'anxiety': ['anxious', 'worried', 'nervous', 'stress', 'stressed', 'panic',
                'overwhelm', 'overwhelmed', 'tense', 'uneasy'],
    'sadness': ['sad', 'depressed', 'down', 'unhappy', 'miserable', 'hopeless',
                'grief', 'loss', 'crying'],
    'anger': ['angry', 'mad', 'frustrated', 'irritated', 'annoyed', 'furious',
              'rage', 'upset'],
    'food': ['food', 'eating', 'diet', 'hungry', 'appetite', 'meal', 'nutrition'],
    'education': ['school', 'study', 'exam', 'test', 'homework', 'class', 
                  'university', 'college', 'learning']
}

# Map categories to activity best_for tags
CATEGORY_TO_ACTIVITY_TAGS = {
    'work': ['work', 'stress', 'overwhelm', 'burnout'],
    'relationship': ['relationship', 'friend', 'support', 'loneliness'],
    'health': ['tired', 'energy', 'sleep', 'health'],
    'anxiety': ['anxiety', 'stress', 'calm', 'focus'],
    'sadness': ['mood boost', 'support', 'self-reflection'],
    'anger': ['calm', 'stress', 'physical tension'],
    'food': ['food', 'health'],
    'education': ['education', 'stress', 'focus']
}

# ============================================================================
# ACTIVITY CATALOG (Load from DB)
# ============================================================================

def _load_activities_from_db():
    """
    Load activities from suggestion_master table AND content_items table.
    Falls back to hardcoded if DB unavailable.
    """
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mood_capture.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        activities = {}
        
        # Load regular activities from suggestion_master
        cursor.execute("""
            SELECT suggestion_key, title, description, 
                   category, effort_level, duration_minutes, is_active, best_for
            FROM suggestion_master
            WHERE is_active = 1
        """)
        
        for row in cursor.fetchall():
            key, title, desc, category, effort, duration, is_active, best_for_json = row
            
            # Parse best_for JSON tags
            import json
            if best_for_json:
                try:
                    best_for = json.loads(best_for_json)
                except:
                    best_for = _get_best_for_keywords(category, key)
            else:
                best_for = _get_best_for_keywords(category, key)
            
            activities[key] = {
                'id': key,
                'name': title,
                'description': desc,
                'category': category,
                'effort': effort,
                'duration': f"{duration} min",
                'work_friendly': effort == 'low',  # Simple heuristic
                'is_active': bool(is_active),
                'best_for': best_for
            }
        
        # Load external content from content_items (NEW!)
        cursor.execute("""
            SELECT ci.id, ci.title, ci.description, ci.content_type, 
                   ci.content_url, ci.duration_minutes, ci.difficulty_level, 
                   ci.tags, ci.is_featured, c.slug as category_slug
            FROM content_items ci
            JOIN content_categories c ON ci.category_id = c.id
            WHERE ci.is_active = 1
        """)
        
        for row in cursor.fetchall():
            content_id, title, desc, content_type, content_url, duration, difficulty, tags_json, is_featured, category_slug = row
            
            # Parse tags
            try:
                tags = json.loads(tags_json) if tags_json else []
            except:
                tags = []
            
            # Create unique key for content
            key = f"content_{content_id}"
            
            # Map content type to action verb
            type_map = {
                'video': 'Watch',
                'blog': 'Read',
                'podcast': 'Listen to'
            }
            verb = type_map.get(content_type, 'View')
            
            activities[key] = {
                'id': key,
                'name': f"{verb}: {title}",
                'description': desc,
                'category': category_slug,
                'effort': difficulty or 'low',
                'duration': f"{duration} min" if duration else "Varies",
                'work_friendly': difficulty == 'low',
                'is_active': True,
                'best_for': tags,  # Use tags as best_for
                'action_type': 'open_external',
                'content_url': content_url,
                'content_type': content_type,
                'is_featured': bool(is_featured)
            }
        
        conn.close()
        
        if activities:
            logger.info(f"✅ Loaded {len(activities)} activities from database (including content)")
            return activities
        
    except Exception as e:
        logger.warning(f"Failed to load from DB: {e}, using hardcoded activities")
    
    # Fallback to hardcoded
    return WELLNESS_ACTIVITIES_FALLBACK


def _get_best_for_keywords(category: str, activity_id: str) -> list:
    """Map category and activity to best_for keywords"""
    keyword_map = {
        'mindfulness': ['stress', 'anxiety', 'calm', 'focus'],
        'physical': ['energy', 'mood boost', 'exercise'],
        'rest': ['tired', 'burnout', 'overwhelm'],
        'social': ['loneliness', 'friend', 'relationship', 'support'],
        'reflection': ['stress', 'anxiety', 'self-reflection'],
        'relaxation': ['stress', 'mood boost', 'calm'],
        'health': ['energy', 'health', 'quick relief']
    }
    
    # Activity-specific keywords
    specific_keywords = {
        'breathing': ['work', 'quick relief'],
        'take_break': ['work', 'education', 'overwhelm'],
        'short_walk': ['relationship', 'food'],
        'power_nap': ['sleep', 'burnout'],
        'call_friend': ['loneliness', 'relationship'],
        'hydrate': ['quick relief']
    }
    
    keywords = keyword_map.get(category, [])
    keywords.extend(specific_keywords.get(activity_id, []))
    
    return list(set(keywords))  # Remove duplicates


# Hardcoded fallback (original WELLNESS_ACTIVITIES)
WELLNESS_ACTIVITIES_FALLBACK = {
    "breathing": {
        "id": "breathing",
        "name": "Breathing Exercise",
        "effort": "low",
        "work_friendly": True,
        "description": "Quick breathing exercises to calm your mind",
        "duration": "3-5 min",
        "best_for": ["stress", "anxiety", "work", "quick relief"]
    },
    "short_walk": {
        "id": "short_walk",
        "name": "Short Walk",
        "effort": "medium",
        "work_friendly": False,
        "description": "Brief walk or movement to refresh",
        "duration": "10-15 min",
        "best_for": ["energy", "mood boost", "friend", "relationship", "food"]
    },
    "meditation": {
        "id": "meditation_module",  # Changed to trigger module
        "name": "Start Meditation",
        "effort": "low",
        "work_friendly": True,
        "description": "Guided meditation session",
        "duration": "10-20 min",
        "best_for": ["calm", "focus", "stress", "anxiety", "mindfulness"],
        "is_module": True
    },
    "stretching": {
        "id": "stretching",
        "name": "Stretching",
        "effort": "low",
        "work_friendly": True,
        "description": "Gentle stretches to release tension",
        "duration": "5-10 min",
        "best_for": ["physical tension", "work", "exercise", "energy"]
    },
    "take_break": {
        "id": "take_break",
        "name": "Take a Break",
        "effort": "low",
        "work_friendly": True,
        "description": "Step away from current activity",
        "duration": "5 min",
        "best_for": ["work", "education", "overwhelm", "burnout"]
    },
    "journaling": {
        "id": "journaling",
        "name": "Journaling",
        "effort": "low",
        "work_friendly": True,
        "description": "Write down your thoughts and feelings",
        "duration": "10-15 min",
        "best_for": ["stress", "anxiety", "relationship", "self-reflection"]
    },
    "music": {
        "id": "music",
        "name": "Listen to Music",
        "effort": "low",
        "work_friendly": True,
        "description": "Listen to calming or uplifting music",
        "duration": "10-15 min",
        "best_for": ["mood boost", "stress", "energy", "focus"],
        "action_type": "open_external",
        "content_url": "https://www.youtube.com/watch?v=lTRiuFIWV54",  # 3-hour calming music
        "content_type": "video"
    },
    "call_friend": {
        "id": "call_friend",
        "name": "Call a Friend",
        "effort": "medium",
        "work_friendly": False,
        "description": "Connect with someone you trust",
        "duration": "15-30 min",
        "best_for": ["loneliness", "friend", "relationship", "support"]
    },
    "hydrate": {
        "id": "hydrate",
        "name": "Drink Water",
        "effort": "low",
        "work_friendly": True,
        "description": "Have a glass of water and hydrate",
        "duration": "1 min",
        "best_for": ["energy", "health", "quick relief"]
    },
    "power_nap": {
        "id": "power_nap",
        "name": "Power Nap",
        "effort": "low",
        "work_friendly": False,
        "description": "Short 15-20 minute rest",
        "duration": "15-20 min",
        "best_for": ["tired", "energy", "sleep", "burnout"]
    },
    "outdoor_activity": {
        "id": "outdoor_activity",
        "name": "Start Outdoor Activity",
        "effort": "medium",
        "work_friendly": False,
        "description": "Go outside for fresh air and movement",
        "duration": "15-30 min",
        "best_for": ["energy", "mood boost", "stress", "nature", "exercise"],
        "is_module": True
    },
    "seven_minute_workout": {
        "id": "seven_minute_workout",
        "name": "Start 7 Minute Workout",
        "effort": "high",
        "work_friendly": False,
        "description": "Quick high-intensity workout routine",
        "duration": "7 min",
        "best_for": ["energy", "exercise", "fitness", "quick workout"],
        "is_module": True
    },
    "squats_workout": {
        "id": "squats_workout",
        "name": "Start Squats Workout",
        "effort": "medium",
        "work_friendly": False,
        "description": "Focused squats exercise routine",
        "duration": "10-15 min",
        "best_for": ["exercise", "strength", "fitness", "legs"],
        "is_module": True
    },
    "meditation_module": {
        "id": "meditation_module",
        "name": "Start Meditation",
        "effort": "low",
        "work_friendly": True,
        "description": "Guided meditation session",
        "duration": "10-20 min",
        "best_for": ["calm", "focus", "stress", "anxiety", "mindfulness"],
        "is_module": True
    }
}

# ============================================================================
# CONTEXT BUILDER (Pre-fetch all DB data in ONE place)
# ============================================================================

def _build_scoring_context(user_id: str, base_context: dict) -> dict:
    """
    Pre-fetch ALL data needed for scoring in ONE place.
    This prevents DB access inside scoring loops.
    
    Returns: Enhanced context with pre-fetched data
    """
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mood_capture.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cooldown_time = datetime.now() - timedelta(minutes=COOLDOWN_MINUTES)
        
        # Fetch cooldown set (ONE query)
        cursor.execute("""
            SELECT DISTINCT suggestion_key
            FROM suggestion_history
            WHERE user_id = ?
            AND shown_at > ?
        """, (str(user_id), cooldown_time.isoformat()))
        
        cooldown_set = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        
        # Add to context
        base_context['cooldown_set'] = cooldown_set
        
        logger.debug(f"[Context] Pre-fetched cooldown set: {len(cooldown_set)} activities")
        
    except Exception as e:
        logger.warning(f"Failed to fetch cooldown data: {e}")
        base_context['cooldown_set'] = set()
    
    return base_context


# ============================================================================
# HARD FILTERS (Remove invalid options BEFORE scoring)
# ============================================================================

def _apply_hard_filters(activities: list, context: dict) -> list:
    """
    Remove activities that are invalid for current context.
    This is NOT scoring - just binary filtering.
    
    Filters:
    1. Inactive activities
    2. Work hours constraint (can't do non-work-friendly activities at work)
    3. Cooldown (shown too recently) - uses pre-fetched cooldown_set
    """
    filtered = []
    cooldown_set = context.get('cooldown_set', set())  # Pre-fetched!
    
    for activity in activities:
        # Filter 1: Inactive activities
        if not activity.get('is_active', True):
            logger.debug(f"  Filtered {activity['id']}: inactive")
            continue
        
        # Filter 2: Work hours constraint
        if context.get('is_work_hours') and not activity.get('work_friendly', False):
            logger.debug(f"  Filtered {activity['id']}: not work-friendly")
            continue
        
        # Filter 3: Cooldown check (O(1) lookup in set)
        if activity['id'] in cooldown_set:
            logger.debug(f"  Filtered {activity['id']}: in cooldown")
            continue
        
        filtered.append(activity)
    
    logger.info(f"[Hard Filters] {len(activities)} → {len(filtered)} activities")
    return filtered


# ============================================================================
# NORMALIZED SIGNALS (All return 0-1)
# ============================================================================

def _categorize_reason(reason: str) -> list:
    """
    Categorize reason into one or more categories.
    Returns: List of matching categories
    
    Example: "stressed about work deadline" → ['work', 'anxiety']
    """
    if not reason:
        return []
    
    reason_lower = reason.lower()
    categories = []
    
    for category, keywords in REASON_CATEGORIES.items():
        if any(keyword in reason_lower for keyword in keywords):
            categories.append(category)
    
    return categories


def _compute_reason_score(activity: dict, reason: str) -> float:
    """
    Signal 1: Does activity help with this reason?
    Returns: 0 or 1 (binary match)
    
    Phase 2: Uses reason categories for better matching
    """
    if not reason:
        return 0.0
    
    # Get reason categories
    categories = _categorize_reason(reason)
    
    if not categories:
        # Fallback to substring matching
        reason_lower = reason.lower()
        best_for = activity.get('best_for', [])
        
        for keyword in best_for:
            if keyword in reason_lower:
                return 1.0
        
        return 0.0
    
    # Check if activity helps with any of the categories
    activity_tags = activity.get('best_for', [])
    
    for category in categories:
        category_tags = CATEGORY_TO_ACTIVITY_TAGS.get(category, [])
        
        # Check if any category tag matches activity tags
        for tag in category_tags:
            if tag in activity_tags:
                return 1.0  # Match found!
    
    return 0.0  # No match


def _compute_user_preference_score(activity: dict, context: dict) -> float:
    """
    Signal 2: How much does user like this activity?
    Returns: 0-1 (normalized by max completion count)
    """
    favorites = context.get('favorite_activities', [])
    
    if not favorites:
        return 0.0  # Neutral = no boost (let reason_match dominate)
    
    activity_id = activity['id']
    completion_count = 0
    
    for fav in favorites:
        if fav.get('id') == activity_id:
            completion_count = fav.get('completion_count', 0)
            break
    
    # Normalize by max completion count
    max_count = max([f.get('completion_count', 1) for f in favorites])
    
    if max_count == 0:
        return 0.0  # No completions = no preference
    
    return min(completion_count / max_count, 1.0)


def _compute_reason_preference_score(activity: dict, reason: str, context: dict) -> float:
    """
    Signal 3: When user has THIS reason, do they choose THIS activity?
    Returns: 0-1 (frequency)
    """
    if not reason:
        return 0.0  # No reason = no preference signal
    
    reason_prefs = context.get('reason_preferences', {}).get(reason, {})
    
    if not reason_prefs:
        return 0.0  # No history = no preference
    
    activity_id = activity['id']
    frequency = reason_prefs.get(activity_id, 0.0)
    
    return min(frequency, 1.0)  # Already 0-1


def _compute_time_preference_score(activity: dict, context: dict) -> float:
    """
    Signal 4: Does user do this activity at this time of day?
    Returns: 0-1 (frequency)
    """
    time_period = context.get('time_period', 'day')
    time_prefs = context.get('time_preferences', {}).get(time_period, {})
    
    if not time_prefs:
        return 0.0  # No history = no time preference
    
    activity_id = activity['id']
    frequency = time_prefs.get(activity_id, 0.0)
    
    return min(frequency, 1.0)  # Already 0-1


def _compute_mood_intensity_score(activity: dict, mood_emoji: str) -> float:
    """
    Signal 5: Does activity effort match mood severity?
    Returns: 0-1 (1 = perfect match, 0 = poor match)
    
    Logic: Match activity intensity to mood intensity
    - Happy (😊) → light activities (breathing, meditation)
    - Stressed (😟) → focused activities (take break, journaling)
    - Very stressed (😰) → intensive activities (workout, long walk)
    """
    if not mood_emoji:
        return 0.5  # Neutral if no mood
    
    # Get mood intensity (0-1)
    mood_intensity = MOOD_INTENSITY_MAP.get(mood_emoji, 0.5)
    
    # Get activity intensity based on effort
    activity_effort = activity.get('effort', 'low')
    activity_intensity = EFFORT_INTENSITY_MAP.get(activity_effort, 0.5)
    
    # Score based on how close they match
    # Perfect match = 1.0, complete mismatch = 0.0
    diff = abs(mood_intensity - activity_intensity)
    score = 1.0 - diff
    
    return max(0.0, score)  # Ensure non-negative


def _compute_fatigue_score(activity: dict, context: dict) -> float:
    """
    Signal 6: How recently was this activity used?
    Returns: 0-1 (1 = very recent, 0 = not recent)
    This is SUBTRACTED in final score.
    
    Phase 2: Uses exponential time decay instead of static values
    Formula: fatigue = e^(-minutes/decay_factor)
    """
    recent_activities = context.get('recent_activities', [])
    
    if not recent_activities:
        return 0.0  # No fatigue
    
    activity_id = activity['id']
    
    for recent in recent_activities:
        if recent.get('activity_id') == activity_id:
            # Try to get actual timestamp
            timestamp = recent.get('timestamp')
            
            if timestamp and isinstance(timestamp, datetime):
                # Calculate minutes since last use
                minutes_ago = (datetime.now() - timestamp).total_seconds() / 60
                
                # Exponential decay: fatigue = e^(-minutes/decay_factor)
                import math
                fatigue = math.exp(-minutes_ago / FATIGUE_DECAY_FACTOR)
                
                # fatigue at 0 min = 1.0 (100%)
                # fatigue at 2 hours = 0.37 (37%)
                # fatigue at 4 hours = 0.14 (14%)
                
                return fatigue
            
            # Fallback to position-based if no timestamp
            idx = recent_activities.index(recent)
            if idx == 0:
                return 1.0  # Just used - high fatigue
            elif idx == 1:
                return 0.6  # Used recently - medium fatigue
            elif idx == 2:
                return 0.3  # Used a while ago - low fatigue
    
    return 0.0  # Not in recent list


# ============================================================================
# WEIGHTED SUM CALCULATION
# ============================================================================

def _compute_weighted_score(activity: dict, reason: str, mood_emoji: str, context: dict) -> float:
    """
    Compute final score using weighted sum model.
    
    Formula:
    score = w1*reason + w2*user_pref + w3*reason_pref + w4*time + w5*mood - w6*fatigue
    
    Returns: 0-1 (higher = better match)
    """
    # Compute all 6 signals (each 0-1)
    reason_score = _compute_reason_score(activity, reason)
    user_pref_score = _compute_user_preference_score(activity, context)
    reason_pref_score = _compute_reason_preference_score(activity, reason, context)
    time_score = _compute_time_preference_score(activity, context)
    mood_score = _compute_mood_intensity_score(activity, mood_emoji)
    fatigue_score = _compute_fatigue_score(activity, context)
    
    # Apply weighted sum
    final_score = (
        WEIGHTS['reason_match'] * reason_score +
        WEIGHTS['user_preference'] * user_pref_score +
        WEIGHTS['reason_preference'] * reason_pref_score +
        WEIGHTS['time_preference'] * time_score +
        WEIGHTS['mood_intensity'] * mood_score +  # NEW!
        -WEIGHTS['fatigue_penalty'] * fatigue_score  # Subtract!
    )
    
    # Store debug info
    activity['_debug_scores'] = {
        'reason': reason_score,
        'user_pref': user_pref_score,
        'reason_pref': reason_pref_score,
        'time': time_score,
        'mood': mood_score,  # NEW!
        'fatigue': fatigue_score,
        'final': final_score
    }
    
    return max(final_score, 0.0)  # Ensure non-negative


def _score_suggestions_weighted(
    activities: list,
    mood_emoji: str,
    reason: str,
    context: dict
) -> list:
    """
    Score all suggestions using weighted sum model.
    
    Steps:
    1. Apply hard filters
    2. Compute weighted scores for each (now includes mood intensity!)
    3. Sort by score (descending)
    
    Returns: List of activities sorted by score
    """
    user_id = context.get('user_id', 'unknown')
    
    logger.info(f"[Weighted Sum] Scoring {len(activities)} activities for user {user_id}")
    
    # Step 1: Apply hard filters
    filtered = _apply_hard_filters(activities, context)
    
    if not filtered:
        logger.warning("[Weighted Sum] No activities passed filters!")
        return []
    
    # Step 2: Compute weighted scores
    scored = []
    for activity in filtered:
        score = _compute_weighted_score(activity, reason, mood_emoji, context)  # Pass mood_emoji!
        activity['score'] = score
        scored.append(activity)
    
    # Step 3: Sort by score (descending)
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    # Step 4: Log top 5 for debugging
    logger.info(f"[Weighted Sum] Top 5 scores:")
    for i, activity in enumerate(scored[:5]):
        debug = activity.get('_debug_scores', {})
        logger.info(
            f"  #{i+1}: {activity['id']:20} "
            f"score={activity['score']:.3f} "
            f"(r:{debug.get('reason', 0):.1f} "
            f"u:{debug.get('user_pref', 0):.1f} "
            f"m:{debug.get('mood', 0):.1f} "  # NEW!
            f"f:{debug.get('fatigue', 0):.1f})"
        )
    
    return scored


# ============================================================================
# MAIN SUGGESTION FUNCTION
# ============================================================================

def get_smart_suggestions(mood_emoji: str, reason: str, context: dict, count: int = 3, preferred_types: list = None) -> list:
    """
    Get smart activity suggestions using weighted sum model + LLM ranking.
    
    Flow:
    1. Build scoring context (pre-fetch all DB data)
    2. Load activities from DB
    3. Filter by preferred types (if specified)
    4. Score using weighted sum model (6 signals including mood intensity!)
    5. Take top 5
    6. LLM re-ranks top 5 (temperature 0.2)
    7. Return top N
    
    Args:
        mood_emoji: User's mood emoji (NOW USED in scoring!)
        reason: Reason for mood
        context: User context dict
        count: Number of suggestions to return
        preferred_types: Optional list of preferred activity types
    
    Returns:
        List of top N suggestions
    """
    user_id = context.get('user_id', 'unknown')
    
    logger.info(f"[Smart Suggestions] Getting suggestions for user {user_id}")
    logger.info(f"  Mood: {mood_emoji}, Reason: {reason}, Count: {count}")
    
    # Step 1: Build scoring context (pre-fetch all DB data in ONE place)
    context = _build_scoring_context(user_id, context)
    
    # Step 2: Load activities from DB
    all_activities_dict = _load_activities_from_db()
    all_activities = list(all_activities_dict.values())
    
    logger.info(f"[Smart Suggestions] Loaded {len(all_activities)} activities")
    
    # Step 3: Filter by preferred types if specified
    if preferred_types:
        all_activities = [a for a in all_activities if a['id'] in preferred_types]
        logger.info(f"[Smart Suggestions] Filtered to {len(all_activities)} preferred types")
    
    if not all_activities:
        logger.warning("[Smart Suggestions] No activities available!")
        return []
    
    # Step 4: Score using weighted sum model
    scored_activities = _score_suggestions_weighted(
        all_activities,
        mood_emoji,
        reason,
        context
    )
    
    if not scored_activities:
        logger.warning("[Smart Suggestions] No activities passed scoring!")
        return []
    
    # Step 5: Take top 5 for LLM ranking
    top_5 = scored_activities[:5]
    logger.info(f"[Smart Suggestions] Passing top 5 to LLM ranker")
    
    # Step 5.5: Log ranking context for debugging/optimization
    try:
        # Prepare ranked suggestions with scores for logging
        ranked_with_scores = []
        for suggestion in top_5:
            debug_scores = suggestion.get('_debug_scores', {})
            ranked_with_scores.append({
                'suggestion_key': suggestion['id'],
                'final_score': suggestion.get('score', 0),
                'recency_score': None,  # Not used in weighted sum
                'frequency_score': debug_scores.get('user_pref', 0),
                'acceptance_score': debug_scores.get('reason_pref', 0),
                'mood_match_score': debug_scores.get('mood', 0),
                'time_match_score': debug_scores.get('time', 0),
                'diversity_penalty': debug_scores.get('fatigue', 0),
                'signals': {
                    'reason_match': debug_scores.get('reason', 0),
                    'user_preference': debug_scores.get('user_pref', 0),
                    'reason_preference': debug_scores.get('reason_pref', 0),
                    'time_preference': debug_scores.get('time', 0),
                    'mood_intensity': debug_scores.get('mood', 0),
                    'fatigue_penalty': debug_scores.get('fatigue', 0)
                }
            })
        
        # Log ranking context
        ranking_context_id = ranking_logger.log_ranking(
            user_id=user_id,
            mood_emoji=mood_emoji,
            reason=reason,
            algorithm_name='weighted_sum_v2',
            ranked_suggestions=ranked_with_scores,
            user_context={
                k: list(v) if isinstance(v, set) else v 
                for k, v in context.items()
            }  # Convert sets to lists for JSON serialization
        )
        
        # Store ranking_context_id in context for later selection tracking
        context['ranking_context_id'] = ranking_context_id
        
        # Also attach to each suggestion for tracking
        for suggestion in top_5:
            suggestion['ranking_context_id'] = ranking_context_id
        
        logger.info(f"[Ranking Logger] Logged context ID: {ranking_context_id}")
        
    except Exception as e:
        logger.error(f"[Ranking Logger] Failed to log ranking context: {e}")
    
    # Step 6: Try LLM re-ranking
    try:
        from chat_assistant.domain.llm.suggestion_ranker import get_suggestion_ranker
        
        ranker = get_suggestion_ranker()
        ranked = ranker.rank_suggestions(
            candidates=top_5,
            mood_emoji=mood_emoji,
            reason=reason,
            context=context,
            top_n=count
        )
        
        if ranked:
            logger.info(f"[Smart Suggestions] ✅ Returned {len(ranked)} LLM-ranked suggestions")
            return ranked
    
    except Exception as e:
        logger.warning(f"[Smart Suggestions] LLM ranking failed: {e}")
    
    # Step 7: Fallback - return top N by score
    logger.info(f"[Smart Suggestions] Using score-based ranking (LLM unavailable)")
    return scored_activities[:count]


# ============================================================================
# LEGACY FUNCTIONS (Kept for backward compatibility)
# ============================================================================

# ============================================================================
# LEGACY FUNCTIONS (Kept for backward compatibility)
# ============================================================================

def _get_llm_suggestions_OLD(mood_emoji: str, reason: str, context: dict, count: int, llm_service) -> list:
    """Use LLM to select best activities based on context"""
    
    # Build context summary
    time_info = f"{context.get('time_period', 'day')} on {context.get('day_of_week', 'weekday')}"
    if context.get('is_weekend'):
        time_info += " (weekend)"
    if context.get('is_work_hours'):
        time_info += " (work hours)"
    
    # User history summary
    history_info = ""
    if context.get('has_activity_history'):
        favorites = context.get('favorite_activities', [])
        if favorites:
            fav_names = [f['name'] for f in favorites[:2]]
            history_info = f"\nUser's favorite activities: {', '.join(fav_names)}"
        
        # Time preferences
        time_prefs = context.get('time_preferences', {}).get(context.get('time_period'), {})
        if time_prefs:
            top_time_activity = max(time_prefs.items(), key=lambda x: x[1])[0]
            history_info += f"\nUsually does {top_time_activity} at this time"
        
        # Reason preferences
        reason_prefs = context.get('reason_preferences', {}).get(reason, {})
        if reason_prefs:
            top_reason_activity = max(reason_prefs.items(), key=lambda x: x[1])[0]
            history_info += f"\nUsually does {top_reason_activity} for {reason} issues"
    
    # Recent activities (avoid repetition)
    recent_info = ""
    recent_activities = context.get('recent_activities', [])
    if recent_activities:
        recent_ids = [a['activity_id'] for a in recent_activities[:3]]
        recent_info = f"\nRecently completed: {', '.join(recent_ids)}"
    
    # Build activity list
    activities_desc = "\n".join([
        f"- {act['id']}: {act['name']} ({act['duration']}, {act['effort']} effort, "
        f"{'work-friendly' if act['work_friendly'] else 'needs space'}) - {act['description']}"
        for act in WELLNESS_ACTIVITIES.values()
    ])
    
    prompt = f"""You are a wellness AI selecting activities for a user feeling {mood_emoji} due to {reason}.

Context:
- Time: {time_info}
- Mood: {mood_emoji}
- Reason: {reason}{history_info}{recent_info}

Available activities:
{activities_desc}

Select the TOP {count} MOST APPROPRIATE and DIVERSE activities considering:
1. User's current mood and specific reason (match activities to the reason)
2. Time of day and work hours constraints
3. User's past preferences (if available)
4. VARIETY - Choose different types of activities (don't just pick breathing/meditation/stretching)
5. Practical constraints (work-friendly during work hours)

IMPORTANT: 
- For work stress: Consider take_break, breathing, short_walk
- For relationship issues: Consider call_friend, journaling, short_walk
- For tiredness: Consider power_nap, hydrate, short_walk
- For anxiety: Consider breathing, meditation, journaling
- For loneliness: Consider call_friend, music, short_walk
- Provide VARIETY - don't always suggest the same activities

Respond with ONLY a JSON array of activity IDs in order of preference:
["activity_id1", "activity_id2", "activity_id3"]

Your response (JSON only):"""
    
    try:
        response = llm_service.call(prompt, max_tokens=100, temperature=0.7)
        
        if response:
            # Extract JSON from response
            response = response.strip()
            if response.startswith('[') and response.endswith(']'):
                activity_ids = json.loads(response)
                
                # Validate and build suggestions
                suggestions = []
                for act_id in activity_ids[:count]:
                    if act_id in WELLNESS_ACTIVITIES:
                        suggestions.append(WELLNESS_ACTIVITIES[act_id])
                
                if suggestions:
                    logger.info(f"✅ LLM selected: {[s['id'] for s in suggestions]}")
                    return suggestions
        
        return None
        
    except Exception as e:
        logger.error(f"LLM suggestion failed: {e}")
        return None

def _get_rule_based_suggestions_OLD(mood_emoji: str, reason: str, context: dict, count: int) -> list:
    """Fallback rule-based suggestions"""
    
    scores = {}
    
    for act_id, activity in WELLNESS_ACTIVITIES.items():
        score = 0
        
        # Reason matching
        if reason:
            reason_lower = reason.lower()
            for keyword in activity['best_for']:
                if keyword in reason_lower:
                    score += 10
        
        # Time of day matching
        time_period = context.get('time_period', 'day')
        if time_period == 'morning' and act_id in ['stretching', 'breathing', 'short_walk']:
            score += 5
        elif time_period == 'afternoon' and act_id in ['take_break', 'short_walk', 'breathing']:
            score += 5
        elif time_period == 'evening' and act_id in ['meditation', 'breathing', 'stretching']:
            score += 5
        elif time_period == 'night' and act_id in ['breathing', 'meditation']:
            score += 5
        
        # Work hours constraint
        if context.get('is_work_hours') and activity['work_friendly']:
            score += 3
        elif not context.get('is_work_hours'):
            score += 2
        
        # User history preferences
        if context.get('has_activity_history'):
            # Favorite activities
            favorites = context.get('favorite_activities', [])
            for fav in favorites:
                if fav['id'] == act_id:
                    score += 8
            
            # Time preferences
            time_prefs = context.get('time_preferences', {}).get(time_period, {})
            if act_id in time_prefs:
                score += time_prefs[act_id] * 2
            
            # Reason preferences
            reason_prefs = context.get('reason_preferences', {}).get(reason, {})
            if act_id in reason_prefs:
                score += reason_prefs[act_id] * 3
        
        # Avoid recent activities (slight penalty)
        recent_activities = context.get('recent_activities', [])
        recent_ids = [a['activity_id'] for a in recent_activities[:2]]
        if act_id in recent_ids:
            score -= 2
        
        scores[act_id] = score
    
    # Sort by score and return top N
    sorted_activities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    suggestions = []
    for act_id, score in sorted_activities[:count]:
        suggestions.append(WELLNESS_ACTIVITIES[act_id])
        logger.info(f"  {act_id}: score={score}")
    
    return suggestions
