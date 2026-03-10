#!/usr/bin/env python3
"""
Show Demo User Summary
Display all the data created for the demo user
"""

import sqlite3
import os
from datetime import datetime, timedelta

def get_db_path():
    """Get database path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, 'mood_capture.db')

def show_comprehensive_summary():
    """Show comprehensive demo user summary"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🎉 COMPREHENSIVE DEMO USER READY!")
    print("=" * 60)
    
    # Basic counts
    print("📊 DATA OVERVIEW:")
    
    cursor.execute("SELECT COUNT(*) FROM mood_logs WHERE user_id = 1")
    mood_count = cursor.fetchone()[0]
    print(f"  😊 Mood Entries: {mood_count} (30 days of emotional tracking)")
    
    cursor.execute("SELECT COUNT(*) FROM user_activity_history WHERE user_id = 1")
    activity_count = cursor.fetchone()[0]
    print(f"  🏃 Activity Records: {activity_count} (workouts, yoga, walks, etc.)")
    
    cursor.execute("SELECT COUNT(*) FROM health_activities WHERE user_id = 1")
    health_count = cursor.fetchone()[0]
    print(f"  💊 Health Data: {health_count} (water, sleep, weight, exercise)")
    
    cursor.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = 1")
    chat_count = cursor.fetchone()[0]
    print(f"  💬 Chat Messages: {chat_count} (conversations with AI coach)")
    
    cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE user_id = '1'")
    analytics_count = cursor.fetchone()[0]
    print(f"  📈 Analytics Events: {analytics_count} (behavioral tracking)")
    
    cursor.execute("SELECT COUNT(*) FROM suggestion_history WHERE user_id = '1'")
    suggestion_count = cursor.fetchone()[0]
    print(f"  💡 Suggestion History: {suggestion_count} (AI recommendations)")
    
    cursor.execute("SELECT COUNT(*) FROM user_challenges WHERE user_id = 1")
    challenge_count = cursor.fetchone()[0]
    print(f"  🎯 Active Challenges: {challenge_count} (fitness goals)")
    
    # Behavior metrics
    print(f"\n📈 PERSONALIZED INSIGHTS:")
    cursor.execute("SELECT * FROM user_behavior_metrics WHERE user_id = '1'")
    metrics = cursor.fetchone()
    if metrics:
        print(f"  💤 Average Sleep: {metrics[1]} hours/night")
        print(f"  💧 Average Water: {metrics[2]} glasses/day")
        print(f"  🏃 Average Exercise: {metrics[3]} minutes/day")
        print(f"  🎯 Suggestion Acceptance: {metrics[6]}%")
        print(f"  💪 Hydration Score: {metrics[4]}/100")
        print(f"  😌 Stress Management: {100-metrics[5]}/100")
    
    # Recent mood trends
    print(f"\n😊 RECENT MOOD TRENDS:")
    cursor.execute("""
        SELECT mood_emoji, mood, reason, DATE(timestamp) as date
        FROM mood_logs WHERE user_id = 1 
        ORDER BY timestamp DESC LIMIT 7
    """)
    recent_moods = cursor.fetchall()
    for emoji, mood, reason, date in recent_moods:
        print(f"  {emoji} {mood.title()} - {reason} ({date})")
    
    # Activity patterns
    print(f"\n🏃 ACTIVITY PATTERNS:")
    cursor.execute("""
        SELECT activity_name, COUNT(*) as frequency, AVG(duration_minutes) as avg_duration
        FROM user_activity_history WHERE user_id = 1 
        GROUP BY activity_name ORDER BY frequency DESC LIMIT 5
    """)
    activities = cursor.fetchall()
    for activity, freq, avg_dur in activities:
        print(f"  • {activity}: {freq} times (avg {avg_dur:.0f} min)")
    
    # Health trends
    print(f"\n💊 HEALTH TRENDS (Last 7 Days):")
    cursor.execute("""
        SELECT activity_type, AVG(value) as avg_value, unit
        FROM health_activities WHERE user_id = 1 
        AND timestamp >= date('now', '-7 days')
        GROUP BY activity_type, unit
    """)
    health_trends = cursor.fetchall()
    for activity_type, avg_value, unit in health_trends:
        print(f"  • {activity_type.title()}: {avg_value:.1f} {unit}/day")
    
    # Challenge progress
    print(f"\n🎯 CHALLENGE PROGRESS:")
    cursor.execute("""
        SELECT c.title, uc.progress, uc.days_completed, uc.points_earned, uc.status
        FROM user_challenges uc
        JOIN challenges c ON uc.challenge_id = c.id
        WHERE uc.user_id = 1
    """)
    challenges = cursor.fetchall()
    for title, progress, days, points, status in challenges:
        print(f"  • {title}: {progress}% complete ({days} days, {points} points)")
    
    # AI Insights Available
    print(f"\n🤖 AI FEATURES READY:")
    print(f"  ✅ Mood-based activity suggestions")
    print(f"  ✅ Personalized workout recommendations")
    print(f"  ✅ Health pattern analysis")
    print(f"  ✅ Progress tracking and insights")
    print(f"  ✅ Intelligent conversation flow")
    print(f"  ✅ Challenge recommendations")
    print(f"  ✅ Behavioral trend analysis")
    
    print(f"\n🔑 LOGIN CREDENTIALS:")
    print(f"   Username: demo")
    print(f"   Password: demo123")
    
    print(f"\n🚀 READY FOR DEMONSTRATION:")
    print(f"   • Rich 30-day history for realistic insights")
    print(f"   • Multiple data types for comprehensive analysis")
    print(f"   • Active challenges with progress tracking")
    print(f"   • Conversation history for context-aware chat")
    print(f"   • Behavioral patterns for personalized suggestions")
    
    conn.close()

if __name__ == '__main__':
    show_comprehensive_summary()