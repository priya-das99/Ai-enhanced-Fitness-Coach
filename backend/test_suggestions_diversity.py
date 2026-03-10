#!/usr/bin/env python3
"""
Test suggestion diversity with different moods and reasons
"""

import sys
sys.path.insert(0, '.')

from chat_assistant.smart_suggestions import get_smart_suggestions
from chat_assistant.context_builder_simple import build_context

def test_suggestions():
    """Test suggestions for different scenarios"""
    user_id = 1
    
    print("\n" + "="*80)
    print("TESTING SUGGESTION DIVERSITY")
    print("="*80)
    
    # Build user context
    context = build_context(user_id)
    
    # Test scenarios
    scenarios = [
        ("😢", "work", "Sad because of work stress"),
        ("😟", "relationship", "Anxious about relationship"),
        ("😊", "general", "Happy, just checking in"),
        ("😡", "traffic", "Angry about traffic"),
        ("😰", "deadline", "Overwhelmed by deadline"),
        ("😐", "tired", "Feeling tired and low energy"),
    ]
    
    for mood_emoji, reason, description in scenarios:
        print(f"\n{'='*80}")
        print(f"Scenario: {description}")
        print(f"Mood: {mood_emoji} | Reason: {reason}")
        print(f"{'='*80}")
        
        # Get suggestions
        suggestions = get_smart_suggestions(
            mood_emoji=mood_emoji,
            reason=reason,
            context=context,
            count=5
        )
        
        if suggestions:
            print(f"\nGot {len(suggestions)} suggestions:")
            for i, sugg in enumerate(suggestions, 1):
                print(f"\n{i}. {sugg.get('name', 'Unknown')}")
                print(f"   ID: {sugg.get('id', 'N/A')}")
                print(f"   Category: {sugg.get('category', 'N/A')}")
                print(f"   Duration: {sugg.get('duration', 'N/A')}")
                print(f"   Effort: {sugg.get('effort', 'N/A')}")
                print(f"   Description: {sugg.get('description', 'N/A')[:80]}...")
                
                # Check if it's content or activity
                if sugg.get('action_type') == 'open_external':
                    print(f"   Type: External Content ({sugg.get('content_type', 'N/A')})")
                    print(f"   URL: {sugg.get('content_url', 'N/A')[:50]}...")
                else:
                    print(f"   Type: Activity")
        else:
            print("\n⚠️  NO SUGGESTIONS RETURNED!")
    
    print("\n" + "="*80)
    print("DIVERSITY TEST COMPLETE")
    print("="*80 + "\n")

def check_database_content():
    """Check what's actually in the database"""
    import sqlite3
    import os
    
    print("\n" + "="*80)
    print("CHECKING DATABASE CONTENT")
    print("="*80)
    
    db_path = os.path.join(os.path.dirname(__file__), 'mood_capture.db')
    
    if not os.path.exists(db_path):
        print(f"\n⚠️  Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check suggestion_master
    print("\n--- SUGGESTION_MASTER TABLE ---")
    cursor.execute("SELECT COUNT(*) FROM suggestion_master WHERE is_active = 1")
    count = cursor.fetchone()[0]
    print(f"Active suggestions: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT suggestion_key, title, category, effort_level 
            FROM suggestion_master 
            WHERE is_active = 1 
            LIMIT 10
        """)
        print("\nFirst 10 suggestions:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} ({row[2]}, {row[3]})")
    
    # Check content_items
    print("\n--- CONTENT_ITEMS TABLE ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM content_items WHERE is_active = 1")
        count = cursor.fetchone()[0]
        print(f"Active content items: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT ci.id, ci.title, ci.content_type, c.name as category
                FROM content_items ci
                JOIN content_categories c ON ci.category_id = c.id
                WHERE ci.is_active = 1
                LIMIT 10
            """)
            print("\nFirst 10 content items:")
            for row in cursor.fetchall():
                print(f"  - content_{row[0]}: {row[1]} ({row[2]}, {row[3]})")
    except Exception as e:
        print(f"⚠️  Error reading content_items: {e}")
    
    conn.close()
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    # First check what's in the database
    check_database_content()
    
    # Then test suggestions
    test_suggestions()
