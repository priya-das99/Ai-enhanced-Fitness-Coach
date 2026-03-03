"""
Intelligent Activity Suggestion Engine
Maps user states to appropriate activities, content, and challenges
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class IntelligentSuggestionEngine:
    """
    Suggests activities, content, and challenges based on:
    - User's current mood/state
    - Time of day
    - Recent activity history
    - Active challenges
    """
    
    # Mood/State to Activity Mapping
    STATE_TO_ACTIVITIES = {
        'bored': {
            'primary_need': 'engagement',
            'activities': [
                {
                    'id': 'read_blog',
                    'name': 'Read a Blog',
                    'description': 'Learn something new',
                    'duration': '5-10 min',
                    'effort': 'low',
                    'action_type': 'content',
                    'content_type': 'blog'
                },
                {
                    'id': 'watch_video',
                    'name': 'Watch a Video',
                    'description': 'Engaging visual content',
                    'duration': '10-15 min',
                    'effort': 'low',
                    'action_type': 'content',
                    'content_type': 'video'
                },
                {
                    'id': 'try_challenge',
                    'name': 'Try a Challenge',
                    'description': 'Set a goal and track progress',
                    'duration': 'ongoing',
                    'effort': 'medium',
                    'action_type': 'challenge'
                },
                {
                    'id': 'listen_to_music',
                    'name': 'Listen to Music',
                    'description': 'Upbeat music to energize',
                    'duration': '10-15 min',
                    'effort': 'low',
                    'url': 'https://youtu.be/uwEaQk5VeS4?si=81cpsJQScEinmIop'
                }
            ],
            'message_template': "Let's find something interesting! What sounds good?",
            'tone': 'energizing',
            'ask_reason': False
        },
        'restless': {
            'primary_need': 'movement',
            'activities': [
                {
                    'id': 'short_walk',
                    'name': 'Quick Walk',
                    'description': 'Get moving',
                    'duration': '10 min',
                    'effort': 'medium'
                },
                {
                    'id': 'stretching',
                    'name': 'Stretching',
                    'description': 'Release tension',
                    'duration': '5 min',
                    'effort': 'low'
                },
                {
                    'id': 'exercise',
                    'name': 'Quick Exercise',
                    'description': 'Burn some energy',
                    'duration': '10-15 min',
                    'effort': 'high'
                }
            ],
            'message_template': "Let's channel that energy! Pick one:",
            'tone': 'energizing',
            'ask_reason': False
        },
        'lonely': {
            'primary_need': 'connection',
            'activities': [
                {
                    'id': 'call_someone',
                    'name': 'Call a Friend',
                    'description': 'Reach out to someone',
                    'duration': '10-20 min',
                    'effort': 'medium'
                },
                {
                    'id': 'join_community',
                    'name': 'Join a Challenge',
                    'description': 'Connect with others',
                    'duration': 'ongoing',
                    'effort': 'low',
                    'action_type': 'challenge'
                },
                {
                    'id': 'write_journal',
                    'name': 'Journal',
                    'description': 'Express your thoughts',
                    'duration': '10 min',
                    'effort': 'low'
                }
            ],
            'message_template': "You're not alone. Let's find a way to connect:",
            'tone': 'warm',
            'ask_reason': False
        },
        'tired': {
            'primary_need': 'energy',
            'activities': [
                {
                    'id': 'hydrate',
                    'name': 'Drink Water',
                    'description': 'Hydration boosts energy',
                    'duration': '1 min',
                    'effort': 'low'
                },
                {
                    'id': 'stretching',
                    'name': 'Light Stretching',
                    'description': 'Wake up your body',
                    'duration': '5 min',
                    'effort': 'low'
                },
                {
                    'id': 'fresh_air',
                    'name': 'Get Fresh Air',
                    'description': 'Step outside briefly',
                    'duration': '5 min',
                    'effort': 'low'
                },
                {
                    'id': 'power_nap',
                    'name': 'Power Nap',
                    'description': '15-20 minute rest',
                    'duration': '15-20 min',
                    'effort': 'low'
                }
            ],
            'message_template': "Let's help you recharge. What sounds doable?",
            'tone': 'gentle',
            'ask_reason': False
        }
    }
    
    # Keywords to detect each state
    STATE_KEYWORDS = {
        'bored': ['bored', 'boring', 'nothing to do', 'uninterested', 'dull'],
        'restless': ['restless', 'antsy', 'fidgety', 'can\'t sit still', 'need to move'],
        'lonely': ['lonely', 'alone', 'isolated', 'no one to talk to', 'miss people'],
        'tired': ['tired', 'exhausted', 'sleepy', 'no energy', 'drained', 'fatigued']
    }
    
    def detect_state(self, message: str) -> Optional[str]:
        """
        Detect user state from message
        
        Args:
            message: User's message
            
        Returns:
            State name or None
        """
        message_lower = message.lower()
        
        for state, keywords in self.STATE_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                logger.info(f"Detected state: {state} from message: {message}")
                return state
        
        return None
    
    def get_suggestions(self, state: str, user_id: int, context: Dict) -> Dict:
        """
        Get intelligent suggestions based on user state and context
        
        Args:
            state: User's current state (bored, stressed, tired, etc.)
            user_id: User ID for personalization
            context: Additional context (time, history, etc.)
            
        Returns:
            {
                'activities': List of activity suggestions,
                'message': Contextual message,
                'tone': Message tone,
                'ask_reason': Whether to ask for more context,
                'show_challenges': Whether to show challenge options
            }
        """
        if state not in self.STATE_TO_ACTIVITIES:
            return self._get_default_suggestions(user_id, context)
        
        state_config = self.STATE_TO_ACTIVITIES[state]
        
        # Get base activities (hardcoded fallback)
        activities = state_config['activities'].copy()
        
        # Try to get content from database for enrichment
        try:
            db_content = self._get_content_from_db(state, user_id)
            if db_content:
                # Mix database content with hardcoded activities
                activities = self._merge_activities(activities, db_content)
                logger.info(f"Enhanced suggestions with {len(db_content)} items from database")
        except Exception as e:
            logger.warning(f"Failed to get content from DB, using hardcoded: {e}")
        
        # Personalize based on context
        activities = self._personalize_activities(activities, user_id, context)
        
        # Check if we should suggest challenges
        show_challenges = self._should_suggest_challenges(user_id, context, state)
        
        return {
            'activities': activities[:4],  # Top 4 suggestions
            'message': state_config['message_template'],
            'tone': state_config['tone'],
            'ask_reason': state_config.get('ask_reason', False),
            'show_challenges': show_challenges
        }
    
    def _get_content_from_db(self, state: str, user_id: int) -> List[Dict]:
        """
        Get relevant content from wellness_content database
        
        Args:
            state: User's current state (bored, tired, etc.)
            user_id: User ID
            
        Returns:
            List of content items from database
        """
        # Map states to content categories
        state_to_categories = {
            'bored': ['yoga', 'mindfulness', 'exercise'],  # Engaging content
            'tired': ['mindfulness', 'healthy-eating'],     # Calming/energy content
            'restless': ['exercise', 'yoga'],               # Movement content
            'lonely': ['mindfulness']                       # Connection/reflection content
        }
        
        categories = state_to_categories.get(state, [])
        if not categories:
            return []
        
        try:
            from app.services.content_service import ContentService
            content_service = ContentService()
            
            # Get featured content from relevant categories
            content_items = []
            for category_slug in categories:
                items = content_service.get_content_by_category(
                    category_slug=category_slug,
                    limit=2,
                    featured_only=True
                )
                content_items.extend(items)
            
            # Convert to activity format
            activities = []
            for item in content_items[:2]:  # Max 2 from DB
                activities.append({
                    'id': f"content_{item['id']}",
                    'name': item['title'],
                    'description': item['description'][:50] + '...' if len(item['description']) > 50 else item['description'],
                    'duration': f"{item['duration_minutes']} min",
                    'effort': item['difficulty_level'],
                    'action_type': 'open_external',
                    'content_type': item['content_type'],
                    'content_url': item['content_url']
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error fetching content from DB: {e}")
            return []
    
    def _merge_activities(self, hardcoded: List[Dict], db_content: List[Dict]) -> List[Dict]:
        """
        Merge hardcoded activities with database content
        
        Strategy: Keep some hardcoded (like Listen to Music with URL),
        add database content for variety
        """
        # Keep first 2 hardcoded activities
        merged = hardcoded[:2].copy()
        
        # Add database content
        merged.extend(db_content)
        
        # Add remaining hardcoded if needed
        if len(merged) < 4:
            merged.extend(hardcoded[2:4-len(merged)])
        
        return merged
    
    def _personalize_activities(self, activities: List[Dict], user_id: int, context: Dict) -> List[Dict]:
        """Personalize activity list based on user history and preferences"""
        # TODO: Implement personalization logic
        # - Filter out recently completed activities
        # - Prioritize activities user has engaged with before
        # - Consider time of day (no exercise late at night)
        return activities
    
    def _should_suggest_challenges(self, user_id: int, context: Dict, state: str) -> bool:
        """Determine if we should suggest challenges"""
        # Suggest challenges if:
        # 1. User has a 3+ day streak
        # 2. User is in a positive/motivated state
        # 3. User has no active challenges
        
        has_streak = context.get('activity_streak', 0) >= 3
        is_engagement_state = state in ['bored', 'restless']  # Looking for engagement
        no_active_challenge = not context.get('has_active_challenge', False)
        
        return has_streak or (is_engagement_state and no_active_challenge)
    
    def _get_default_suggestions(self, user_id: int, context: Dict) -> Dict:
        """Default suggestions when state is unknown"""
        return {
            'activities': [],
            'message': "How can I help you today?",
            'tone': 'neutral',
            'ask_reason': False,
            'show_challenges': False
        }


# Global instance
_suggestion_engine = None

def get_suggestion_engine() -> IntelligentSuggestionEngine:
    """Get or create global suggestion engine"""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = IntelligentSuggestionEngine()
    return _suggestion_engine


# ===== ENHANCED SUGGESTION ENGINE WITH DB INTEGRATION =====
class EnhancedIntelligentSuggestionEngine:
    """
    Enhanced suggestion engine with database integration and dependency injection
    Consolidates smart_suggestions ranking with database-driven content
    """
    def __init__(self, ranker=None, content_service=None):
        """
        Initialize with dependency injection for testability
        Args:
            ranker: Function to rank activities (from smart_suggestions)
            content_service: Service to fetch activities from DB
        """
        self.ranker = ranker or self._default_ranker
        self.content_service = content_service
        
        # Import content service at class level
        if self.content_service is None:
            try:
                from app.services.content_service import get_activities_for_mood, normalize_activity_format
                self.get_activities_for_mood = get_activities_for_mood
                self.normalize_activity_format = normalize_activity_format
            except ImportError:
                logger.warning("Content service not available, using fallback")
                self.get_activities_for_mood = None
                self.normalize_activity_format = None
    
    def get_suggestions(self, state: str, user_id: int, context: dict) -> dict:
        """
        Orchestrator for activity suggestions - DB first, then ranking
        Args:
            state: User's mood/state ('bored', 'stressed', etc.)
            user_id: User ID for personalization
            context: Additional context (time, history, etc.)
        Returns:
            {
                'activities': [{"id": int, "title": str, ...}],
                'state': state,
                'count': int
            }
        """
        logger.info(f"🎯 Getting suggestions for state: {state}, user: {user_id}")
        
        # Step 1: Fetch activities from database
        activities = []
        if self.get_activities_for_mood:
            try:
                activities = self.get_activities_for_mood(state, limit=10)
                logger.info(f"📊 DB returned {len(activities)} activities for '{state}'")
            except Exception as e:
                logger.error(f"❌ DB query failed: {e}")
        
        # Step 2: Fallback to hardcoded if empty
        if not activities:
            logger.info(f"🔄 Using fallback activities for '{state}'")
            activities = self._get_fallback_activities(state)
        
        # Step 3: Normalize format for ranking
        normalized = []
        for act in activities:
            if self.normalize_activity_format:
                normalized.append(self.normalize_activity_format(act))
            else:
                normalized.append(self._normalize_activity(act))
        
        # Step 4: Rank using injected ranker
        try:
            ranked = self.ranker(normalized, user_id, context)
            logger.info(f"📈 Ranked {len(ranked)} activities")
        except Exception as e:
            logger.error(f"❌ Ranking failed: {e}, using original order")
            ranked = normalized
        
        # Step 5: Validate and slice
        final = self._validate_and_slice(ranked, count=4)
        
        # Step 6: Return structured data (NO message generation)
        return {
            'activities': final,
            'state': state,
            'count': len(final)
        }
    
    def _validate_and_slice(self, activities: list, count: int = 4) -> list:
        """
        Validation layer - never return empty, remove duplicates, ensure titles
        Args:
            activities: List of activity dicts
            count: Max activities to return
        Returns:
            Validated and sliced activity list
        """
        if not activities:
            logger.warning("⚠️  No activities after ranking, using generic fallback")
            return self._get_generic_fallback()
        
        # Remove activities missing title
        valid_activities = [act for act in activities if act.get('title') or act.get('name')]
        if not valid_activities:
            logger.warning("⚠️  No activities with titles, using generic fallback")
            return self._get_generic_fallback()
        
        # Remove duplicates by id (keep first occurrence)
        unique_activities = {}
        for act in valid_activities:
            act_id = act.get('id', act.get('title') or act.get('name'))
            if act_id not in unique_activities:
                unique_activities[act_id] = act
        
        final_list = list(unique_activities.values())[:count]
        logger.info(f"✅ Validated {len(final_list)} unique activities")
        return final_list
    
    def _get_fallback_activities(self, state: str) -> list:
        """Get hardcoded activities for state (from existing system)"""
        # Use existing STATE_TO_ACTIVITIES mapping
        engine = IntelligentSuggestionEngine()
        if state in engine.STATE_TO_ACTIVITIES:
            activities_data = engine.STATE_TO_ACTIVITIES[state]
            activities = activities_data.get('activities', [])
            for activity in activities:
                activity['source'] = 'fallback'
            return activities
        
        # Generic fallback
        return self._get_generic_fallback()
    
    def _get_generic_fallback(self) -> list:
        """Last resort - generic activities"""
        return [
            {
                'id': 'breathing',
                'title': 'Breathing Exercise',
                'name': 'Breathing Exercise',
                'description': 'Quick breathing exercise',
                'duration': '5 min',
                'effort': 'low',
                'source': 'generic'
            },
            {
                'id': 'stretching',
                'title': 'Stretching',
                'name': 'Stretching',
                'description': 'Gentle stretching',
                'duration': '10 min',
                'effort': 'low',
                'source': 'generic'
            },
            {
                'id': 'take_break',
                'title': 'Take a Break',
                'name': 'Take a Break',
                'description': 'Step away for a moment',
                'duration': '5 min',
                'effort': 'low',
                'source': 'generic'
            }
        ]
    
    def _normalize_activity(self, activity: dict) -> dict:
        """Normalize activity to standard format"""
        return {
            'id': activity.get('id', activity.get('key', 0)),
            'title': activity.get('title', activity.get('name', 'Activity')),
            'name': activity.get('name', activity.get('title', 'Activity')),
            'description': activity.get('description', ''),
            'duration': activity.get('duration', activity.get('duration_minutes', '10 min')),
            'effort': activity.get('effort', activity.get('difficulty_level', 'low')),
            'source': activity.get('source', 'fallback')
        }
    
    def _default_ranker(self, activities: list, user_id: int, context: dict) -> list:
        """Default ranking if no ranker injected"""
        # Simple ranking by effort level
        effort_priority = ['low', 'medium', 'high']
        def rank_key(activity):
            effort = activity.get('effort', 'low')
            try:
                return effort_priority.index(effort)
            except ValueError:
                return len(effort_priority)
        return sorted(activities, key=rank_key)


# ===== FACTORY AND DEPENDENCY INJECTION =====
def create_enhanced_suggestion_engine(ranker=None):
    """
    Factory to create enhanced suggestion engine with dependencies
    Args:
        ranker: Optional custom ranking function
    Returns:
        Configured EnhancedIntelligentSuggestionEngine
    """
    # Try to import smart_suggestions ranker
    try:
        from chat_assistant.smart_suggestions import get_smart_suggestions
        # Create a wrapper that matches expected signature
        def smart_ranker(activities, user_id, context):
            # For now, return as-is (smart_suggestions works differently)
            return activities
        ranker = ranker or smart_ranker
    except ImportError:
        logger.warning("Smart suggestions not available, using default ranker")
    
    return EnhancedIntelligentSuggestionEngine(ranker=ranker)


# Update global instance to use enhanced version
def get_enhanced_suggestion_engine() -> EnhancedIntelligentSuggestionEngine:
    """Get or create enhanced suggestion engine"""
    global _suggestion_engine
    if _suggestion_engine is None or not isinstance(_suggestion_engine, EnhancedIntelligentSuggestionEngine):
        _suggestion_engine = create_enhanced_suggestion_engine()
    return _suggestion_engine
