#!/usr/bin/env python3
"""
Create a demo user with 15 days of comprehensive activity data.

This script creates realistic data to test:
- Activity workflows (water, sleep, exercise, mood)
- Challenge system
- Suggestion system
- Insight generation
- Pattern detection
- Streak tracking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from datetime import datetime, timedelta, date
import random
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    from app.core.database import get_db
    return get_db()

def create_demo_user():
    """Create a demo user"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Temporarily disable foreign keys for cleanup
        cursor.execute('PRAGMA foreign_keys = OFF')
        
        # First ensure users table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Clean up any existing data for demo user from all tables
        tables_to_clean = [
            'activities', 'health_activities', 'chat_messages', 'chat_sessions',
            'user_challenges', 'user_insights', 'user_streaks', 'mood_logs',
            'action_suggestions', 'user_activity_history', 'analytics_events',
            'user_behavior_metrics', 'suggestion_history'
        ]
        
        for table in tables_to_clean:
            try:
                cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (9999,))
            except sqlite3.OperationalError:
                # Table doesn't exist, skip
                pass
        
        # Delete user by email too
        cursor.execute('DELETE FROM users WHERE id = ?', (9999,))
        cursor.execute('DELETE FROM users WHERE username = ?', ('demo_user',))
        cursor.execute('DELETE FROM users WHERE email = ?', ('demo_user_9999@example.com',))
        
        # Re-enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Create demo user with unique email
        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            9999,  # Fixed user ID for demo
            'demo_user_9999',
            'demo_user_9999@example.com',
            'demo_password_hash',
            'Demo User 9999',
            datetime.now().isoformat()
        ))
        
        logger.info("Created demo user (ID: 9999)")
        return 9999

def generate_realistic_activities(user_id, days_back=15):
    """Generate realistic activity data for the past N days"""
    
    activities_data = []
    today = date.today()
    
    # Define realistic patterns for each activity
    water_patterns = [6, 7, 8, 5, 9, 6, 7, 8, 4, 6, 7, 8, 9, 5, 6]  # glasses per day
    sleep_patterns = [7.5, 8, 6.5, 7, 8.5, 6, 7.5, 8, 7, 6.5, 8, 7.5, 6, 8.5, 7]  # hours per day
    exercise_patterns = [30, 45, 0, 60, 30, 0, 45, 30, 60, 0, 45, 30, 0, 60, 45]  # minutes per day
    mood_patterns = ['😊', '😐', '😟', '😊', '😊', '😐', '😊', '😟', '😊', '😐', '😊', '😊', '😐', '😟', '😊']
    
    for i in range(days_back):
        activity_date = today - timedelta(days=days_back - i)
        
        # Water activities (multiple entries per day)
        water_glasses = water_patterns[i]
        water_times = [
            (8, 0),   # Morning
            (12, 30), # Lunch
            (15, 0),  # Afternoon
            (18, 30), # Evening
            (20, 0),  # Night
        ]
        
        glasses_per_session = [2, 1, 2, 2, 1] if water_glasses >= 8 else [1, 1, 1, 1, 1]
        
        for j, (hour, minute) in enumerate(water_times[:len(glasses_per_session)]):
            if sum(glasses_per_session[:j+1]) <= water_glasses:
                timestamp = datetime.combine(activity_date, datetime.min.time().replace(hour=hour, minute=minute))
                activities_data.append({
                    'user_id': user_id,
                    'activity_type': 'water',
                    'value': glasses_per_session[j],
                    'unit': 'glasses',
                    'timestamp': timestamp,
                    'notes': f'Daily hydration - session {j+1}'
                })
        
        # Sleep activity (one entry per day)
        sleep_hours = sleep_patterns[i]
        sleep_time = datetime.combine(activity_date, datetime.min.time().replace(hour=23, minute=30))
        activities_data.append({
            'user_id': user_id,
            'activity_type': 'sleep',
            'value': sleep_hours,
            'unit': 'hours',
            'timestamp': sleep_time,
            'notes': f'Night sleep - {sleep_hours} hours'
        })
        
        # Exercise activity (if > 0)
        exercise_minutes = exercise_patterns[i]
        if exercise_minutes > 0:
            exercise_time = datetime.combine(activity_date, datetime.min.time().replace(hour=17, minute=0))
            exercise_types = ['Running', 'Gym workout', 'Yoga', 'Walking', 'Cycling']
            activities_data.append({
                'user_id': user_id,
                'activity_type': 'exercise',
                'value': exercise_minutes,
                'unit': 'minutes',
                'timestamp': exercise_time,
                'notes': f'{random.choice(exercise_types)} - {exercise_minutes} minutes'
            })
        
        # Mood activity (one entry per day)
        mood_emoji = mood_patterns[i]
        mood_time = datetime.combine(activity_date, datetime.min.time().replace(hour=19, minute=0))
        mood_reasons = {
            '😊': ['Had a great day', 'Accomplished my goals', 'Spent time with friends', 'Feeling energetic'],
            '😐': ['Normal day', 'Nothing special', 'Feeling okay', 'Routine day'],
            '😟': ['Stressful day', 'Feeling tired', 'Work pressure', 'Didn\'t sleep well']
        }
        activities_data.append({
            'user_id': user_id,
            'activity_type': 'mood',
            'value': 1,  # Mood is just a flag
            'unit': 'entry',
            'timestamp': mood_time,
            'notes': f'{mood_emoji} - {random.choice(mood_reasons[mood_emoji])}'
        })
    
    return activities_data

