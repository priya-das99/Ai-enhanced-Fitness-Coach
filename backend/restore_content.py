#!/usr/bin/env python3
"""
Restore Essential Content and Sample Data
Populates the database with meaningful content for demonstration
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

def get_db_path():
    """Get database path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, 'mood_capture.db')

def populate_wellness_content():
    """Add comprehensive wellness content"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🌿 Adding wellness content...")
    
    # Sample content items for each category
    content_items = [
        # Yoga content
        (1, "Morning Sun Salutation", "Energizing 10-minute morning yoga routine", "video", "https://example.com/yoga1", None, 10, "beginner", "morning,energy,flexibility", 1),
        (1, "Evening Relaxation Yoga", "Calming yoga sequence for better sleep", "video", "https://example.com/yoga2", None, 15, "beginner", "evening,relaxation,sleep", 1),
        (1, "Desk Yoga Stretches", "Quick yoga moves you can do at your desk", "article", "https://example.com/yoga3", None, 5, "beginner", "office,stretching,quick", 0),
        
        # Mindfulness content
        (2, "5-Minute Breathing Exercise", "Simple breathing technique for instant calm", "audio", "https://example.com/breath1", None, 5, "beginner", "breathing,calm,stress", 1),
        (2, "Body Scan Meditation", "Progressive relaxation meditation", "audio", "https://example.com/meditation1", None, 20, "intermediate", "meditation,relaxation,mindfulness", 0),
        (2, "Mindful Walking Guide", "How to practice mindfulness while walking", "article", "https://example.com/walk1", None, 15, "beginner", "walking,mindfulness,outdoor", 0),
        
        # Exercise content
        (3, "7-Minute HIIT Workout", "High-intensity interval training routine", "video", "https://example.com/hiit1", None, 7, "intermediate", "hiit,cardio,strength", 1),
        (3, "Beginner Strength Training", "Introduction to weight training", "video", "https://example.com/strength1", None, 30, "beginner", "strength,weights,muscle", 0),
        (3, "Cardio Dance Workout", "Fun dance routine for cardio fitness", "video", "https://example.com/dance1", None, 25, "beginner", "dance,cardio,fun", 0),
        
        # Healthy Eating content
        (4, "Meal Prep Basics", "How to prepare healthy meals for the week", "article", "https://example.com/meal1", None, 60, "beginner", "meal-prep,nutrition,planning", 1),
        (4, "Healthy Smoothie Recipes", "Nutritious smoothie ideas for any time", "article", "https://example.com/smoothie1", None, 10, "beginner", "smoothies,nutrition,recipes", 0),
        (4, "Mindful Eating Practice", "How to eat more mindfully and enjoy food", "article", "https://example.com/mindful-eat1", None, 20, "beginner", "mindful-eating,awareness,health", 0),
        
        # Smoking Cessation content
        (5, "Quit Smoking Timeline", "What happens when you quit smoking", "article", "https://example.com/quit1", None, 15, "beginner", "quit-smoking,timeline,health", 1),
        (5, "Coping with Cravings", "Strategies to manage smoking cravings", "article", "https://example.com/cravings1", None, 10, "beginner", "cravings,strategies,support", 0),
        (5, "Breathing Exercises for Ex-Smokers", "Lung health improvement exercises", "video", "https://example.com/lung1", None, 12, "beginner", "breathing,lungs,recovery", 0),
    ]
    
    for item in content_items:
        cursor.execute("""
            INSERT OR IGNORE INTO content_items 
            (category_id, title, description, content_type, content_url, thumbnail_url, 
             duration_minutes, difficulty_level, tags, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)
    
    conn.commit()
    conn.close()
    print(f"✅ Added {len(content_items)} content items")

