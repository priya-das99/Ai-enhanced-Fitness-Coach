"""
Migration 013: Add Quick Actions to Activity Catalog
Adds quick action activities to database and adds quick_action flag
"""

import sqlite3
from datetime import datetime

def upgrade(conn: sqlite3.Connection):
    """Add quick_action column and populate with quick actions"""
    cursor = conn.cursor()
    
    print("Migration 013: Adding quick actions...")
    
    # Step 1: Add quick_action column
    try:
        cursor.execute("""
            ALTER TABLE activity_catalog
            ADD COLUMN quick_action INTEGER DEFAULT 0
        """)
        print("✅ Added quick_action column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  quick_action column already exists")
        else:
            raise
    
    # Step 2: Add best_for column for mood mapping
    try:
        cursor.execute("""
            ALTER TABLE activity_catalog
            ADD COLUMN best_for TEXT
        """)
        print("✅ Added best_for column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  best_for column already exists")
        else:
            raise
    
    # Step 3: Insert quick action activities
    quick_actions = [
        {
            'id': 'breathing',
            'name': 'Breathing Exercise',
            'category': 'wellbeing',
            'icon': '🫁',
            'default_duration': 5,
            'requires_duration': 0,
            'description': 'Quick breathing exercises to calm your mind',
            'quick_action': 1,
            'best_for': 'work,stress,anxiety,travel'
        },
        {
            'id': 'take_break',
            'name': 'Take a Break',
            'category': 'wellbeing',
            'icon': '☕',
            'default_duration': 5,
            'requires_duration': 0,
            'description': 'Step away from current activity and rest',
            'quick_action': 1,
            'best_for': 'education,work,tired'
        },
        {
            'id': 'stretching',
            'name': 'Stretching',
            'category': 'exercise',
            'icon': '🤸',
            'default_duration': 10,
            'requires_duration': 0,
            'description': 'Gentle stretches to release tension',
            'quick_action': 1,
            'best_for': 'exercise,tired,morning'
        },
        {
            'id': 'short_walk',
            'name': 'Short Walk',
            'category': 'exercise',
            'icon': '🚶',
            'default_duration': 15,
            'requires_duration': 0,
            'description': 'Brief walk or movement to clear your mind',
            'quick_action': 1,
            'best_for': 'work,food,stress'
        },
        {
            'id': 'listen_music',
            'name': 'Listen to Music',
            'category': 'wellbeing',
            'icon': '🎵',
            'default_duration': 15,
            'requires_duration': 0,
            'description': 'Relaxing music to calm your mind',
            'quick_action': 1,
            'best_for': 'stress,anxiety,sad'
        }
    ]
    
    for action in quick_actions:
        # Check if already exists
        cursor.execute("SELECT id FROM activity_catalog WHERE id = ?", (action['id'],))
        if cursor.fetchone():
            # Update existing
            cursor.execute("""
                UPDATE activity_catalog
                SET quick_action = ?, best_for = ?
                WHERE id = ?
            """, (action['quick_action'], action['best_for'], action['id']))
            print(f"✅ Updated {action['name']} as quick action")
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO activity_catalog 
                (id, name, category, icon, default_duration, requires_duration, 
                 description, active, quick_action, best_for)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                action['id'],
                action['name'],
                action['category'],
                action['icon'],
                action['default_duration'],
                action['requires_duration'],
                action['description'],
                action['quick_action'],
                action['best_for']
            ))
            print(f"✅ Added {action['name']} as quick action")
    
    # Step 4: Update existing activities with best_for tags
    existing_updates = [
        ('meditation', 'stress,anxiety,relationship,family,evening'),
        ('journaling', 'stress,sad,reflection'),
        ('reading', 'relaxation,evening,bored'),
        ('running', 'energetic,morning,happy'),
        ('cycling', 'energetic,happy,exercise'),
        ('yoga', 'stress,morning,flexibility')
    ]
    
    for activity_id, best_for in existing_updates:
        cursor.execute("""
            UPDATE activity_catalog
            SET best_for = ?
            WHERE id = ?
        """, (best_for, activity_id))
    
    print("✅ Updated existing activities with best_for tags")
    
    conn.commit()
    print("✅ Migration 013 complete!")

def downgrade(conn: sqlite3.Connection):
    """Remove quick actions"""
    cursor = conn.cursor()
    
    # Remove quick action activities
    cursor.execute("DELETE FROM activity_catalog WHERE quick_action = 1")
    
    # Note: SQLite doesn't support DROP COLUMN easily
    # Columns will remain but unused
    
    conn.commit()
    print("✅ Migration 013 downgrade complete")

if __name__ == '__main__':
    # Run migration
    conn = sqlite3.connect('mood_capture.db')
    upgrade(conn)
    conn.close()