def insert_activities(activities_data):
    """Insert activity data into database"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Ensure activities table exists (using health_activities from init_db.py)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                value REAL,
                unit TEXT,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Clear existing data for demo user
        cursor.execute('DELETE FROM activities WHERE user_id = ?', (9999,))
        
        # Insert new activities
        for activity in activities_data:
            cursor.execute('''
                INSERT INTO activities (user_id, activity_type, value, unit, timestamp, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                activity['user_id'],
                activity['activity_type'],
                activity['value'],
                activity['unit'],
                activity['timestamp'].isoformat(),
                activity['notes']
            ))
        
        logger.info(f"Inserted {len(activities_data)} activities for demo user")

def create_chat_history(user_id):
    """Create realistic chat history"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Ensure chat tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_end DATETIME,
                messages_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id INTEGER,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
        ''')
        
        # Clear existing chat data for demo user
        cursor.execute('DELETE FROM chat_messages WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (user_id,))
        
        # Create a few chat sessions with realistic conversations
        today = datetime.now()
        
        chat_conversations = [
            # 3 days ago - Initial interaction
            {
                'date': today - timedelta(days=3),
                'messages': [
                    ('user', 'Hello, I want to start tracking my wellness'),
                    ('bot', 'Welcome! I\'m here to help you track your wellness journey. You can log activities like water intake, sleep, exercise, and mood. What would you like to start with?'),
                    ('user', 'log water'),
                    ('bot', 'Great! How many glasses of water did you drink?'),
                    ('user', '3 glasses'),
                    ('bot', 'Excellent! I\'ve logged 3 glasses of water for you. Staying hydrated is important for your health. 💧'),
                ]
            },
            # 2 days ago - Challenge interaction
            {
                'date': today - timedelta(days=2),
                'messages': [
                    ('user', 'How am I doing with my goals?'),
                    ('bot', 'You\'re doing great! You\'ve been consistent with water logging. I notice you\'ve logged water for 2 days in a row - that\'s a good start for building a habit!'),
                    ('user', 'What challenges do you have?'),
                    ('bot', 'I can help you with hydration challenges! Try to drink 8 glasses of water daily for a week. Would you like me to track this for you?'),
                    ('user', 'yes'),
                    ('bot', 'Perfect! I\'ve set up a hydration challenge for you. Keep logging your water intake and I\'ll track your progress.'),
                ]
            },
            # 1 day ago - Mood and suggestions
            {
                'date': today - timedelta(days=1),
                'messages': [
                    ('user', 'I\'m feeling stressed 😟'),
                    ('bot', 'I\'m sorry to hear you\'re feeling stressed. Here are some activities that might help: deep breathing exercises, a short walk, or some light stretching. Would you like specific suggestions?'),
                    ('user', 'suggest activities for stress'),
                    ('bot', 'Here are some stress-relief activities I recommend: 1) 5-minute meditation, 2) Take a walk outside, 3) Practice deep breathing, 4) Listen to calming music. Which one sounds good to you?'),
                    ('user', 'I\'ll try meditation'),
                    ('bot', 'That\'s a great choice! Meditation can be very effective for stress relief. Even 5 minutes can make a difference. Let me know how it goes!'),
                ]
            }
        ]
        
        session_id = 9001  # Start with a high number to avoid conflicts
        for conversation in chat_conversations:
            # Create session (let database auto-generate ID)
            cursor.execute('''
                INSERT INTO chat_sessions (user_id, session_start)
                VALUES (?, ?)
            ''', (user_id, conversation['date'].isoformat()))
            
            # Get the generated session ID
            actual_session_id = cursor.lastrowid
            
            # Add messages
            for i, (sender, message) in enumerate(conversation['messages']):
                message_time = conversation['date'] + timedelta(minutes=i*2)
                cursor.execute('''
                    INSERT INTO chat_messages (user_id, session_id, sender, message, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, actual_session_id, sender, message, message_time.isoformat()))
            
            session_id += 1
        
        logger.info(f"Created chat history with {len(chat_conversations)} conversations")

