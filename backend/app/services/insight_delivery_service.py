"""
Insight Delivery Service
Delivers insights via scheduler using unified insight system

Features:
- Frequency limiting (max 1 per 24h)
- Active user filtering
- Pattern confidence checking
- Graceful error handling
- Dry run mode for testing
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Configuration
DRY_RUN = False  # Set to False to actually send notifications
CONFIDENCE_THRESHOLDS = {
    'day_pattern': 0.60,      # 60% confidence for day patterns
    'time_pattern': 0.50,     # 50% confidence for time patterns
    'activity_pattern': 0.60, # 60% confidence for activity patterns
}

# In-memory tracking (per user)
_last_insight_sent = {}  # user_id -> {'type': str, 'timestamp': datetime}


class InsightDeliveryService:
    """Service for delivering scheduled insights to users"""
    
    def __init__(self):
        from app.services.unified_insight_system import get_unified_insight_system
        from app.services.notification_service import get_notification_service
        
        self.insight_system = get_unified_insight_system()
        self.notification_service = get_notification_service()
    
    # ===== ACTIVE USER MANAGEMENT =====
    
    def get_active_users(self) -> List[int]:
        """Get users active in last 7 days"""
        try:
            from app.core.database import get_db
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("""
                    SELECT DISTINCT user_id
                    FROM mood_logs
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                return [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
    
    # ===== FREQUENCY LIMITING =====
    
    def can_send_insight(self, user_id: int, insight_type: str) -> bool:
        """Check if user can receive insight (frequency limiting)"""
        
        # Rule 1: Max 1 insight per 24 hours (any type)
        if user_id in _last_insight_sent:
            last_sent = _last_insight_sent[user_id]['timestamp']
            hours_since = (datetime.now() - last_sent).total_seconds() / 3600
            
            if hours_since < 24:
                logger.info(f"  ⏸️  User {user_id}: Too soon (last insight {hours_since:.1f}h ago)")
                return False
        
        # Rule 2: Max 1 of same type per week
        if user_id in _last_insight_sent:
            if _last_insight_sent[user_id]['type'] == insight_type:
                last_sent = _last_insight_sent[user_id]['timestamp']
                days_since = (datetime.now() - last_sent).days
                
                if days_since < 7:
                    logger.info(f"  ⏸️  User {user_id}: Same type too soon ({days_since} days ago)")
                    return False
        
        return True
    
    def mark_insight_sent(self, user_id: int, insight_type: str):
        """Mark that insight was sent to user"""
        _last_insight_sent[user_id] = {
            'type': insight_type,
            'timestamp': datetime.now()
        }
    
    # ===== PATTERN CONFIDENCE CHECKING =====
    
    def meets_confidence_threshold(self, pattern: Dict) -> bool:
        """Check if pattern meets confidence threshold"""
        pattern_type = pattern.get('type', '')
        confidence = pattern.get('confidence', 0)
        threshold = CONFIDENCE_THRESHOLDS.get(pattern_type, 0.60)
        
        return confidence >= threshold
    
    # ===== MONDAY MORNING PREVENTIVE =====
    
    def send_monday_preventive_insights(self) -> Dict:
        """Send preventive insights for Monday stress (Monday 9 AM)"""
        logger.info("🕐 Starting Monday preventive insights job")
        
        active_users = self.get_active_users()
        sent_count = 0
        skipped_count = 0
        
        for user_id in active_users:
            try:
                # Check frequency limit
                if not self.can_send_insight(user_id, 'monday_preventive'):
                    skipped_count += 1
                    continue
                
                # Get patterns
                from app.core.database import get_db
                
                with get_db() as db:
                    patterns = self.insight_system.pattern_detector.detect_all_patterns(user_id, db)
                
                # Check for Monday stress pattern
                monday_pattern = None
                for pattern in patterns.get('day_patterns', []):
                    if pattern.get('day') == 'Monday' and self.meets_confidence_threshold(pattern):
                        monday_pattern = pattern
                        break
                
                if not monday_pattern:
                    logger.info(f"  ⏭️  User {user_id}: No Monday stress pattern")
                    skipped_count += 1
                    continue
                
                # Generate LLM message
                message = self.insight_system.llm_generator.generate_insight_message(
                    pattern_type='day_pattern',
                    pattern_data=monday_pattern,
                    user_context={},
                    priority='medium'
                )
                
                # Send notification
                self._send_insight_notification(
                    user_id=user_id,
                    title='💡 Monday Morning Boost',
                    message=message,
                    insight_type='monday_preventive',
                    action_buttons=[
                        {'id': 'start_routine', 'label': '✨ Start Routine'},
                        {'id': 'not_today', 'label': 'Not today'}
                    ]
                )
                
                sent_count += 1
                logger.info(f"  ✅ Sent Monday preventive to user {user_id}")
            
            except Exception as e:
                logger.error(f"  ❌ Failed for user {user_id}: {e}")
                continue
        
        logger.info(f"✅ Monday preventive job complete: {sent_count} sent, {skipped_count} skipped")
        
        return {
            'sent': sent_count,
            'skipped': skipped_count,
            'total': len(active_users)
        }
    
    # ===== AFTERNOON ENERGY BOOST =====
    
    def send_afternoon_energy_insights(self) -> Dict:
        """Send energy boost insights for 3 PM fatigue (Daily 2:55 PM)"""
        logger.info("🕐 Starting afternoon energy insights job")
        
        active_users = self.get_active_users()
        sent_count = 0
        skipped_count = 0
        
        for user_id in active_users:
            try:
                # Check frequency limit
                if not self.can_send_insight(user_id, 'afternoon_energy'):
                    skipped_count += 1
                    continue
                
                # Get patterns
                from app.core.database import get_db
                
                with get_db() as db:
                    patterns = self.insight_system.pattern_detector.detect_all_patterns(user_id, db)
                
                # Check for 3 PM fatigue pattern (hour 15)
                fatigue_pattern = None
                for pattern in patterns.get('time_patterns', []):
                    hour = pattern.get('hour', 0)
                    if 14 <= hour <= 16 and self.meets_confidence_threshold(pattern):
                        fatigue_pattern = pattern
                        break
                
                if not fatigue_pattern:
                    logger.info(f"  ⏭️  User {user_id}: No afternoon fatigue pattern")
                    skipped_count += 1
                    continue
                
                # Generate LLM message
                message = self.insight_system.llm_generator.generate_insight_message(
                    pattern_type='time_pattern',
                    pattern_data=fatigue_pattern,
                    user_context={},
                    priority='medium'
                )
                
                # Send notification
                self._send_insight_notification(
                    user_id=user_id,
                    title='💡 Energy Boost Time ⚡',
                    message=message,
                    insight_type='afternoon_energy',
                    action_buttons=[
                        {'id': 'quick_activity', 'label': '⚡ Quick Boost'},
                        {'id': 'im_good', 'label': "I'm good, thanks"}
                    ]
                )
                
                sent_count += 1
                logger.info(f"  ✅ Sent afternoon energy to user {user_id}")
            
            except Exception as e:
                logger.error(f"  ❌ Failed for user {user_id}: {e}")
                continue
        
        logger.info(f"✅ Afternoon energy job complete: {sent_count} sent, {skipped_count} skipped")
        
        return {
            'sent': sent_count,
            'skipped': skipped_count,
            'total': len(active_users)
        }
    
    # ===== PATTERN DISCOVERY =====
    
    def send_pattern_discovery_insights(self) -> Dict:
        """Send insights about newly discovered patterns (Daily 10 AM)"""
        logger.info("🕐 Starting pattern discovery insights job")
        
        active_users = self.get_active_users()
        sent_count = 0
        skipped_count = 0
        
        for user_id in active_users:
            try:
                # Check frequency limit
                if not self.can_send_insight(user_id, 'pattern_discovery'):
                    skipped_count += 1
                    continue
                
                # Get patterns
                from app.core.database import get_db
                
                with get_db() as db:
                    patterns = self.insight_system.pattern_detector.detect_all_patterns(user_id, db)
                
                # Find strongest pattern (highest confidence)
                all_patterns = []
                
                for pattern in patterns.get('day_patterns', []):
                    if self.meets_confidence_threshold(pattern):
                        all_patterns.append(pattern)
                
                for pattern in patterns.get('activity_patterns', []):
                    if self.meets_confidence_threshold(pattern):
                        all_patterns.append(pattern)
                
                if not all_patterns:
                    logger.info(f"  ⏭️  User {user_id}: No strong patterns")
                    skipped_count += 1
                    continue
                
                # Get strongest pattern
                strongest = max(all_patterns, key=lambda p: p.get('confidence', 0))
                
                # Generate LLM message
                message = self.insight_system.llm_generator.generate_insight_message(
                    pattern_type=strongest['type'],
                    pattern_data=strongest,
                    user_context={},
                    priority='low'
                )
                
                # Send notification
                self._send_insight_notification(
                    user_id=user_id,
                    title='💡 Pattern Discovered 🔍',
                    message=message,
                    insight_type='pattern_discovery',
                    action_buttons=[
                        {'id': 'tell_me_more', 'label': '📊 Tell me more'},
                        {'id': 'got_it', 'label': 'Got it!'}
                    ]
                )
                
                sent_count += 1
                logger.info(f"  ✅ Sent pattern discovery to user {user_id}")
            
            except Exception as e:
                logger.error(f"  ❌ Failed for user {user_id}: {e}")
                continue
        
        logger.info(f"✅ Pattern discovery job complete: {sent_count} sent, {skipped_count} skipped")
        
        return {
            'sent': sent_count,
            'skipped': skipped_count,
            'total': len(active_users)
        }
    
    # ===== WEEKLY SUMMARY =====
    
    def send_weekly_summaries(self) -> Dict:
        """Send weekly summaries to active users (Friday 7 PM)"""
        logger.info("🕐 Starting weekly summary insights job")
        
        active_users = self.get_active_users()
        sent_count = 0
        skipped_count = 0
        
        for user_id in active_users:
            try:
                # Check frequency limit
                if not self.can_send_insight(user_id, 'weekly_summary'):
                    skipped_count += 1
                    continue
                
                # Generate weekly summary
                summary = self.insight_system.generate_weekly_summary(user_id)
                
                if not summary:
                    logger.info(f"  ⏭️  User {user_id}: No weekly summary data")
                    skipped_count += 1
                    continue
                
                # Send notification
                self._send_insight_notification(
                    user_id=user_id,
                    title='📊 Your Weekly Summary',
                    message=summary['message'],
                    insight_type='weekly_summary',
                    action_buttons=[
                        {'id': 'view_details', 'label': '📈 View Details'},
                        {'id': 'thanks', 'label': 'Thanks!'}
                    ]
                )
                
                sent_count += 1
                logger.info(f"  ✅ Sent weekly summary to user {user_id}")
            
            except Exception as e:
                logger.error(f"  ❌ Failed for user {user_id}: {e}")
                continue
        
        logger.info(f"✅ Weekly summary job complete: {sent_count} sent, {skipped_count} skipped")
        
        return {
            'sent': sent_count,
            'skipped': skipped_count,
            'total': len(active_users)
        }
    
    # ===== MOOD FOLLOW-UPS =====
    
    def send_mood_followups(self) -> Dict:
        """Send follow-up messages for mood improvements or persistent issues (Daily 12 PM)"""
        logger.info("🕐 Starting mood follow-up insights job")
        
        active_users = self.get_active_users()
        sent_count = 0
        skipped_count = 0
        
        for user_id in active_users:
            try:
                # Check frequency limit
                if not self.can_send_insight(user_id, 'mood_followup'):
                    skipped_count += 1
                    continue
                
                # Check for follow-up opportunities
                followup = self.insight_system.check_follow_up(user_id)
                
                if not followup:
                    logger.info(f"  ⏭️  User {user_id}: No follow-up needed")
                    skipped_count += 1
                    continue
                
                # Determine title based on follow-up type
                followup_type = followup['followup_type']
                if followup_type == 'mood_improvement':
                    title = '🎉 Great Progress!'
                elif followup_type == 'persistent_negative':
                    title = '💙 I\'m Here for You'
                elif followup_type == 'event_followup':
                    title = '📅 Following Up'
                else:
                    title = '💡 Checking In'
                
                # Send notification
                self._send_insight_notification(
                    user_id=user_id,
                    title=title,
                    message=followup['message'],
                    insight_type='mood_followup',
                    action_buttons=[
                        {'id': 'tell_more', 'label': '💬 Tell me more'},
                        {'id': 'thanks', 'label': 'Thanks!'}
                    ]
                )
                
                sent_count += 1
                logger.info(f"  ✅ Sent mood follow-up to user {user_id}")
            
            except Exception as e:
                logger.error(f"  ❌ Failed for user {user_id}: {e}")
                continue
        
        logger.info(f"✅ Mood follow-up job complete: {sent_count} sent, {skipped_count} skipped")
        
        return {
            'sent': sent_count,
            'skipped': skipped_count,
            'total': len(active_users)
        }
    
    # ===== HELPER METHODS =====
    
    def _send_insight_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        insight_type: str,
        action_buttons: List[Dict] = None
    ):
        """Send insight notification (or log if dry run)"""
        
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would send to user {user_id}:")
            logger.info(f"  Title: {title}")
            logger.info(f"  Message: {message[:100]}...")
            logger.info(f"  Type: {insight_type}")
            return
        
        # Actually send
        self.notification_service.send_notification(user_id, {
            'title': title,
            'message': message,
            'type': 'insight',
            'action_buttons': action_buttons or [],
            'priority': 'normal'
        })
        
        # Mark sent
        self.mark_insight_sent(user_id, insight_type)


# Global instance
_insight_delivery_service = None

def get_insight_delivery_service() -> InsightDeliveryService:
    """Get or create global InsightDeliveryService instance"""
    global _insight_delivery_service
    if _insight_delivery_service is None:
        _insight_delivery_service = InsightDeliveryService()
    return _insight_delivery_service
