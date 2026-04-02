# app/api/v1/endpoints/demo_insights.py
# Demo endpoints for showcasing AI insights

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/insights/{insight_type}")
async def get_demo_insight(insight_type: str) -> Dict:
    """Get demo insight for showcase"""
    
    insights = {
        "day_pattern": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "📅 Day Pattern Detected",
            "message": "I've noticed that Sundays tend to be challenging for you. You've logged negative moods on 4 out of the last 5 Sundays. This is completely normal - many people experience 'Sunday blues' as they prepare for the week ahead. Let's create a Sunday routine to help you feel more positive!",
            "type": "pattern_insight",
            "confidence": 0.95,
            "pattern_data": {
                "day": "Sunday",
                "occurrences": 4,
                "total_sundays": 5,
                "pattern_strength": "strong"
            },
            "action_buttons": [
                {"id": "create_routine", "label": "📝 Create Sunday Routine"},
                {"id": "view_pattern", "label": "📊 View Pattern Details"},
                {"id": "dismiss", "label": "✅ Got it!"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        
        "sleep_issue": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "😴 Sleep Pattern Alert",
            "message": "I'm concerned about your sleep pattern this week. You've averaged only 5.2 hours per night, which is well below the recommended 7-9 hours. I've also noticed your mood ratings have dropped by 40% during this period. Poor sleep might be affecting your emotional well-being.",
            "type": "health_insight",
            "severity": "high",
            "health_data": {
                "average_sleep": 5.2,
                "recommended_sleep": "7-9 hours",
                "mood_impact": -0.40,
                "trend": "declining"
            },
            "action_buttons": [
                {"id": "sleep_tips", "label": "💤 Get Sleep Tips"},
                {"id": "set_bedtime", "label": "⏰ Set Bedtime Reminder"},
                {"id": "track_sleep", "label": "� Track Sleep Better"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        
        "activity_success": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "🏃 Activity Success Pattern",
            "message": "Great news! I've found your winning formula. When you do yoga in the morning, you're 85% more likely to have a positive mood throughout the day. You've done this 12 times, and 10 of those days were rated as 'good' or 'excellent'. Morning yoga seems to be your superpower!",
            "type": "pattern_insight",
            "confidence": 0.85,
            "pattern_data": {
                "activity": "yoga",
                "time": "morning",
                "success_rate": 0.85,
                "total_attempts": 12,
                "successful_days": 10
            },
            "action_buttons": [
                {"id": "schedule_yoga", "label": "🧘 Schedule Morning Yoga"},
                {"id": "view_correlation", "label": "📈 View Correlation"},
                {"id": "share_success", "label": "🎉 Celebrate!"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        
        "weekly_summary": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "📊 Weekly Progress Summary",
            "message": "What a week! Here's your wellness snapshot:\n💧 Hydration: 8.2/8 glasses daily (103% of goal!)\n🏃 Exercise: 4 sessions, 180 total minutes\n😊 Mood: 78% positive days (up 15% from last week)\n🎯 Challenges: Completed hydration challenge!\n🔥 Current streak: 5 days of consistent logging.\n\nYou're building incredible healthy habits!",
            "type": "weekly_summary",
            "summary_data": {
                "hydration": {"actual": 8.2, "target": 8.0, "percentage": 103},
                "exercise": {"sessions": 4, "total_minutes": 180},
                "mood": {"positive_percentage": 78, "improvement": 15},
                "challenges": {"completed": 1, "active": 2},
                "streak": {"current": 5, "type": "logging"}
            },
            "action_buttons": [
                {"id": "detailed_report", "label": "📋 Detailed Report"},
                {"id": "next_week_goals", "label": "🎯 Set Next Week Goals"},
                {"id": "share_wins", "label": "🏆 Share Wins"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        
        "predictive": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "🔮 Predictive Wellness Insight",
            "message": "Based on your patterns, I predict you'll feel most energetic tomorrow between 10 AM - 12 PM. This is your optimal window for challenging activities! Your historical data shows 92% positive mood ratings during this time when you've had good sleep (which you did last night).",
            "type": "predictive_insight",
            "prediction_data": {
                "optimal_time": "10:00-12:00",
                "confidence": 0.92,
                "based_on": ["sleep_quality", "historical_patterns"],
                "recommended_activity": "challenging_workout"
            },
            "action_buttons": [
                {"id": "schedule_workout", "label": "🏃 Schedule Workout"},
                {"id": "set_energy_reminder", "label": "⚡ Set Energy Reminder"},
                {"id": "view_prediction", "label": "📊 View Prediction Model"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        
        "stress_pattern": {
            "id": f"demo_{int(datetime.now().timestamp())}",
            "title": "😰 Stress Pattern Analysis",
            "message": "I've identified a stress pattern that might help you. You tend to feel most stressed on Monday mornings (90% of the time) and Wednesday afternoons (75% of the time). However, when you do breathing exercises on Sunday evenings, your Monday stress levels drop by 50%.",
            "type": "pattern_insight",
            "prediction_data": {
                "stress_times": ["Monday morning", "Wednesday afternoon"],
                "stress_rates": [0.90, 0.75],
                "prevention_activity": "Sunday evening breathing",
                "prevention_effectiveness": 0.50
            },
            "action_buttons": [
                {"id": "sunday_breathing", "label": "🫁 Sunday Breathing Reminder"},
                {"id": "stress_toolkit", "label": "🧰 Stress Management Kit"},
                {"id": "pattern_details", "label": "📊 View Stress Pattern"}
            ],
            "timestamp": datetime.now().isoformat()
        }
    }
    
    if insight_type not in insights:
        raise HTTPException(status_code=404, detail=f"Insight type '{insight_type}' not found")
    
    return insights[insight_type]