def create_challenge_data(user_id):
    """Create challenge data"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Ensure challenges tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                target_value REAL,
                target_unit TEXT,
                duration_days INTEGER,
                points_reward INTEGER DEFAULT 10,
                difficulty TEXT DEFAULT 'medium',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_id INTEGER NOT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0,
                days_completed INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (challenge_id) REFERENCES challenges(id),
                UNIQUE(user_id, challenge_id)
            )
        ''')
        
        # Clear existing challenges for demo user
        cursor.execute('DELETE FROM user_challenges WHERE user_id = ?', (user_id,))
        
        # Create some master challenges first
        today = date.today()
        master_challenges = [
            {
                'title': 'Daily Hydration Challenge',
                'description': 'Drink 8 glasses of water daily for 7 days',
                'challenge_type': 'water',
                'target_value': 8,
                'target_unit': 'glasses',
                'duration_days': 7,
                'points': 50,
                'start_date': today - timedelta(days=10),
                'end_date': today + timedelta(days=4)
            },
            {
                'title': 'Weekly Exercise Goal',
                'description': 'Exercise for 150 minutes per week',
                'challenge_type': 'exercise',
                'target_value': 150,
                'target_unit': 'minutes',
                'duration_days': 7,
                'points': 75,
                'start_date': today - timedelta(days=7),
                'end_date': today + timedelta(days=7)
            },
            {
                'title': 'Sleep Consistency Challenge',
                'description': 'Get 7+ hours of sleep for 14 days',
                'challenge_type': 'sleep',
                'target_value': 7,
                'target_unit': 'hours',
                'duration_days': 14,
                'points': 100,
                'start_date': today - timedelta(days=14),
                'end_date': today + timedelta(days=1)
            }
        ]
        
        challenge_ids = []
        for challenge in master_challenges:
            cursor.execute('''
                INSERT OR IGNORE INTO challenges 
                (title, description, challenge_type, target_value, target_unit, duration_days, points, start_date, end_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                challenge['title'],
                challenge['description'],
                challenge['challenge_type'],
                challenge['target_value'],
                challenge['target_unit'],
                challenge['duration_days'],
                challenge['points'],
                challenge['start_date'].isoformat(),
                challenge['end_date'].isoformat(),
                user_id  # Demo user created the challenges
            ))
            
            # Get the challenge ID
            cursor.execute('SELECT id FROM challenges WHERE title = ?', (challenge['title'],))
            result = cursor.fetchone()
            if result:
                challenge_ids.append(result[0])
        
        # Now create user participation in these challenges
        user_challenge_data = [
            {
                'challenge_id': challenge_ids[0] if len(challenge_ids) > 0 else 1,  # Hydration
                'joined_at': today - timedelta(days=10),
                'status': 'active',
                'progress': 65.0,  # 65% complete
                'days_completed': 4,
                'points_earned': 20
            },
            {
                'challenge_id': challenge_ids[1] if len(challenge_ids) > 1 else 2,  # Exercise
                'joined_at': today - timedelta(days=7),
                'status': 'active',
                'progress': 80.0,  # 80% complete
                'days_completed': 5,
                'points_earned': 40
            },
            {
                'challenge_id': challenge_ids[2] if len(challenge_ids) > 2 else 3,  # Sleep
                'joined_at': today - timedelta(days=14),
                'status': 'active',
                'progress': 92.0,  # Almost complete!
                'days_completed': 13,
                'points_earned': 85
            }
        ]
        
        for uc_data in user_challenge_data:
            cursor.execute('''
                INSERT INTO user_challenges 
                (user_id, challenge_id, joined_at, status, progress, days_completed, points_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                uc_data['challenge_id'],
                uc_data['joined_at'].isoformat(),
                uc_data['status'],
                uc_data['progress'],
                uc_data['days_completed'],
                uc_data['points_earned']
            ))
        
        logger.info(f"Created {len(user_challenge_data)} user challenges for demo user")

def create_insight_data(user_id):
    """Create insight and pattern data"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Create insights table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                insight_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                confidence REAL DEFAULT 0.8,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                shown_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Clear existing insights for demo user
        cursor.execute('DELETE FROM user_insights WHERE user_id = ?', (user_id,))
        
        # Create some insights
        today = datetime.now()
        insights = [
            {
                'insight_type': 'pattern_detection',
                'title': 'Hydration Pattern Detected',
                'message': 'I noticed you drink more water on weekdays than weekends. Your average is 7.2 glasses on weekdays vs 5.8 on weekends.',
                'data': json.dumps({
                    'pattern': 'weekday_vs_weekend',
                    'activity': 'water',
                    'weekday_avg': 7.2,
                    'weekend_avg': 5.8
                }),
                'confidence': 0.85,
                'created_at': today - timedelta(days=2)
            },
            {
                'insight_type': 'streak_achievement',
                'title': 'Sleep Consistency Streak!',
                'message': 'Great job! You\'ve maintained 7+ hours of sleep for 5 days in a row. Consistent sleep is key to good health.',
                'data': json.dumps({
                    'activity': 'sleep',
                    'streak_days': 5,
                    'target_hours': 7
                }),
                'confidence': 1.0,
                'created_at': today - timedelta(days=1)
            },
            {
                'insight_type': 'mood_correlation',
                'title': 'Exercise & Mood Connection',
                'message': 'I noticed you tend to feel happier on days when you exercise. Your mood is 40% more positive on exercise days!',
                'data': json.dumps({
                    'correlation': 'exercise_mood',
                    'improvement': 0.4,
                    'sample_size': 8
                }),
                'confidence': 0.75,
                'created_at': today - timedelta(hours=12)
            }
        ]
        
        for insight in insights:
            cursor.execute('''
                INSERT INTO user_insights 
                (user_id, insight_type, title, message, data, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                insight['insight_type'],
                insight['title'],
                insight['message'],
                insight['data'],
                insight['confidence'],
                insight['created_at'].isoformat()
            ))
        
        logger.info(f"Created {len(insights)} insights for demo user")

def create_streak_data(user_id):
    """Create streak tracking data"""
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Create streaks table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, activity_type)
            )
        ''')
        
        # Clear existing streaks for demo user
        cursor.execute('DELETE FROM user_streaks WHERE user_id = ?', (user_id,))
        
        # Create streak data based on activity patterns
        today = date.today()
        streaks = [
            {
                'activity_type': 'water',
                'current_streak': 12,  # 12 days in a row
                'longest_streak': 15,
                'last_activity_date': today - timedelta(days=1)
            },
            {
                'activity_type': 'sleep',
                'current_streak': 15,  # Perfect streak
                'longest_streak': 15,
                'last_activity_date': today - timedelta(days=1)
            },
            {
                'activity_type': 'exercise',
                'current_streak': 0,  # Broken yesterday
                'longest_streak': 4,
                'last_activity_date': today - timedelta(days=2)
            },
            {
                'activity_type': 'mood',
                'current_streak': 8,
                'longest_streak': 10,
                'last_activity_date': today - timedelta(days=1)
            }
        ]
        
        for streak in streaks:
            cursor.execute('''
                INSERT INTO user_streaks 
                (user_id, activity_type, current_streak, longest_streak, last_activity_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                streak['activity_type'],
                streak['current_streak'],
                streak['longest_streak'],
                streak['last_activity_date'].isoformat()
            ))
        
        logger.info(f"Created {len(streaks)} streak records for demo user")

def main():
    """Create comprehensive demo user data"""
    print("CREATING COMPREHENSIVE DEMO USER DATA")
    print("=" * 50)
    
    try:
        # Step 1: Create demo user
        print("\n1. Creating demo user...")
        user_id = create_demo_user()
        
        # Step 2: Generate and insert activity data
        print("\n2. Generating 15 days of activity data...")
        activities = generate_realistic_activities(user_id, days_back=15)
        insert_activities(activities)
        
        # Step 3: Create chat history
        print("\n3. Creating chat conversation history...")
        create_chat_history(user_id)
        
        # Step 4: Create challenge data
        print("\n4. Creating challenge data...")
        create_challenge_data(user_id)
        
        # Step 5: Create insight data
        print("\n5. Creating insight and pattern data...")
        create_insight_data(user_id)
        
        # Step 6: Create streak data
        print("\n6. Creating streak tracking data...")
        create_streak_data(user_id)
        
        print(f"\n{'='*50}")
        print("✅ DEMO USER CREATED SUCCESSFULLY!")
        print(f"{'='*50}")
        print(f"User ID: {user_id}")
        print(f"Username: demo_user")
        print(f"Email: demo@example.com")
        print(f"Password: demo_password_hash")
        print(f"\n📊 DATA SUMMARY:")
        print(f"- 15 days of activity data (water, sleep, exercise, mood)")
        print(f"- {len(activities)} total activity entries")
        print(f"- 3 realistic chat conversations")
        print(f"- 3 active challenges (water, exercise, sleep)")
        print(f"- 3 generated insights (patterns, streaks, correlations)")
        print(f"- Streak data for all activity types")
        print(f"\n🎯 WHAT YOU CAN TEST:")
        print(f"- Activity logging workflows")
        print(f"- Follow-up conversations ('add 1 more')")
        print(f"- Challenge progress queries")
        print(f"- Activity summary requests")
        print(f"- Suggestion system")
        print(f"- Insight generation")
        print(f"- Pattern detection")
        print(f"- Streak tracking")
        print(f"\n💡 LOGIN WITH:")
        print(f"- User ID: 9999")
        print(f"- Or create login endpoint for demo_user")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        logger.error(f"Demo user creation failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()