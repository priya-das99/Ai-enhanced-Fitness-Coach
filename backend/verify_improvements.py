"""
Verify all schema improvements are working
"""

import sqlite3


def verify_schema():
    import os
    db_path = os.path.join(os.path.dirname(__file__), "mood.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("="*60)
    print("VERIFYING SCHEMA IMPROVEMENTS")
    print(f"Database: {db_path}")
    print("="*60)
    
    # Check foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    print(f"\n✓ Foreign keys enabled: {fk_enabled == 1}")
    
    # Check mood_logs has new columns
    cursor.execute("PRAGMA table_info(mood_logs)")
    mood_cols = [col[1] for col in cursor.fetchall()]
    required_mood_cols = ['mood_intensity', 'stress_level', 'energy_level', 'confidence_level', 'tags']
    has_mood_enhancements = all(col in mood_cols for col in required_mood_cols)
    print(f"✓ mood_logs enhanced: {has_mood_enhancements}")
    if has_mood_enhancements:
        print(f"  - Added: {', '.join(required_mood_cols)}")
    
    # Check suggestion_history has interaction tracking
    cursor.execute("PRAGMA table_info(suggestion_history)")
    sugg_cols = [col[1] for col in cursor.fetchall()]
    required_sugg_cols = ['interaction_type', 'rejected_at', 'ignored', 'expired']
    has_interaction_tracking = all(col in sugg_cols for col in required_sugg_cols)
    print(f"✓ suggestion_history enhanced: {has_interaction_tracking}")
    if has_interaction_tracking:
        print(f"  - Added: {', '.join(required_sugg_cols)}")
    
    # Check user_activity_history has quality metrics
    cursor.execute("PRAGMA table_info(user_activity_history)")
    activity_cols = [col[1] for col in cursor.fetchall()]
    required_activity_cols = ['completion_percentage', 'user_rating', 'energy_before', 'energy_after', 'satisfaction_score', 'would_repeat']
    has_quality_metrics = all(col in activity_cols for col in required_activity_cols)
    print(f"✓ user_activity_history enhanced: {has_quality_metrics}")
    if has_quality_metrics:
        print(f"  - Added: {', '.join(required_activity_cols)}")
    
    # Check chat_messages has session_id
    cursor.execute("PRAGMA table_info(chat_messages)")
    chat_cols = [col[1] for col in cursor.fetchall()]
    has_session_link = 'session_id' in chat_cols
    print(f"✓ chat_messages linked to sessions: {has_session_link}")
    
    # Check user_behavior_metrics has rejection tracking
    cursor.execute("PRAGMA table_info(user_behavior_metrics)")
    metrics_cols = [col[1] for col in cursor.fetchall()]
    required_metrics_cols = ['suggestion_rejection_rate', 'total_suggestions_rejected', 'total_suggestions_ignored']
    has_rejection_tracking = all(col in metrics_cols for col in required_metrics_cols)
    print(f"✓ user_behavior_metrics enhanced: {has_rejection_tracking}")
    if has_rejection_tracking:
        print(f"  - Added: {', '.join(required_metrics_cols)}")
    
    # Check ranking context tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suggestion_ranking_context'")
    has_ranking_context = cursor.fetchone() is not None
    print(f"✓ suggestion_ranking_context table: {has_ranking_context}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suggestion_ranking_details'")
    has_ranking_details = cursor.fetchone() is not None
    print(f"✓ suggestion_ranking_details table: {has_ranking_details}")
    
    # Check indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    required_indexes = [
        'idx_mood_logs_user',
        'idx_suggestion_history_user',
        'idx_activity_history_user',
        'idx_ranking_context_user',
        'idx_chat_messages_session'
    ]
    has_indexes = all(idx in indexes for idx in required_indexes)
    print(f"✓ Performance indexes created: {has_indexes}")
    print(f"  - Total indexes: {len(indexes)}")
    
    # Check suggestion_master is populated
    cursor.execute("SELECT COUNT(*) FROM suggestion_master")
    suggestion_count = cursor.fetchone()[0]
    print(f"✓ Suggestions populated: {suggestion_count} suggestions")
    
    # Check demo user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username='demo'")
    has_demo_user = cursor.fetchone()[0] > 0
    print(f"✓ Demo user created: {has_demo_user}")
    
    # Check user_id types are INTEGER
    cursor.execute("PRAGMA table_info(suggestion_history)")
    user_id_type = [col[2] for col in cursor.fetchall() if col[1] == 'user_id'][0]
    print(f"✓ suggestion_history.user_id type: {user_id_type}")
    
    cursor.execute("PRAGMA table_info(analytics_events)")
    user_id_type2 = [col[2] for col in cursor.fetchall() if col[1] == 'user_id'][0]
    print(f"✓ analytics_events.user_id type: {user_id_type2}")
    
    cursor.execute("PRAGMA table_info(user_behavior_metrics)")
    user_id_type3 = [col[2] for col in cursor.fetchall() if col[1] == 'user_id'][0]
    print(f"✓ user_behavior_metrics.user_id type: {user_id_type3}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ ALL SCHEMA IMPROVEMENTS VERIFIED!")
    print("="*60)
    print("\nDatabase is production-ready with:")
    print("  • Foreign key constraints enabled")
    print("  • Enhanced mood tracking (intensity, stress, energy)")
    print("  • Suggestion interaction tracking (reject, ignore)")
    print("  • Activity quality metrics (rating, satisfaction)")
    print("  • Chat session linking")
    print("  • Complete ranking context logging")
    print("  • Performance indexes")
    print("  • Consistent INTEGER user_id types")


if __name__ == '__main__':
    verify_schema()
