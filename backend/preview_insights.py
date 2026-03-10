#!/usr/bin/env python3
"""
Preview AI Insights
Show exactly what insights the demo user will see
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
import json

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def get_db_path():
    """Get database path"""
    return os.path.join(backend_dir, 'mood_capture.db')

def generate_insights():
    """Generate and display actual insights for demo user"""
    print("🤖 AI INSIGHTS FOR DEMO USER")
    print("=" * 60)
    
    try:
        from app.services.insight_system import InsightSystem
        from app.services.pattern_detector import PatternDetector
        from app.services.user_data_analyzer import UserDataAnalyzer
        
        insight_system = InsightSystem()
        pattern_detector = PatternDetector()
        data_analyzer = UserDataAnalyzer()
        
        user_id = 1
        
        # 1. BEHAVIORAL PATTERNS
        print("📊 BEHAVIORAL PATTERN ANALYSIS:")
        patterns = pattern_detector.detect_patterns(user_id)
        
        if patterns:
            for pattern in patterns:
                print(f"  🔍 {pattern.get('type', 'Pattern').title()}: {pattern.get('description', 'N/A')}")
                if pattern.get('confidence'):
                    print(f"      Confidence: {pattern['confidence']}%")
                if pattern.get('recommendation'):
                    print(f"      💡 Suggestion: {pattern['recommendation']}")
        else:
            print("  📈 Analyzing your activity patterns...")
            print("  💤 Sleep Quality: You average 7.5 hours - great consistency!")
            print("  💧 Hydration: 8 glasses/day - excellent hydration habits")
            print("  🏃 Exercise: 55 min/day - very active lifestyle")
            print("  😊 Mood Trends: Positive correlation between exercise and mood")
        
        # 2. PERSONALIZED INSIGHTS
        print(f"\n🎯 PERSONALIZED INSIGHTS:")
        
        # Get greeting insight (what user sees on login)
        greeting_insight = insight_system.get_greeting_insight(user_id)
        if greeting_insight:
            print(f"  🌅 Morning Insight: {greeting_insight.get('message', 'Welcome back!')}")
            if greeting_insight.get('pattern'):
                print(f"      Based on: {greeting_insight['pattern']}")
        
        # Get activity insights
        activity_insights = insight_system.get_activity_insights(user_id)
        if activity_insights:
            for insight in activity_insights[:3]:  # Show top 3
                print(f"  💪 Activity Insight: {insight.get('message', 'Keep up the great work!')}")
        
        # 3. HEALTH TREND ANALYSIS
        print(f"\n📈 HEALTH TREND ANALYSIS:")
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Sleep trends
        cursor.execute("""
            SELECT AVG(value) as avg_sleep, COUNT(*) as days
            FROM health_activities 
            WHERE user_id = 1 AND activity_type = 'sleep' 
            AND timestamp >= date('now', '-7 days')
        """)
        sleep_data = cursor.fetchone()
        if sleep_data[0]:
            avg_sleep = sleep_data[0]
            if avg_sleep >= 7.5:
                print(f"  😴 Sleep Quality: Excellent! {avg_sleep:.1f}h average")
                print(f"      💡 Your consistent sleep schedule is boosting your energy levels")
            elif avg_sleep >= 6.5:
                print(f"  😴 Sleep Quality: Good {avg_sleep:.1f}h average")
                print(f"      💡 Try to get closer to 8 hours for optimal recovery")
            else:
                print(f"  😴 Sleep Quality: Needs improvement {avg_sleep:.1f}h average")
                print(f"      💡 Consider a bedtime routine to improve sleep quality")
        
        # Exercise patterns
        cursor.execute("""
            SELECT activity_name, COUNT(*) as frequency, AVG(duration_minutes) as avg_duration
            FROM user_activity_history 
            WHERE user_id = 1 AND timestamp >= date('now', '-7 days')
            GROUP BY activity_name ORDER BY frequency DESC LIMIT 3
        """)
        top_activities = cursor.fetchall()
        if top_activities:
            print(f"  🏃 Exercise Patterns:")
            for activity, freq, avg_dur in top_activities:
                print(f"      • {activity}: {freq}x this week ({avg_dur:.0f} min avg)")
            
            # Generate insight based on patterns
            most_frequent = top_activities[0][0]
            if 'yoga' in most_frequent.lower():
                print(f"      💡 Great focus on flexibility! Consider adding cardio for balance")
            elif 'running' in most_frequent.lower():
                print(f"      💡 Excellent cardio! Add strength training for muscle balance")
            elif 'strength' in most_frequent.lower():
                print(f"      💡 Strong focus on strength! Add flexibility work for recovery")
        
        # Mood-Activity Correlation
        cursor.execute("""
            SELECT m.mood_emoji, m.mood, COUNT(*) as frequency
            FROM mood_logs m
            WHERE m.user_id = 1 AND m.timestamp >= date('now', '-7 days')
            GROUP BY m.mood_emoji, m.mood ORDER BY frequency DESC LIMIT 3
        """)
        mood_patterns = cursor.fetchall()
        if mood_patterns:
            print(f"  😊 Mood Insights:")
            dominant_mood = mood_patterns[0]
            print(f"      • Most frequent mood: {dominant_mood[0]} {dominant_mood[1]} ({dominant_mood[2]} times)")
            
            if dominant_mood[1] in ['happy', 'awesome', 'energetic']:
                print(f"      💡 Your positive mood correlates with regular exercise!")
            elif dominant_mood[1] in ['tired', 'stressed']:
                print(f"      💡 Consider more rest days or stress-reduction activities")
        
        # 4. CHALLENGE INSIGHTS
        print(f"\n🎯 CHALLENGE PROGRESS INSIGHTS:")
        
        cursor.execute("""
            SELECT c.title, c.challenge_type, uc.progress, uc.days_completed, uc.status
            FROM user_challenges uc
            JOIN challenges c ON uc.challenge_id = c.id
            WHERE uc.user_id = 1 AND uc.status = 'active'
        """)
        active_challenges = cursor.fetchall()
        
        for title, challenge_type, progress, days, status in active_challenges:
            if progress >= 80:
                print(f"  🏆 {title}: {progress}% - Almost there! Just a few more days!")
            elif progress >= 50:
                print(f"  💪 {title}: {progress}% - Great momentum! Keep it up!")
            else:
                print(f"  🎯 {title}: {progress}% - You've got this! Small steps daily!")
            
            if challenge_type == 'water' and progress < 70:
                print(f"      💡 Set hourly reminders to drink water")
            elif challenge_type == 'sleep' and progress < 70:
                print(f"      💡 Try a consistent bedtime routine")
            elif challenge_type == 'meditation' and progress < 70:
                print(f"      💡 Start with just 5 minutes daily")
        
        # 5. PREDICTIVE INSIGHTS
        print(f"\n🔮 PREDICTIVE INSIGHTS:")
        
        # Based on patterns, predict what user might need
        cursor.execute("""
            SELECT strftime('%w', timestamp) as day_of_week, COUNT(*) as activity_count
            FROM user_activity_history 
            WHERE user_id = 1 
            GROUP BY day_of_week ORDER BY activity_count DESC
        """)
        activity_by_day = cursor.fetchall()
        
        if activity_by_day:
            most_active_day = activity_by_day[0][0]
            least_active_day = activity_by_day[-1][0]
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            print(f"  📅 You're most active on {days[int(most_active_day)]}s")
            print(f"  📅 Consider scheduling lighter activities on {days[int(least_active_day)]}s")
        
        # Suggest based on recent mood trends
        cursor.execute("""
            SELECT mood, COUNT(*) as frequency
            FROM mood_logs 
            WHERE user_id = 1 AND timestamp >= date('now', '-3 days')
            GROUP BY mood ORDER BY frequency DESC LIMIT 1
        """)
        recent_mood = cursor.fetchone()
        if recent_mood:
            mood = recent_mood[0]
            if mood in ['tired', 'stressed']:
                print(f"  🧘 Recent stress detected - consider meditation or yoga")
            elif mood in ['happy', 'energetic']:
                print(f"  🚀 High energy detected - great time for challenging workouts!")
            elif mood == 'okay':
                print(f"  🌟 Steady mood - perfect for building consistent habits")
        
        # 6. WELLNESS RECOMMENDATIONS
        print(f"\n🌟 PERSONALIZED RECOMMENDATIONS:")
        
        # Based on user's data, generate specific recommendations
        cursor.execute("""
            SELECT AVG(value) as avg_water FROM health_activities 
            WHERE user_id = 1 AND activity_type = 'water' 
            AND timestamp >= date('now', '-7 days')
        """)
        avg_water = cursor.fetchone()[0]
        
        if avg_water and avg_water < 8:
            print(f"  💧 Hydration Goal: Increase water intake by {8 - avg_water:.0f} glasses")
        elif avg_water and avg_water >= 8:
            print(f"  💧 Hydration: Perfect! You're meeting your daily water goals")
        
        # Exercise recommendations
        cursor.execute("""
            SELECT AVG(duration_minutes) as avg_exercise FROM user_activity_history 
            WHERE user_id = 1 AND timestamp >= date('now', '-7 days')
        """)
        avg_exercise = cursor.fetchone()[0]
        
        if avg_exercise and avg_exercise >= 60:
            print(f"  🏃 Exercise: Excellent activity level! Consider active recovery days")
        elif avg_exercise and avg_exercise >= 30:
            print(f"  🏃 Exercise: Good activity level! Try adding 10 more minutes daily")
        else:
            print(f"  🏃 Exercise: Start with 20-minute daily walks to build momentum")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to manual insights based on demo data
        show_manual_insights()

def show_manual_insights():
    """Show manual insights based on demo data"""
    print("\n🤖 SAMPLE AI INSIGHTS (Based on Demo Data):")
    print("=" * 60)
    
    print("📊 BEHAVIORAL PATTERNS:")
    print("  🔍 Exercise Consistency: You work out 6 days/week - excellent routine!")
    print("      💡 Consider adding one rest day for optimal recovery")
    print("  🔍 Sleep Pattern: Consistent 7.5h average - great sleep hygiene!")
    print("      💡 Your sleep quality correlates with better mood next day")
    print("  🔍 Hydration Habit: 8 glasses daily - perfect hydration!")
    print("      💡 Your water intake supports your active lifestyle")
    
    print("\n🎯 PERSONALIZED INSIGHTS:")
    print("  🌅 Morning Insight: Your energy peaks after morning workouts!")
    print("  💪 Activity Insight: Strength training is your most consistent activity")
    print("  😊 Mood Insight: Exercise days show 40% higher positive mood ratings")
    print("  🏃 Performance Insight: Your running pace improves on high-sleep days")
    
    print("\n📈 HEALTH TRENDS:")
    print("  😴 Sleep Quality: Excellent 7.5h average (optimal range)")
    print("  🏃 Exercise Patterns: Strength training 3x/week, cardio 2x/week")
    print("  😊 Mood Trends: 70% positive moods, linked to activity completion")
    print("  💧 Hydration: Consistent 8+ glasses, supporting recovery")
    
    print("\n🎯 CHALLENGE INSIGHTS:")
    print("  🏆 Hydration Challenge: 48% complete - on track for success!")
    print("  💪 Sleep Challenge: 61% complete - consistency is key!")
    print("  🧘 Mindfulness Challenge: 69% complete - almost there!")
    
    print("\n🔮 PREDICTIVE INSIGHTS:")
    print("  📅 You're most active on weekdays - great work-life balance!")
    print("  🧘 Stress levels lower on meditation days - keep it up!")
    print("  🚀 High energy detected - perfect time for challenging goals!")
    
    print("\n🌟 PERSONALIZED RECOMMENDATIONS:")
    print("  💧 Hydration: Perfect! You're exceeding daily water goals")
    print("  🏃 Exercise: Excellent 55min/day average - consider active recovery")
    print("  😴 Sleep: Optimal range - your 7.5h supports peak performance")
    print("  🧘 Stress Management: Add 5 more minutes of daily meditation")
    print("  🎯 Next Goal: Try a 30-day consistency challenge!")

def show_chat_insights():
    """Show what insights appear in chat conversations"""
    print("\n💬 CHAT CONVERSATION INSIGHTS:")
    print("=" * 60)
    
    print("🤖 AI Coach: \"Good morning! I noticed you've been incredibly consistent")
    print("    with your workouts this week - 6 days in a row! 💪\"")
    print()
    print("🤖 AI Coach: \"Your sleep data shows you're averaging 7.5 hours, which")
    print("    correlates perfectly with your positive mood ratings. Keep it up!\"")
    print()
    print("🤖 AI Coach: \"I see you completed strength training yesterday and logged")
    print("    a happy mood afterward. Your body responds well to resistance training!\"")
    print()
    print("🤖 AI Coach: \"You're 69% through your mindfulness challenge! Just 4 more")
    print("    days of meditation to complete it. You've got this! 🧘\"")
    print()
    print("🤖 AI Coach: \"Based on your patterns, you tend to have more energy on days")
    print("    when you drink 8+ glasses of water. Today's a perfect day for a")
    print("    challenging workout!\"")

if __name__ == '__main__':
    generate_insights()
    show_chat_insights()