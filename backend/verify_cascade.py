import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "mood.db")
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

print("="*60)
print("VERIFYING CASCADE DELETE CONFIGURATION")
print("="*60)

# Check if foreign keys are enabled
cursor.execute("PRAGMA foreign_keys")
fk_enabled = cursor.fetchone()[0]
print(f"\n✓ Foreign keys enabled in connection: {fk_enabled == 1}")

# Check foreign key definitions for key tables
tables = [
    'mood_logs',
    'chat_messages',
    'suggestion_history',
    'analytics_events',
    'user_activity_history',
    'user_behavior_metrics',
    'suggestion_ranking_context',
    'user_challenges'
]

print("\nForeign Key Constraints with CASCADE:")
all_have_cascade = True

for table in tables:
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    fks = cursor.fetchall()
    if fks:
        print(f"\n{table}:")
        for fk in fks:
            on_delete = fk[6] if len(fk) > 6 else "NO ACTION"
            has_cascade = on_delete == "CASCADE" or on_delete == "SET NULL"
            status = "✓" if has_cascade else "✗"
            print(f"  {status} {fk[3]} -> {fk[2]}({fk[4]}) ON DELETE {on_delete}")
            if not has_cascade:
                all_have_cascade = False
    else:
        print(f"\n{table}: ✗ NO FOREIGN KEYS DEFINED")
        all_have_cascade = False

# Test CASCADE delete
print("\n" + "="*60)
print("TESTING CASCADE DELETE")
print("="*60)

try:
    # Create test user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES ('test_cascade', 'test@cascade.com', 'hash123', 'Test User')
    """)
    test_user_id = cursor.lastrowid
    print(f"\n✓ Created test user (ID: {test_user_id})")
    
    # Create related records
    cursor.execute("""
        INSERT INTO mood_logs (user_id, mood, mood_emoji)
        VALUES (?, '5', '😊')
    """, (test_user_id,))
    print(f"✓ Created mood_log")
    
    cursor.execute("""
        INSERT INTO suggestion_history (user_id, suggestion_key)
        VALUES (?, 'breathing')
    """, (test_user_id,))
    print(f"✓ Created suggestion_history")
    
    cursor.execute("""
        INSERT INTO analytics_events (user_id, event_type)
        VALUES (?, 'test_event')
    """, (test_user_id,))
    print(f"✓ Created analytics_event")
    
    # Count related records
    cursor.execute("SELECT COUNT(*) FROM mood_logs WHERE user_id = ?", (test_user_id,))
    mood_count_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM suggestion_history WHERE user_id = ?", (test_user_id,))
    sugg_count_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE user_id = ?", (test_user_id,))
    analytics_count_before = cursor.fetchone()[0]
    
    print(f"\nBefore delete:")
    print(f"  - mood_logs: {mood_count_before}")
    print(f"  - suggestion_history: {sugg_count_before}")
    print(f"  - analytics_events: {analytics_count_before}")
    
    # Delete user (should CASCADE)
    cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
    print(f"\n✓ Deleted test user")
    
    # Check if related records were deleted
    cursor.execute("SELECT COUNT(*) FROM mood_logs WHERE user_id = ?", (test_user_id,))
    mood_count_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM suggestion_history WHERE user_id = ?", (test_user_id,))
    sugg_count_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE user_id = ?", (test_user_id,))
    analytics_count_after = cursor.fetchone()[0]
    
    print(f"\nAfter delete:")
    print(f"  - mood_logs: {mood_count_after}")
    print(f"  - suggestion_history: {sugg_count_after}")
    print(f"  - analytics_events: {analytics_count_after}")
    
    cascade_works = (mood_count_after == 0 and sugg_count_after == 0 and analytics_count_after == 0)
    
    if cascade_works:
        print(f"\n✅ CASCADE DELETE WORKS CORRECTLY!")
    else:
        print(f"\n✗ CASCADE DELETE NOT WORKING - Orphaned records remain")
    
    conn.rollback()  # Don't actually save test data
    
except Exception as e:
    print(f"\n✗ Error testing CASCADE: {e}")
    conn.rollback()

conn.close()

print("\n" + "="*60)
if all_have_cascade:
    print("✅ ALL FOREIGN KEYS HAVE CASCADE/SET NULL")
else:
    print("⚠️  SOME FOREIGN KEYS MISSING CASCADE")
print("="*60)
