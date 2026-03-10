# Scheduler Use Cases for MoodCapture App

## What is a Scheduler?

A scheduler runs tasks automatically at specific times or intervals, without user interaction.

Think of it as a **robot assistant** that wakes up at scheduled times to do work for you.

---

## Use Cases for YOUR App (MoodCapture)

### 1. **Proactive Reminders** ⏰

Send reminders to users who need them.

#### Water Reminder
```python
@scheduler.scheduled_job('cron', hour=14, minute=0)  # 2 PM daily
async def water_reminder():
    """Remind users who haven't drunk enough water"""
    for user in get_active_users():
        progress = get_water_progress(user.id)
        if progress < 50%:  # Less than half done
            send_notification(user.id, "💧 Don't forget to drink water!")
```

**When:** 2 PM daily  
**Why:** Afternoon is good time to check hydration  
**Who:** Only users who are behind on their water goal

#### Mood Check-in Reminder
```python
@scheduler.scheduled_job('cron', hour=10, minute=0)  # 10 AM daily
async def mood_reminder():
    """Remind users who haven't logged mood today"""
    for user in get_active_users():
        if not has_logged_mood_today(user.id):
            send_notification(user.id, "😊 How are you feeling today?")
```

**When:** 10 AM daily  
**Why:** Morning is good time for mood check-in  
**Who:** Only users who haven't logged mood yet

#### Evening Challenge Reminder
```python
@scheduler.scheduled_job('cron', hour=20, minute=0)  # 8 PM daily
async def evening_challenge_reminder():
    """Remind about incomplete challenges before day ends"""
    for user in get_active_users():
        incomplete = get_incomplete_challenges(user.id)
        if incomplete:
            send_notification(user.id, 
                f"⏰ {len(incomplete)} challenge(s) still pending today!")
```

**When:** 8 PM daily  
**Why:** Last chance to complete daily challenges  
**Who:** Users with incomplete challenges

---

### 2. **Streak Tracking & Celebrations** 🎉

Celebrate user achievements automatically.

#### Daily Streak Check
```python
@scheduler.scheduled_job('cron', hour=23, minute=0)  # 11 PM daily
async def check_streaks():
    """Check and celebrate activity streaks"""
    for user in get_active_users():
        # Check water streak
        water_streak = get_streak(user.id, 'water')
        if water_streak in [3, 7, 14, 30]:  # Milestones
            send_notification(user.id, 
                f"🔥 Amazing! {water_streak}-day water streak!")
        
        # Check mood logging streak
        mood_streak = get_mood_streak(user.id)
        if mood_streak == 7:
            send_notification(user.id, 
                "🌟 7 days of mood tracking! You're building a great habit!")
```

**When:** 11 PM daily (end of day)  
**Why:** Celebrate achievements when day is complete  
**Who:** Users who hit streak milestones

---

### 3. **Challenge Management** 🏆

Automatically manage challenge lifecycle.

#### Start New Challenges
```python
@scheduler.scheduled_job('cron', day_of_week='mon', hour=0)  # Monday midnight
async def start_weekly_challenges():
    """Start new weekly challenges"""
    create_challenge(
        title="Mindfulness Week",
        type="meditation",
        duration=7,
        start_date=today()
    )
    
    # Notify users
    for user in get_active_users():
        send_notification(user.id, 
            "🆕 New challenge available: Mindfulness Week!")
```

**When:** Every Monday at midnight  
**Why:** Fresh start for weekly challenges  
**Who:** All active users

#### End Expired Challenges
```python
@scheduler.scheduled_job('cron', hour=0, minute=0)  # Midnight daily
async def end_expired_challenges():
    """Mark expired challenges as complete/failed"""
    expired = get_expired_challenges()
    
    for challenge in expired:
        if challenge.progress >= 100:
            mark_as_completed(challenge)
            award_points(challenge.user_id, challenge.points)
            send_notification(challenge.user_id,
                f"🎉 Challenge completed! +{challenge.points} points!")
        else:
            mark_as_failed(challenge)
            send_notification(challenge.user_id,
                f"Challenge ended. You completed {challenge.progress}%")
```

**When:** Midnight daily  
**Why:** Clean up expired challenges  
**Who:** Users with expired challenges

---

### 4. **Data Analysis & Insights** 📊

Generate insights from user data.

