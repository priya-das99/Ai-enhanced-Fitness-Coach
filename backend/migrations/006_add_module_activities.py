"""Add module-triggering activities (outdoor, 7-minute workout, meditation)"""
import sqlite3

def upgrade(db_path: str = "mood.db"):
    """Add new activities that trigger external modules"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if suggestion_master table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='suggestion_master'
        """)
        
        if not cursor.fetchone():
            print("❌ suggestion_master table not found. Please run earlier migrations first.")
            return
        
        # Add new module-triggering activities
        new_activities = [
            {
                'suggestion_key': 'outdoor_activity',
                'title': 'Start Outdoor Activity',
                'description': 'Get outside for fresh air and nature - opens outdoor activity module',
                'category': 'physical',
                'effort_level': 'medium',
                'duration_minutes': 20,
                'is_active': 1,
                'triggers_module': 'outdoor_activity',  # Module identifier
                'module_type': 'external'
            },
            {
                'suggestion_key': 'seven_minute_workout',
                'title': 'Start 7-Minute Workout',
                'description': 'Quick high-intensity workout - opens 7-minute workout module',
                'category': 'physical',
                'effort_level': 'high',
                'duration_minutes': 7,
                'is_active': 1,
                'triggers_module': '7min_workout',  # Module identifier
                'module_type': 'external'
            },
            {
                'suggestion_key': 'guided_meditation',
                'title': 'Start Meditation Session',
                'description': 'Guided meditation for calm and focus - opens meditation module',
                'category': 'mindfulness',
                'effort_level': 'low',
                'duration_minutes': 10,
                'is_active': 1,
                'triggers_module': 'meditation',  # Module identifier
                'module_type': 'external'
            }
        ]
        
        # Check if columns exist, add if needed
        cursor.execute("PRAGMA table_info(suggestion_master)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'triggers_module' not in columns:
            cursor.execute("""
                ALTER TABLE suggestion_master 
                ADD COLUMN triggers_module TEXT
            """)
            print("✅ Added triggers_module column")
        
        if 'module_type' not in columns:
            cursor.execute("""
                ALTER TABLE suggestion_master 
                ADD COLUMN module_type TEXT DEFAULT 'internal'
            """)
            print("✅ Added module_type column")
        
        # Insert new activities
        for activity in new_activities:
            cursor.execute("""
                INSERT OR REPLACE INTO suggestion_master 
                (suggestion_key, title, description, category, effort_level, 
                 duration_minutes, is_active, triggers_module, module_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity['suggestion_key'],
                activity['title'],
                activity['description'],
                activity['category'],
                activity['effort_level'],
                activity['duration_minutes'],
                activity['is_active'],
                activity['triggers_module'],
                activity['module_type']
            ))
        
        conn.commit()
        print(f"✅ Added {len(new_activities)} module-triggering activities")
        
        # Show summary
        cursor.execute("""
            SELECT suggestion_key, title, triggers_module 
            FROM suggestion_master 
            WHERE module_type = 'external'
        """)
        
        print("\n📊 Module Activities:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} → {row[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "mood.db"
    upgrade(db_path)
