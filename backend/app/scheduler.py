# app/scheduler.py
# APScheduler for proactive notifications and reminders

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.user_context_service import get_context_service
from app.services.notification_service import get_notification_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

# ===== REMINDER JOBS =====

@scheduler.scheduled_job('cron', hour=15, minute=0, id='water_reminder')
async def water_reminder_job():
    """
    3:00 PM Daily: Send water reminders to users who need them (mid-afternoon check)
    """
    logger.info("🕐 Running water reminder job")
    
    context_service = get_context_service()
    notification_service = get_notification_service()
    
    active_users = context_service.get_active_users()
    sent_count = 0
    
    for user_id in active_users:
        try:
            result = context_service.should_send_reminder(user_id, 'water_reminder')
            
            if result['should_send']:
                progress = result['data']
                message = _generate_water_reminder_message(progress)
                
                notification_service.send_notification(user_id, {
                    'title': '💧 Hydration Reminder',
                    'message': message,
                    'type': 'reminder',
                    'action_buttons': [
                        {'id': 'log_water', 'label': '💧 Log Water'}
                    ],
                    'priority': 'normal'
                })
                
                sent_count += 1
                logger.info(f"  ✓ Sent water reminder to user {user_id}")
        
        except Exception as e:
            logger.error(f"  ✗ Failed to send water reminder to user {user_id}: {e}")
    
    logger.info(f"✅ Water reminder job complete: {sent_count}/{len(active_users)} sent")


@scheduler.scheduled_job('cron', hour=16, minute=0, id='mood_reminder')
async def mood_reminder_job():
    """
    4 PM Daily: Remind users to log their mood (appears naturally when they open chat)
    """
    logger.info("🕐 Running mood reminder job")
    
    context_service = get_context_service()
    notification_service = get_notification_service()
    
    active_users = context_service.get_active_users()
    sent_count = 0
    
    for user_id in active_users:
        try:
            result = context_service.should_send_reminder(user_id, 'mood_reminder')
            
            if result['should_send']:
                notification_service.send_notification(user_id, {
                    'title': '😊 Mood Check-in',
                    'message': 'Good evening! How are you feeling today? Take a moment to reflect on your day.',
                    'type': 'reminder',
                    'action_buttons': [
                        {'id': 'log_mood', 'label': '😊 Log Mood'}
                    ],
                    'priority': 'normal'
                })
                
                sent_count += 1
                logger.info(f"  ✓ Sent mood reminder to user {user_id}")
        
        except Exception as e:
            logger.error(f"  ✗ Failed to send mood reminder to user {user_id}: {e}")
    
    logger.info(f"✅ Mood reminder job complete: {sent_count}/{len(active_users)} sent")


@scheduler.scheduled_job('cron', hour=18, minute=0, id='exercise_reminder')
async def exercise_reminder_job():
    """
    6 PM Daily: Remind users about exercise
    """
    logger.info("🕐 Running exercise reminder job")
    
    context_service = get_context_service()
    notification_service = get_notification_service()
    
    active_users = context_service.get_active_users()
    sent_count = 0
    
    for user_id in active_users:
        try:
            result = context_service.should_send_reminder(user_id, 'exercise_reminder')
            
            if result['should_send']:
                progress = result['data']
                message = _generate_exercise_reminder_message(progress)
                
                notification_service.send_notification(user_id, {
                    'title': '🏃 Exercise Reminder',
                    'message': message,
                    'type': 'reminder',
                    'action_buttons': [
                        {'id': 'log_exercise', 'label': '🏃 Log Exercise'}
                    ],
                    'priority': 'normal'
                })
                
                sent_count += 1
                logger.info(f"  ✓ Sent exercise reminder to user {user_id}")
        
        except Exception as e:
            logger.error(f"  ✗ Failed to send exercise reminder to user {user_id}: {e}")
    
    logger.info(f"✅ Exercise reminder job complete: {sent_count}/{len(active_users)} sent")