#### Weekly Summary
```python
@scheduler.scheduled_job('cron', day_of_week='sun', hour=20)  # Sunday 8 PM
async def generate_weekly_summary():
    """Generate and send weekly summary to users"""
    for user in get_active_users():
        summary = {
            'water_avg': get_weekly_avg(user.id, 'water'),
            'sleep_avg': get_weekly_avg(user.id, 'sleep'),
            'mood_trend': get_mood_trend(user.id, days=7),
            'challenges_completed': count_completed_challenges(user.id, days=7),
            'streak_days': get_longest_streak(user.id)
        }
        
        message = format_weekly_summary(summary)
        send_notification(user.id, message)
```

**When:** Sunday 8 PM (end of week)  
**Why:** Users can reflect on their week  
**Who:** All active users

#### Stress Pattern Detection
```python
@scheduler.scheduled_job('cron', hour=9, minute=0)  # 9 AM daily
async def detect_stress_patterns():
    """Detect users with prolonged stress and offer help"""
    for user in get_active_users():
        stress_days = count_consecutive_stress_days(user.id)
        
        if stress_days >= 3:
            send_notification(user.id,
                f"💙 You've been stressed for {stress_days} days. "
                "Would you like some activity suggestions?")
```

**When:** 9 AM daily  
**Why:** Early intervention for stressed users  
**Who:** Users with 3+ consecutive stress days

---

### 5. **Database Maintenance** 🗄️

Keep your database clean and optimized.

#### Clean Old Data
```python
@scheduler.scheduled_job('cron', day_of_week='sun', hour=2)  # Sunday 2 AM
async def cleanup_old_data():
    """Delete old data to save space"""
    # Delete read notifications older than 30 days
    delete_old_notifications(days=30)
    
    # Archive old chat messages (older than 90 days)
    archive_old_messages(days=90)
    
    # Delete expired sessions
    delete_expired_sessions()
    
    logger.info("Database cleanup completed")
```

**When:** Sunday 2 AM (low traffic time)  
**Why:** Keep database size manageable  
**Who:** System maintenance (no user notification)

#### Backup Database
```python
@scheduler.scheduled_job('cron', hour=3, minute=0)  # 3 AM daily
async def backup_database():
    """Create daily database backup"""
    backup_path = f"backups/db_backup_{date.today()}.sqlite"
    create_backup(backup_path)
    
    # Keep only last 7 days of backups
    delete_old_backups(keep_days=7)
    
    logger.info(f"Database backed up to {backup_path}")
```

**When:** 3 AM daily (low traffic time)  
**Why:** Disaster recovery  
**Who:** System maintenance

---

### 6. **User Engagement** 💬

Re-engage inactive users.

#### Inactive User Nudge
```python
@scheduler.scheduled_job('cron', hour=18, minute=0)  # 6 PM daily
async def nudge_inactive_users():
    """Re-engage users who haven't used app in 3 days"""
    inactive_users = get_users_inactive_for_days(3)
    
    for user in inactive_users:
        last_activity = get_last_activity(user.id)
        
        send_notification(user.id,
            f"👋 We miss you! It's been {last_activity.days} days. "
            "How are you feeling today?")
```

**When:** 6 PM daily  
**Why:** Evening is good time to re-engage  
**Who:** Users inactive for 3+ days

#### Personalized Tips
```python
@scheduler.scheduled_job('cron', hour=12, minute=0)  # Noon daily
async def send_daily_tip():
    """Send personalized wellness tip"""
    for user in get_active_users():
        # Analyze user's patterns
        patterns = analyze_user_patterns(user.id)
        
        # Generate personalized tip
        tip = generate_tip_based_on_patterns(patterns)
        
        send_notification(user.id, f"💡 Daily Tip: {tip}")
```

**When:** Noon daily  
**Why:** Midday motivation boost  
**Who:** All active users

---

### 7. **Performance Monitoring** 📈

Monitor app health and performance.

#### Health Check
```python
@scheduler.scheduled_job('interval', minutes=5)
async def health_check():
    """Check if critical services are running"""
    checks = {
        'database': check_database_connection(),
        'llm_service': check_llm_api(),
        'notification_service': check_notification_service()
    }
    
    for service, status in checks.items():
        if not status:
            alert_admin(f"⚠️ {service} is down!")
            logger.error(f"{service} health check failed")
```

