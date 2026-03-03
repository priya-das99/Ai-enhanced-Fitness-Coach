#!/usr/bin/env python3
"""
Demo User Insights Guide
Shows what insights are available and when they appear
"""

import sys
sys.path.insert(0, '.')

from app.services.insight_generator import get_insight_generator
from app.services.pattern_detector import PatternDetector

def show_insights_guide():
    print("\n" + "="*70)
    print("📊 DEMO USER INSIGHTS GUIDE")
    print("="*70)
    
    print("\n🎯 WHEN INSIGHTS APPEAR:")
    print("-" * 70)
    print("""
1. ✅ AFTER MOOD LOGGING (negative mood with reason)
   - User logs a negative mood (😟 😰 😢 😭 😡 😤 😔)
   - User provides a reason for the mood
   - Example: "I'm feeling stressed about work"
   
2. ✅ AFTER ACTIVITY LOGGING (significant activities)
   - User logs sleep or exercise
   - Example: "I slept 7 hours" or "I did a workout"
   
3. ✅ AFTER EXTERNAL ACTIVITY COMPLETION
   - User completes an activity via button click
   - Example: Clicks "Complete Meditation" button
   
4. ✅ USER ASKS ABOUT PROGRESS
   - User explicitly asks: "How am I doing?"
   - User asks: "Show my progress" or "My trends"
   - User asks: "Am I improving?"
   
5. ✅ ENGAGEMENT DROP DETECTED
   - User's acceptance rate drops below 30%
   - System detects user is losing interest
""")
    
    print("\n⏰ TIMING RULES:")
    print("-" * 70)
    print("""
- Maximum 1 insight per session
- Maximum 1 insight per 24 hours
- Maximum 1 insight per 3 mood logs
- Never shown during emotional venting
- Never shown during clarification flows
- High-priority insights: minimum 12 hours apart
""")
    
    print("\n📋 AVAILABLE INSIGHT TYPES:")
    print("-" * 70)
    
    # Get actual insights for demo user
    try:
        insight_gen = get_insight_generator()
        pattern_detector = PatternDetector()
        
        user_id = 1
        patterns = pattern_detector.detect_all_patterns(user_id)
        insights = insight_gen.generate_insights(user_id)
        
        if insights:
            print(f"\n✅ Found {len(insights)} insights for demo user:\n")
            
            for i, insight in enumerate(insights, 1):
                severity_emoji = {
                    'high': '🔴',
                    'moderate': '🟡',
                    'low': '🟢'
                }.get(insight.severity, '💡')
                
                print(f"{i}. {severity_emoji} {insight.insight_type.upper()}")
                print(f"   Severity: {insight.severity}")
                print(f"   Priority: {insight.priority}")
                print(f"   Data: {insight.data}")
                print()
        else:
            print("\n⚠️ No insights generated (may need more user data)")
            
    except Exception as e:
        print(f"\n❌ Error loading insights: {e}")
    
    print("\n💬 EXAMPLE INSIGHT MESSAGES:")
    print("-" * 70)
    print("""
🔴 HIGH SEVERITY (Priority 1-2):
   "🔴 You've been stressed for 5 consecutive days, mostly about work.
    This prolonged stress is affecting your wellbeing."
   
   "🔴 You've been stressed for 3 days and your activity dropped 45%.
    Let's work together to break this pattern."

🟡 MODERATE SEVERITY (Priority 3):
   "🟡 Your activity has declined 35% - from 18 activities to just 12
    in the last week."
   
   "🟡 Your water intake has dropped 40% - averaging only 4.5 glasses
    per day, down from 7.5. Dehydration can worsen stress."

🟢 LOW SEVERITY (Priority 4-5):
   "🔥 You're on a 31-day activity streak! Keep it going!"
   
   "📈 You're 28% more active this week! (23 activities vs 18.0 baseline)"
   
   "💡 Meditation helped you before (rated 4.5/5) - would you like to
    try that?"
""")
    
    print("\n🎯 CHALLENGE-RELATED INSIGHTS:")
    print("-" * 70)
    print("""
When user asks "How am I doing?" they see:

1. Activity Streak: "🔥 You're on a 31-day activity streak!"
2. Activity Improvement: "📈 You're 28% more active this week!"
3. Challenge Progress:
   - 🔥 Almost There: 80%+ complete
   - 📈 Making Progress: 30-80% complete
   - 🌱 Just Getting Started: <30% complete
4. Motivational Message based on progress
""")
    
    print("\n📱 HOW TO TRIGGER INSIGHTS IN DEMO:")
    print("-" * 70)
    print("""
1. Ask "How am I doing?" 
   → Shows activity streak, improvements, and challenge progress
   
2. Log a negative mood with reason
   → May show stress pattern or proven solution insight
   
3. Complete an activity
   → May show activity streak or improvement trend
   
4. Ask "Show my progress" or "My trends"
   → Shows comprehensive progress report with insights
   
5. Log sleep or exercise
   → May show health pattern insights
""")
    
    print("\n" + "="*70)
    print("✅ Guide Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    show_insights_guide()