def create_sample_challenges():
    """Create sample wellness challenges"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("🎯 Creating sample challenges...")
    
    # Get demo user ID
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    demo_user = cursor.fetchone()
    if not demo_user:
        print("❌ Demo user not found")
        conn.close()
        return
    
    demo_user_id = demo_user[0]
    
    # Sample challenges
    challenges = [
        ("7-Day Hydration Challenge", "Drink 8 glasses of water daily for a week", "water", 8.0, "glasses", 7, 100, "2024-03-01", "2024-03-07", demo_user_id, 1),
        ("30-Day Step Challenge", "Walk 10,000 steps every day for a month", "steps", 10000.0, "steps", 30, 300, "2024-03-01", "2024-03-30", demo_user_id, 1),
        ("Sleep Better Challenge", "Get 7+ hours of sleep for 14 days", "sleep", 7.0, "hours", 14, 200, "2024-03-01", "2024-03-14", demo_user_id, 1),
        ("Mindfulness Week", "Practice 10 minutes of meditation daily", "meditation", 10.0, "minutes", 7, 150, "2024-03-01", "2024-03-07", demo_user_id, 1),
        ("Active Lifestyle Challenge", "Exercise for 30 minutes, 5 days a week", "exercise", 30.0, "minutes", 21, 250, "2024-03-01", "2024-03-21", demo_user_id, 1),
    ]
    
    for challenge in challenges:
        cursor.execute("""
            INSERT OR IGNORE INTO challenges 
            (title, description, challenge_type, target_value, target_unit, duration_days, 
             points, start_date, end_date, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, challenge)
    
    conn.commit()
    conn.close()
    print(f"✅ Created {len(challenges)} sample challenges")