**When:** Every 5 minutes  
**Why:** Early detection of issues  
**Who:** System monitoring (admin alerts)

#### Usage Analytics
```python
@scheduler.scheduled_job('cron', hour=1, minute=0)  # 1 AM daily
async def calculate_daily_metrics():
    """Calculate daily usage metrics"""
    metrics = {
        'active_users': count_active_users_today(),
        'messages_sent': count_messages_today(),
        'moods_logged': count_moods_today(),
        'challenges_completed': count_challenges_completed_today(),
        'avg_response_time': calculate_avg_response_time()
    }
    
    store_metrics(metrics)
    
    # Alert if metrics are unusual
    if metrics['active_users'] < threshold:
        alert_admin("⚠️ Low user activity today")
```

**When:** 1 AM daily  
**Why:** Analyze previous day's data  
**Who:** Analytics (admin dashboard)

---

## Complete Scheduler Setup Example

```python
# backend/app/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

# ===== REMINDERS =====

@scheduler.scheduled_job('cron', hour=14, minute=0)
async def water_reminder():
    """2 PM: Water reminder"""
    logger.info("Running water reminder job")
    # Implementation here

@scheduler.scheduled_job('cron', hour=10, minute=0)
async def mood_reminder():
    """10 AM: Mood check-in"""
    logger.info("Running mood reminder job")
    # Implementation here

@scheduler.scheduled_job('cron', hour=20, minute=0)
async def evening_challenge_reminder():
    """8 PM: Challenge reminder"""
    logger.info("Running challenge reminder job")
    # Implementation here

# ===== CELEBRATIONS =====

@scheduler.scheduled_job('cron', hour=23, minute=0)
async def check_streaks():
    """11 PM: Check and celebrate streaks"""
    logger.info("Running streak check job")
    # Implementation here

# ===== INSIGHTS =====

@scheduler.scheduled_job('cron', day_of_week='sun', hour=20)
async def weekly_summary():
    """Sunday 8 PM: Weekly summary"""
    logger.info("Generating weekly summaries")
    # Implementation here

@scheduler.scheduled_job('cron', hour=9, minute=0)
async def stress_pattern_detection():
    """9 AM: Detect stress patterns"""
    logger.info("Running stress pattern detection")
    # Implementation here

# ===== MAINTENANCE =====

@scheduler.scheduled_job('cron', day_of_week='sun', hour=2)
async def cleanup_old_data():
    """Sunday 2 AM: Database cleanup"""
    logger.info("Running database cleanup")
    # Implementation here

@scheduler.scheduled_job('cron', hour=3, minute=0)
async def backup_database():
    """3 AM: Database backup"""
    logger.info("Creating database backup")
    # Implementation here

# ===== MONITORING =====

@scheduler.scheduled_job('interval', minutes=5)
async def health_check():
    """Every 5 minutes: Health check"""
    # Implementation here

# ===== LIFECYCLE =====

def start_scheduler():
    """Start the scheduler"""
    scheduler.start()
    logger.info("✅ Scheduler started")
    logger.info(f"Scheduled jobs: {len(scheduler.get_jobs())}")

def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("❌ Scheduler stopped")
```

```python
# backend/main.py

from fastapi import FastAPI
from app.scheduler import start_scheduler, stop_scheduler

app = FastAPI()

@app.on_event("startup")
async def startup():
    start_scheduler()
    print("🚀 App started with scheduler")

@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()
    print("👋 App stopped")
```

---

## Summary: When to Use Scheduler

### ✅ USE Scheduler For:

1. **Proactive Reminders** - Nudge users at specific times
2. **Celebrations** - Celebrate achievements automatically
3. **Insights** - Generate weekly/daily summaries
4. **Maintenance** - Clean up old data, backups
5. **Monitoring** - Health checks, analytics
6. **Re-engagement** - Bring back inactive users
7. **Challenge Management** - Start/end challenges automatically

### ❌ DON'T Use Scheduler For:

1. **User-initiated actions** - Use regular API endpoints
2. **Real-time responses** - Use WebSocket
3. **Immediate tasks** - Use background tasks (Celery)
4. **One-time tasks** - Use manual scripts

---

## Key Principle

**Scheduler = Proactive System Actions**

If it needs to happen:
- At a specific time
- Regularly (daily, weekly, hourly)
- Without user interaction
- For multiple users

→ Use Scheduler ✅
