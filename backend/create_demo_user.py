#!/usr/bin/env python3
"""
Create Comprehensive Demo User
Creates a demo user with rich data to showcase all features
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta, date
import json
import random

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def get_db_path():
    """Get database path"""
    return os.path.join(backend_dir, 'mood_capture.db')

def create_demo_user():
    """Create a comprehensive demo user with rich data"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("👤 Creating comprehensive demo user...")
    
    try:
        from app.core.security import get_password_hash
        
        # Create demo user with bcrypt password
        demo_password = get_password_hash('demo123')
        
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (id, username, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 'demo', 'demo@example.com', demo_password, 'Demo User', '2024-02-15 08:00:00'))
        
        print("✅ Demo user created/updated")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Clear existing demo data
    cursor.execute("DELETE FROM mood_logs WHERE user_id = 1")
    cursor.execute("DELETE FROM user_activity_history WHERE user_id = 1")
    cursor.execute("DELETE FROM health_activities WHERE user_id = 1")
    cursor.execute("DELETE FROM chat_messages WHERE user_id = 1")
    cursor.execute("DELETE FROM user_challenges WHERE user_id = 1")
    cursor.execute("DELETE FROM challenge_progress WHERE user_challenge_id IN (SELECT id FROM user_challenges WHERE user_id = 1)")
    cursor.execute("DELETE FROM analytics_events WHERE user_id = '1'")
    cursor.execute("DELETE FROM suggestion_history WHERE user_id = '1'")
    
    print("🗑️  Cleared existing demo data")
    
    # Create 30 days of comprehensive data
    base_date = datetime.now() - timedelta(days=30)
    
    mood_data = []
    activity_data = []
    health_data = []
    chat_data = []
    analytics_data = []
    suggestion_data = []
    
    # Define mood patterns (realistic ups and downs)
    mood_patterns = [
        ('😊', 'happy', 'Had a great workout this morning'),
        ('😄', 'awesome', 'Achieved my daily goals'),
        ('😐', 'okay', 'Regular day, nothing special'),
        ('😟', 'worried', 'Stressful day at work'),
        ('😢', 'sad', 'Feeling overwhelmed'),
        ('😌', 'calm', 'Enjoyed meditation session'),
        ('⚡', 'energetic', 'Feeling motivated and ready'),
        ('😴', 'tired', 'Long day, need rest'),
        ('💪', 'motivated', 'Ready to tackle challenges'),
        ('🤗', 'grateful', 'Thankful for good health')
    ]
    
    # Activity types with realistic patterns
    activities = [
        ('morning_yoga', 'Morning Yoga', 20, 'morning'),
        ('evening_walk', 'Evening Walk', 30, 'evening'),
        ('gym_workout', 'Gym Workout', 60, 'morning'),
        ('meditation', 'Meditation', 15, 'morning'),
        ('stretching', 'Stretching', 10, 'evening'),
        ('running', 'Running', 45, 'morning'),
        ('cycling', 'Cycling', 40, 'afternoon'),
        ('swimming', 'Swimming', 50, 'afternoon'),
        ('strength_training', 'Strength Training', 45, 'morning'),
        ('pilates', 'Pilates', 35, 'evening')
    ]
    
    print("📊 Generating 30 days of comprehensive data...")
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        day_of_week = current_date.strftime('%A')
        
        # Generate 1-3 mood logs per day
        num_moods = random.randint(1, 3)
        for mood_idx in range(num_moods):
            mood_emoji, mood_name, reason = random.choice(mood_patterns)
            mood_time = current_date + timedelta(hours=random.randint(7, 22), minutes=random.randint(0, 59))
            
            mood_data.append((
                1, mood_name, mood_emoji, 
                random.randint(1, 10),  # intensity
                random.randint(1, 10),  # stress_level
                random.randint(1, 10),  # energy_level
                random.randint(1, 10),  # confidence_level
                reason, 'general', None, mood_time.strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        # Generate 2-5 activities per day
        num_activities = random.randint(2, 5)
        daily_activities = random.sample(activities, min(num_activities, len(activities)))
        
        for activity_id, activity_name, duration, time_of_day in daily_activities:
            if time_of_day == 'morning':
                activity_time = current_date + timedelta(hours=random.randint(6, 10))
            elif time_of_day == 'afternoon':
                activity_time = current_date + timedelta(hours=random.randint(12, 17))
            else:  # evening
                activity_time = current_date + timedelta(hours=random.randint(18, 21))
            
            activity_data.append((
                1, activity_id, activity_name,
                random.choice(['😊', '💪', '⚡', '😌']),  # mood_emoji
                f"Completed {activity_name.lower()}",  # reason
                1,  # completed
                duration + random.randint(-10, 10),  # duration with variation
                activity_time.strftime('%Y-%m-%d %H:%M:%S'),
                day_of_week, time_of_day
            ))
        
        # Generate health activities (water, sleep, weight, exercise)
        # Water intake (6-10 glasses per day)
        water_glasses = random.randint(6, 10)
        health_data.append((
            1, 'water', water_glasses, 'glasses', 
            f"Drank {water_glasses} glasses today",
            (current_date + timedelta(hours=23)).strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        # Sleep (6-9 hours)
        sleep_hours = round(random.uniform(6.0, 9.0), 1)
        health_data.append((
            1, 'sleep', sleep_hours, 'hours',
            f"Slept {sleep_hours} hours",
            (current_date + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        # Exercise minutes (20-90 minutes)
        exercise_minutes = random.randint(20, 90)
        health_data.append((
            1, 'exercise', exercise_minutes, 'minutes',
            f"Exercised for {exercise_minutes} minutes",
            (current_date + timedelta(hours=random.randint(8, 19))).strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        # Weight (weekly)
        if day % 7 == 0:
            weight = round(random.uniform(68.0, 72.0), 1)
            health_data.append((
                1, 'weight', weight, 'kg',
                f"Weekly weigh-in: {weight}kg",
                (current_date + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        # Generate chat messages (2-4 per day)
        if day % 3 == 0:  # Every 3rd day
            chat_messages = [
                ("How are you feeling today?", "user"),
                ("I'm feeling pretty good! Just finished my morning workout 💪", "user"),
                ("That's fantastic! Regular exercise is great for both physical and mental health. How was your workout?", "bot"),
                ("It was challenging but rewarding. I did some strength training.", "user"),
                ("Excellent! Strength training helps build muscle and bone density. Keep up the great work! 🎉", "bot")
            ]
            
            for idx, (message, sender) in enumerate(chat_messages):
                chat_time = current_date + timedelta(hours=9, minutes=idx*2)
                chat_data.append((
                    1, message, sender, chat_time.strftime('%Y-%m-%d %H:%M:%S'), None
                ))
        
        # Generate analytics events
        events = [
            ('mood_logged', f'{{"mood": "{random.choice(["happy", "calm", "energetic"])}", "timestamp": "{current_date.isoformat()}"}}'),
            ('activity_completed', f'{{"activity": "{random.choice(["yoga", "walking", "meditation"])}", "duration": {random.randint(15, 60)}}}'),
            ('suggestion_shown', f'{{"suggestion": "{random.choice(["breathing", "stretching", "hydration"])}", "context": "mood_based"}}'),
            ('challenge_progress', f'{{"challenge_type": "water", "progress": {random.randint(60, 100)}}}')
        ]
        
        for event_type, event_data in random.sample(events, random.randint(2, 4)):
            analytics_data.append((
                '1', event_type, event_data, current_date.strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        # Generate suggestion history
        suggestions = ['breathing', 'short_walk', 'meditation', 'stretching', 'hydrate', 'power_nap']
        for _ in range(random.randint(1, 3)):
            suggestion = random.choice(suggestions)
            shown_time = current_date + timedelta(hours=random.randint(10, 20))
            accepted = random.choice([True, False])
            
            suggestion_data.append((
                '1', suggestion, random.choice(['😊', '😐', '😟']),
                f"Suggested during {random.choice(['work', 'evening', 'afternoon'])} time",
                shown_time.strftime('%Y-%m-%d %H:%M:%S'),
                1 if accepted else 0,
                (shown_time + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S') if accepted else None
            ))
    
    # Insert all data
    print("💾 Inserting mood logs...")
    cursor.executemany("""
        INSERT INTO mood_logs 
        (user_id, mood, mood_emoji, mood_intensity, stress_level, energy_level, 
         confidence_level, reason, reason_category, tags, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, mood_data)
    
    print("💾 Inserting activity history...")
    cursor.executemany("""
        INSERT INTO user_activity_history 
        (user_id, activity_id, activity_name, mood_emoji, reason, completed, 
         duration_minutes, timestamp, day_of_week, time_of_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, activity_data)
    
    print("💾 Inserting health activities...")
    cursor.executemany("""
        INSERT INTO health_activities 
        (user_id, activity_type, value, unit, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, health_data)
    
    print("💾 Inserting chat messages...")
    cursor.executemany("""
        INSERT INTO chat_messages 
        (user_id, message, sender, timestamp, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, chat_data)
    
    print("💾 Inserting analytics events...")
    cursor.executemany("""
        INSERT INTO analytics_events 
        (user_id, event_type, event_data, created_at)
        VALUES (?, ?, ?, ?)
    """, analytics_data)
    
    print("💾 Inserting suggestion history...")
    cursor.executemany("""
        INSERT INTO suggestion_history 
        (user_id, suggestion_key, mood_emoji, reason, shown_at, accepted, accepted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, suggestion_data)
    
    # Create user behavior metrics
    print("📈 Calculating behavior metrics...")
    
    # Calculate averages from the data
    avg_sleep = sum([h[2] for h in health_data if h[1] == 'sleep']) / len([h for h in health_data if h[1] == 'sleep'])
    avg_water = sum([h[2] for h in health_data if h[1] == 'water']) / len([h for h in health_data if h[1] == 'water'])
    avg_exercise = sum([h[2] for h in health_data if h[1] == 'exercise']) / len([h for h in health_data if h[1] == 'exercise'])
    
    accepted_suggestions = len([s for s in suggestion_data if s[5] == 1])
    total_suggestions = len(suggestion_data)
    acceptance_rate = (accepted_suggestions / total_suggestions * 100) if total_suggestions > 0 else 0
    
    cursor.execute("""
        INSERT OR REPLACE INTO user_behavior_metrics 
        (user_id, avg_sleep_7d, avg_water_7d, avg_exercise_7d, hydration_score, 
         stress_score, suggestion_acceptance_rate, total_suggestions_shown, 
         total_suggestions_accepted, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '1', round(avg_sleep, 1), round(avg_water, 1), round(avg_exercise, 1),
        85.0, 65.0, round(acceptance_rate, 1), total_suggestions, accepted_suggestions,
        datetime.now().isoformat()
    ))
    
    # Join some challenges
    print("🎯 Joining challenges...")
    
    # Get available challenges
    cursor.execute("SELECT id, title, challenge_type FROM challenges WHERE is_active = 1")
    challenges = cursor.fetchall()
    
    for challenge_id, title, challenge_type in challenges[:3]:  # Join first 3 challenges
        # Join challenge
        cursor.execute("""
            INSERT OR IGNORE INTO user_challenges 
            (user_id, challenge_id, joined_at, status, progress, days_completed, points_earned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, challenge_id, (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S'),
              'active', random.randint(40, 85), random.randint(5, 20), random.randint(50, 200)))
        
        # Add some progress entries
        user_challenge_id = cursor.lastrowid
        for day in range(random.randint(5, 15)):
            progress_date = (datetime.now() - timedelta(days=day)).date()
            value_achieved = random.uniform(0.6, 1.2) * (8 if challenge_type == 'water' else 7 if challenge_type == 'sleep' else 30)
            
            cursor.execute("""
                INSERT OR IGNORE INTO challenge_progress 
                (user_challenge_id, date, value_achieved, target_met, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (user_challenge_id, progress_date, round(value_achieved, 1), 
                  1 if value_achieved >= (8 if challenge_type == 'water' else 7 if challenge_type == 'sleep' else 30) else 0,
                  f"Daily {challenge_type} tracking"))
    
    # Update user points
    cursor.execute("""
        INSERT OR REPLACE INTO user_points 
        (user_id, total_points, challenges_completed, current_streak, longest_streak, last_activity_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, random.randint(500, 1200), random.randint(2, 5), random.randint(3, 12), 
          random.randint(5, 20), date.today()))
    
    conn.commit()
    conn.close()
    
    print("✅ Comprehensive demo user created successfully!")
    
    # Show summary
    show_demo_summary()

def show_demo_summary():
    """Show summary of created demo data"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("\n📊 Demo User Data Summary")
    print("=" * 50)
    
    # Count records
    tables_to_check = [
        ('mood_logs', 'Mood Entries'),
        ('user_activity_history', 'Activity Records'),
        ('health_activities', 'Health Data Points'),
        ('chat_messages', 'Chat Messages'),
        ('analytics_events', 'Analytics Events'),
        ('suggestion_history', 'Suggestion Interactions'),
        ('user_challenges', 'Active Challenges'),
        ('challenge_progress', 'Challenge Progress Entries')
    ]
    
    for table, description in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = 1 OR user_id = '1'")
        count = cursor.fetchone()[0]
        print(f"  📋 {description}: {count} records")
    
    # Show behavior metrics
    cursor.execute("SELECT * FROM user_behavior_metrics WHERE user_id = '1'")
    metrics = cursor.fetchone()
    if metrics:
        print(f"\n📈 Behavior Metrics:")
        print(f"  💤 Average Sleep: {metrics[1]} hours")
        print(f"  💧 Average Water: {metrics[2]} glasses")
        print(f"  🏃 Average Exercise: {metrics[3]} minutes")
        print(f"  🎯 Suggestion Acceptance: {metrics[6]}%")
    
    # Show recent activities
    cursor.execute("""
        SELECT activity_name, timestamp FROM user_activity_history 
        WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 5
    """)
    recent_activities = cursor.fetchall()
    print(f"\n🏃 Recent Activities:")
    for activity, timestamp in recent_activities:
        print(f"  • {activity} - {timestamp}")
    
    conn.close()
    
    print(f"\n🔑 Login Credentials:")
    print(f"   Username: demo")
    print(f"   Password: demo123")
    print(f"\n🎉 Demo user is ready for comprehensive testing!")

if __name__ == '__main__':
    print("🚀 Creating Comprehensive Demo User")
    print("=" * 50)
    
    create_demo_user()