def add_sample_user_data():
    """Add sample user activity and mood data"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("📊 Adding sample user data...")
    
    # Get demo user ID
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    demo_user = cursor.fetchone()
    if not demo_user:
        print("❌ Demo user not found")
        conn.close()
        return
    
    demo_user_id = demo_user[0]
    
    # Sample mood logs (last 7 days)
    moods = [
        (demo_user_id, "happy", "😊", "Had a great workout this morning", "exercise", "2024-03-01 09:00:00"),
        (demo_user_id, "stressed", "😰", "Busy day at work", "work", "2024-03-01 15:30:00"),
        (demo_user_id, "calm", "😌", "Enjoyed meditation session", "mindfulness", "2024-03-02 07:00:00"),
        (demo_user_id, "energetic", "⚡", "Good night's sleep", "sleep", "2024-03-02 08:00:00"),
        (demo_user_id, "tired", "😴", "Long day, need rest", "fatigue", "2024-03-02 20:00:00"),
        (demo_user_id, "motivated", "💪", "Ready for new challenges", "goals", "2024-03-03 06:30:00"),
    ]
    
    for mood in moods:
        cursor.execute("""
            INSERT OR IGNORE INTO mood_logs 
            (user_id, mood, mood_emoji, reason, reason_category, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mood)
    
    # Sample activity history
    activities = [
        (demo_user_id, "morning_yoga", "Morning Yoga Session", "😊", "Feeling energized", 1, 20, "2024-03-01 07:00:00", "Friday", "morning"),
        (demo_user_id, "water_intake", "Drank Water", "💧", "Staying hydrated", 1, 1, "2024-03-01 09:00:00", "Friday", "morning"),
        (demo_user_id, "meditation", "Meditation", "😌", "Stress relief", 1, 10, "2024-03-01 18:00:00", "Friday", "evening"),
        (demo_user_id, "walking", "Evening Walk", "🚶", "Fresh air and movement", 1, 30, "2024-03-02 19:00:00", "Saturday", "evening"),
        (demo_user_id, "stretching", "Desk Stretches", "🤸", "Relief from sitting", 1, 5, "2024-03-03 14:00:00", "Sunday", "afternoon"),
    ]
    
    for activity in activities:
        cursor.execute("""
            INSERT OR IGNORE INTO user_activity_history 
            (user_id, activity_id, activity_name, mood_emoji, reason, completed, 
             duration_minutes, timestamp, day_of_week, time_of_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, activity)
    
    # Sample health activities
    health_data = [
        (demo_user_id, "water", 8.0, "glasses", "Met daily goal", "2024-03-01 23:59:00"),
        (demo_user_id, "sleep", 7.5, "hours", "Good quality sleep", "2024-03-02 07:00:00"),
        (demo_user_id, "weight", 70.5, "kg", "Weekly weigh-in", "2024-03-02 08:00:00"),
        (demo_user_id, "water", 6.0, "glasses", "Need to drink more", "2024-03-02 23:59:00"),
        (demo_user_id, "exercise", 45.0, "minutes", "Yoga + walking", "2024-03-02 20:00:00"),
    ]
    
    for health in health_data:
        cursor.execute("""
            INSERT OR IGNORE INTO health_activities 
            (user_id, activity_type, value, unit, notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, health)
    
    # Sample chat messages
    chat_messages = [
        (demo_user_id, "Hi! I'm feeling a bit stressed today.", "user", "2024-03-01 15:30:00", None),
        (demo_user_id, "I understand you're feeling stressed. That's completely normal, especially during busy days. Would you like me to suggest some quick stress-relief activities?", "bot", "2024-03-01 15:30:30", '{"suggestions": ["breathing", "short_walk", "meditation"]}'),
        (demo_user_id, "Yes, that would be helpful!", "user", "2024-03-01 15:31:00", None),
        (demo_user_id, "Great! Here are some quick options: 1) 5-minute breathing exercise 2) Short walk around the block 3) Brief meditation session. Which one appeals to you most?", "bot", "2024-03-01 15:31:15", '{"workflow": "stress_relief"}'),
        (demo_user_id, "I'll try the breathing exercise", "user", "2024-03-01 15:32:00", None),
        (demo_user_id, "Excellent choice! Take 5 deep breaths: inhale for 4 counts, hold for 4, exhale for 6. Focus on releasing tension with each exhale. How do you feel after trying this?", "bot", "2024-03-01 15:32:30", '{"activity": "breathing", "completed": true}'),
    ]
    
    for msg in chat_messages:
        cursor.execute("""
            INSERT OR IGNORE INTO chat_messages 
            (user_id, message, sender, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, msg)
    
    conn.commit()
    conn.close()
    print("✅ Added sample user data (moods, activities, health data, chat history)")

def update_behavior_metrics():
    """Calculate and update user behavior metrics"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("📈 Updating behavior metrics...")
    
    # Get demo user ID
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    demo_user = cursor.fetchone()
    if not demo_user:
        conn.close()
        return
    
    demo_user_id = str(demo_user[0])
    
    # Calculate metrics based on sample data
    metrics = {
        'user_id': demo_user_id,
        'avg_sleep_7d': 7.5,
        'avg_water_7d': 7.0,
        'avg_exercise_7d': 25.0,
        'hydration_score': 85.0,
        'stress_score': 65.0,
        'suggestion_acceptance_rate': 80.0,
        'total_suggestions_shown': 10,
        'total_suggestions_accepted': 8,
        'last_updated': datetime.now().isoformat()
    }
    
    cursor.execute("""
        INSERT OR REPLACE INTO user_behavior_metrics 
        (user_id, avg_sleep_7d, avg_water_7d, avg_exercise_7d, hydration_score, 
         stress_score, suggestion_acceptance_rate, total_suggestions_shown, 
         total_suggestions_accepted, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics['user_id'], metrics['avg_sleep_7d'], metrics['avg_water_7d'],
        metrics['avg_exercise_7d'], metrics['hydration_score'], metrics['stress_score'],
        metrics['suggestion_acceptance_rate'], metrics['total_suggestions_shown'],
        metrics['total_suggestions_accepted'], metrics['last_updated']
    ))
    
    conn.commit()
    conn.close()
    print("✅ Updated behavior metrics")

def show_content_summary():
    """Show summary of restored content"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    print("\n📊 Content Restoration Summary")
    print("=" * 50)
    
    # Count content by table
    tables_to_check = [
        ('content_items', 'Wellness Content'),
        ('challenges', 'Sample Challenges'),
        ('mood_logs', 'Mood Entries'),
        ('user_activity_history', 'Activity Records'),
        ('health_activities', 'Health Data'),
        ('chat_messages', 'Chat Messages'),
        ('user_behavior_metrics', 'Behavior Metrics')
    ]
    
    for table, description in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  📋 {description}: {count} records")
    
    conn.close()

def main():
    """Restore all essential content"""
    print("🔄 Restoring Essential Content & Sample Data")
    print("=" * 50)
    
    populate_wellness_content()
    create_sample_challenges()
    add_sample_user_data()
    update_behavior_metrics()
    
    show_content_summary()
    
    print("\n🎉 Content restoration completed!")
    print("\n🔑 Demo Account Ready:")
    print("   Username: demo")
    print("   Password: demo123")
    print("\n📱 Your app now has:")
    print("   ✅ Comprehensive wellness content")
    print("   ✅ Sample challenges to try")
    print("   ✅ Realistic user data for testing")
    print("   ✅ Chat conversation history")
    print("   ✅ Analytics and behavior metrics")

if __name__ == '__main__':
    main()