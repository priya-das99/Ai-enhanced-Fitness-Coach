from flask import Flask, request, jsonify, render_template
from db import init_db, get_connection
from datetime import datetime
from llm_service import llm_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize DB on app start
init_db()

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/api/mood", methods=["POST"])
def log_mood():
    data = request.json

    user_id = data.get("user_id")
    mood = data.get("mood")
    reason = data.get("reason")

    if not user_id or not mood:
        return jsonify({"error": "user_id and mood required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Use local timestamp
    local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO mood_logs (user_id, mood, reason, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, mood, reason, local_timestamp)
    )

    conn.commit()
    conn.close()

    response = {
        "status": "success",
        "message": f"Mood '{mood}' logged successfully"
    }

    # Smart suggestion system - LLM enhanced with rule-based fallback
    suggestion, videos = get_smart_suggestions_enhanced(mood, reason, user_id)
    
    if suggestion:
        response["suggestion"] = suggestion
    
    if videos:
        response["videos"] = videos

    return jsonify(response)

def get_smart_suggestions_enhanced(mood, reason=None, user_id="demo_user"):
    """Enhanced suggestion system with LLM selection and rule-based fallback"""
    
    # Only provide suggestions for negative moods
    negative_moods = ["horrible", "not good", "tired"]
    
    if mood.lower() not in negative_moods:
        return None, []
    
    # Try LLM selection first
    selected_category = None
    source_type = "rule_based_fallback"
    
    try:
        selected_category, source_type = llm_service.select_suggestion_with_llm(mood, reason, user_id)
        if selected_category:
            logger.info(f"Selected category: {selected_category} (source: {source_type})")
    except Exception as e:
        logger.error(f"LLM selection failed: {e}")
    
    # Get suggestion content using existing rule-based system
    suggestion_text, videos = get_smart_suggestions(mood, reason)
    
    if selected_category and suggestion_text:
        enhanced_suggestion = {
            "text": suggestion_text,
            "category": selected_category,
            "source": source_type
        }
        
        if source_type == "openai_llm":
            logger.info(f"🤖 TRUE OpenAI LLM suggestion: category='{selected_category}', user='{user_id}', mood='{mood}'")
        elif source_type == "smart_rules":
            logger.info(f"🧠 Smart rule-based suggestion: category='{selected_category}', user='{user_id}', mood='{mood}'")
            
        return enhanced_suggestion, videos
    
    # Fallback to pure rule-based
    if suggestion_text:
        fallback_suggestion = {
            "text": suggestion_text, 
            "category": "rule_based",
            "source": "rule_based_fallback"
        }
        logger.info(f"🔧 Rule-based fallback suggestion: user='{user_id}', mood='{mood}'")
        return fallback_suggestion, videos
    
    return None, []

def get_smart_suggestions(mood, reason=None):
    """Generate smart suggestions based on mood and reason - ONLY for negative moods"""
    
    # Only provide suggestions for negative moods
    negative_moods = ["horrible", "not good", "tired"]
    
    if mood.lower() not in negative_moods:
        return None, []
    
    # Fitness and wellness suggestions for negative moods only
    suggestions = {
        "horrible": {
            "work_stress": {
                "text": "Work stress can be overwhelming. Try a 5-minute breathing exercise and consider a short walk.",
                "videos": [
                    {"title": "5-Minute Stress Relief Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=inpok4MKVLM"},
                    {"title": "Quick Desk Stretches for Work", "type": "Fitness", "url": "https://www.youtube.com/watch?v=RqcOCBb4arc"},
                    {"title": "Calming Nature Sounds", "type": "Relaxation", "url": "https://www.youtube.com/watch?v=eKFTSSKCzWA"}
                ]
            },
            "relationship": {
                "text": "Relationship issues can be tough. Consider talking to someone you trust or practicing self-care.",
                "videos": [
                    {"title": "Self-Love Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=itZMM5gCboo"},
                    {"title": "Gentle Yoga for Emotional Healing", "type": "Yoga", "url": "https://www.youtube.com/watch?v=GLy2rYHwUqY"},
                    {"title": "Uplifting Music Playlist", "type": "Music", "url": "https://www.youtube.com/watch?v=ZbZSe6N_BXs"}
                ]
            },
            "health": {
                "text": "Health concerns are stressful. Focus on what you can control - gentle movement and relaxation.",
                "videos": [
                    {"title": "Gentle Chair Exercises", "type": "Fitness", "url": "https://www.youtube.com/watch?v=KQm4w_2UQP4"},
                    {"title": "Healing Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=U75g2mDTXtA"},
                    {"title": "Peaceful Piano Music", "type": "Music", "url": "https://www.youtube.com/watch?v=1ZYbU82GVz4"}
                ]
            },
            "default": {
                "text": "You're going through a tough time. Be gentle with yourself and try some calming activities.",
                "videos": [
                    {"title": "10-Minute Meditation for Difficult Times", "type": "Meditation", "url": "https://www.youtube.com/watch?v=O-6f5wQXSu8"},
                    {"title": "Gentle Stretching Routine", "type": "Fitness", "url": "https://www.youtube.com/watch?v=g_tea8ZNk5A"},
                    {"title": "Soothing Rain Sounds", "type": "Relaxation", "url": "https://www.youtube.com/watch?v=mPZkdNFkNps"}
                ]
            }
        },
        "not good": {
            "work_stress": {
                "text": "Work stress is common. Try a quick workout or meditation to reset your energy.",
                "videos": [
                    {"title": "10-Minute Desk Break Workout", "type": "Fitness", "url": "https://www.youtube.com/watch?v=wUEl8KrMz14"},
                    {"title": "Stress Relief Breathing", "type": "Meditation", "url": "https://www.youtube.com/watch?v=tybOi4hjZFQ"},
                    {"title": "Focus Music for Work", "type": "Music", "url": "https://www.youtube.com/watch?v=5qap5aO4i9A"}
                ]
            },
            "sleep": {
                "text": "Lack of sleep affects everything. Try some gentle stretches and plan for better sleep tonight.",
                "videos": [
                    {"title": "Bedtime Yoga Routine", "type": "Yoga", "url": "https://www.youtube.com/watch?v=v7AYKMP6rOE"},
                    {"title": "Sleep Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=aAVPDYhW_nw"},
                    {"title": "Relaxing Sleep Music", "type": "Music", "url": "https://www.youtube.com/watch?v=1ZYbU82GVz4"}
                ]
            },
            "default": {
                "text": "Things could be better. A little movement or mindfulness might help shift your energy.",
                "videos": [
                    {"title": "5-Minute Energy Boost Workout", "type": "Fitness", "url": "https://www.youtube.com/watch?v=50kH47ZztHs"},
                    {"title": "Mindfulness Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=ZToicYcHIOU"},
                    {"title": "Motivational Music", "type": "Music", "url": "https://www.youtube.com/watch?v=g-jwWYX7Jlo"}
                ]
            }
        },
        "tired": {
            "sleep": {
                "text": "Lack of sleep is tough. Try gentle movement to energize or relaxation if you can rest soon.",
                "videos": [
                    {"title": "Gentle Morning Stretches", "type": "Fitness", "url": "https://www.youtube.com/watch?v=g_tea8ZNk5A"},
                    {"title": "Power Nap Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=A5dE25ANU0k"},
                    {"title": "Energizing Playlist", "type": "Music", "url": "https://www.youtube.com/watch?v=thiUW_hBJ2w"}
                ]
            },
            "work_stress": {
                "text": "Mental fatigue from work is real. Take a break and do something refreshing.",
                "videos": [
                    {"title": "Quick Energy Boost Exercises", "type": "Fitness", "url": "https://www.youtube.com/watch?v=50kH47ZztHs"},
                    {"title": "Refreshing Breathing Exercise", "type": "Meditation", "url": "https://www.youtube.com/watch?v=tybOi4hjZFQ"},
                    {"title": "Upbeat Workout Music", "type": "Music", "url": "https://www.youtube.com/watch?v=fBYVlFXsEME"}
                ]
            },
            "default": {
                "text": "Feeling tired is normal. Listen to your body - rest if needed, or try gentle movement.",
                "videos": [
                    {"title": "Gentle Yoga for Fatigue", "type": "Yoga", "url": "https://www.youtube.com/watch?v=GLy2rYHwUqY"},
                    {"title": "Restorative Meditation", "type": "Meditation", "url": "https://www.youtube.com/watch?v=U75g2mDTXtA"},
                    {"title": "Calm Background Music", "type": "Music", "url": "https://www.youtube.com/watch?v=1ZYbU82GVz4"}
                ]
            }
        }
    }
    
    # Get suggestion for the negative mood and reason
    if mood in suggestions:
        mood_suggestions = suggestions[mood]
        if reason and reason in mood_suggestions:
            suggestion_data = mood_suggestions[reason]
        else:
            suggestion_data = mood_suggestions["default"]
        
        return suggestion_data["text"], suggestion_data["videos"]
    
    # No suggestions for positive moods
    return None, []

@app.route("/logs")
def view_logs():
    """View all mood logs in a simple HTML table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM mood_logs ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    conn.close()
    
    return render_template('logs.html', logs=logs)

@app.route("/api/logs")
def get_logs():
    """Get mood logs as JSON"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM mood_logs ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    logs_list = []
    for log in logs:
        logs_list.append({
            'id': log[0],
            'user_id': log[1], 
            'mood': log[2],
            'reason': log[3],
            'timestamp': log[4]
        })
    
    return jsonify(logs_list)

if __name__ == "__main__":
    app.run(debug=True)