@scheduler.scheduled_job('cron', hour=20, minute=0, id='evening_challenges')
async def evening_challenges_job():
    """
    8 PM Daily: Remind about incomplete challenges
    """
    logger.info("🕐 Running evening challenges reminder job")
    
    context_service = get_context_service()
    notification_service = get_notification_service()
    
    active_users = context_service.get_active_users()
    sent_count = 0
    
    for user_id in active_users:
        try:
            result = context_service.should_send_reminder(user_id, 'evening_challenges')
            
            if result['should_send']:
                incomplete = result['data']['incomplete_challenges']
                message = _generate_evening_challenges_message(incomplete)
                
                notification_service.send_notification(user_id, {
                    'title': '⏰ Challenge Reminder',
                    'message': message,
                    'type': 'reminder',
                    'priority': 'normal'
                })
                
                sent_count += 1
                logger.info(f"  ✓ Sent evening challenges reminder to user {user_id}")
        
        except Exception as e:
            logger.error(f"  ✗ Failed to send evening challenges reminder to user {user_id}: {e}")
    
    logger.info(f"✅ Evening challenges job complete: {sent_count}/{len(active_users)} sent")


# ===== MESSAGE GENERATORS =====

def _generate_water_reminder_message(progress: dict) -> str:
    """Generate personalized water reminder message"""
    current = progress['current']
    target = progress['target']
    remaining = progress['remaining']
    percentage = progress['percentage']
    challenge_title = progress.get('challenge_title', 'water challenge')
    
    if current == 0:
        return f"You haven't started your {challenge_title} yet! You need {target} glasses total. Let's get hydrated! 💧"
    elif percentage < 25:
        return f"You've logged {current}/{target} glasses for your {challenge_title}. You need {remaining} more glasses to reach your goal! 💧"
    elif percentage < 50:
        return f"Great progress! {current}/{target} glasses logged. Just {remaining} more glasses to complete your {challenge_title}! 💧"
    elif percentage < 75:
        return f"You're doing amazing! {current}/{target} glasses done. Only {remaining} more glasses to finish your {challenge_title}! 💧"
    else:
        return f"Almost there! Just {remaining} more glasses to complete your {challenge_title} of {target} glasses! You've got this! 💧"


def _generate_exercise_reminder_message(progress: dict) -> str:
    """Generate personalized exercise reminder message"""
    current = progress['current']
    target = progress['target']
    remaining = progress['remaining']
    
    if current == 0:
        return f"You haven't logged any exercise today! Your goal is {target} minutes. Let's get moving! 🏃"
    else:
        return f"You've done {current}/{target} minutes of exercise. Just {remaining} more minutes to go! 🏃"


def _generate_evening_challenges_message(incomplete: list) -> str:
    """Generate evening challenges reminder message"""
    if len(incomplete) == 1:
        challenge = incomplete[0]
        return f"You still have '{challenge['challenge_title']}' pending today. You're at {challenge['percentage']:.0f}% - finish strong! 💪"
    else:
        message = f"You have {len(incomplete)} challenges still pending today:\n\n"
        for ch in incomplete:
            message += f"• {ch['challenge_title']}: {ch['percentage']:.0f}%\n"
        message += "\nYou've got this! 💪"
        return message


@scheduler.scheduled_job('cron', hour=2, minute=0, id='token_cleanup')
async def token_cleanup_job():
    """
    2 AM Daily: Clean up expired blacklisted tokens
    """
    logger.info("🕐 Running token cleanup job")
    
    try:
        from app.services.token_service import TokenService
        token_service = TokenService()
        token_service.cleanup_expired_tokens()
        logger.info("✅ Token cleanup job complete")
    except Exception as e:
        logger.error(f"❌ Token cleanup job failed: {e}")


# ===== SCHEDULER LIFECYCLE =====

def start_scheduler():
    """Start the scheduler"""
    try:
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
        logger.info(f"📋 Scheduled jobs: {len(scheduler.get_jobs())}")
        
        # Log all scheduled jobs
        for job in scheduler.get_jobs():
            logger.info(f"  - {job.id}: {job.next_run_time}")
    
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")


def stop_scheduler():
    """Stop the scheduler"""
    try:
        scheduler.shutdown()
        logger.info("❌ Scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")


def get_scheduler_status() -> dict:
    """Get scheduler status for monitoring"""
    return {
        'running': scheduler.running,
        'jobs_count': len(scheduler.get_jobs()),
        'jobs': [
            {
                'id': job.id,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
