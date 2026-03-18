"""
Migration 007: Add best_for tags to suggestion_master table
This enables context-aware activity suggestions based on user needs
"""
import sqlite3
import json
import os

def get_db_path():
    """Get database path"""
    # Try multiple possible locations
    possible_paths = [
        'mood.db',
        'backend/mood.db',
        '../mood.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return 'mood.db'  # Default

def upgrade(conn):
    """Add best_for column and populate with tags"""
    cursor = conn.cursor()
    
    try:
        # Step 1: Add best_for column
        print("\n1. Adding best_for column...")
        cursor.execute("""
            ALTER TABLE suggestion_master 
            ADD COLUMN best_for TEXT
        """)
        print("✅ Column added")
        
        # Step 2: Define tags for each activity
        activity_tags = {
            'breathing': ['stress', 'anxiety', 'work', 'quick relief', 'calm', 'focus'],
            'short_walk': ['energy', 'mood boost', 'exercise', 'nature', 'break'],
            'meditation': ['calm', 'focus', 'stress', 'anxiety', 'mindfulness'],
            'stretching': ['physical tension', 'work', 'exercise', 'energy', 'break'],
            'take_break': ['work', 'education', 'overwhelm', 'burnout', 'rest'],
            'hydrate': ['energy', 'health', 'quick relief', 'physical'],
            'music': ['mood boost', 'stress', 'energy', 'focus', 'calm'],
            'journaling': ['stress', 'anxiety', 'relationship', 'self-reflection', 'emotional'],
            'call_friend': ['loneliness', 'friend', 'relationship', 'support', 'social'],
            'gratitude': ['mood boost', 'happiness', 'mindfulness', 'positive'],
            'exercise': ['energy', 'mood boost', 'fitness', 'health', 'stress'],
            'nature': ['energy', 'mood boost', 'stress', 'calm', 'outdoor'],
            'hobby': ['mood boost', 'fun', 'creativity', 'relaxation', 'enjoyment'],
            'rest': ['tired', 'energy', 'sleep', 'burnout', 'recovery']
        }
        
        # Step 3: Update each activity with tags
        print("\n2. Populating best_for tags...")
        updated_count = 0
        
        for activity_key, tags in activity_tags.items():
            tags_json = json.dumps(tags)
            
            cursor.execute("""
                UPDATE suggestion_master 
                SET best_for = ? 
                WHERE suggestion_key = ?
            """, (tags_json, activity_key))
            
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"   ✅ {activity_key}: {tags}")
        
        print(f"\n✅ Updated {updated_count} activities with tags")
        
        # Step 4: Verify
        print("\n3. Verifying...")
        cursor.execute("""
            SELECT suggestion_key, title, best_for 
            FROM suggestion_master 
            WHERE best_for IS NOT NULL
        """)
        
        results = cursor.fetchall()
        print(f"✅ {len(results)} activities have best_for tags")
        
        # Don't close connection - let migration runner handle it
        print("\n✅ Migration completed successfully!")
        
        # Show sample
        print("\n📋 Sample activities with tags:")
        for row in results[:5]:
            key, title, tags_json = row
            tags = json.loads(tags_json) if tags_json else []
            print(f"   - {title}: {', '.join(tags[:3])}...")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  Column 'best_for' already exists, skipping column creation")
            print("   Updating tags only...")
            
            # Just update the tags
            activity_tags = {
                'breathing': ['stress', 'anxiety', 'work', 'quick relief', 'calm', 'focus'],
                'short_walk': ['energy', 'mood boost', 'exercise', 'nature', 'break'],
                'meditation': ['calm', 'focus', 'stress', 'anxiety', 'mindfulness'],
                'stretching': ['physical tension', 'work', 'exercise', 'energy', 'break'],
                'take_break': ['work', 'education', 'overwhelm', 'burnout', 'rest'],
                'hydrate': ['energy', 'health', 'quick relief', 'physical'],
                'music': ['mood boost', 'stress', 'energy', 'focus', 'calm'],
                'journaling': ['stress', 'anxiety', 'relationship', 'self-reflection', 'emotional'],
                'call_friend': ['loneliness', 'friend', 'relationship', 'support', 'social'],
                'gratitude': ['mood boost', 'happiness', 'mindfulness', 'positive'],
                'exercise': ['energy', 'mood boost', 'fitness', 'health', 'stress'],
                'nature': ['energy', 'mood boost', 'stress', 'calm', 'outdoor'],
                'hobby': ['mood boost', 'fun', 'creativity', 'relaxation', 'enjoyment'],
                'rest': ['tired', 'energy', 'sleep', 'burnout', 'recovery']
            }
            
            for activity_key, tags in activity_tags.items():
                tags_json = json.dumps(tags)
                cursor.execute("""
                    UPDATE suggestion_master 
                    SET best_for = ? 
                    WHERE suggestion_key = ?
                """, (tags_json, activity_key))
            
            # Don't close connection - let migration runner handle it
            print("✅ Tags updated successfully!")
        else:
            raise

if __name__ == "__main__":
    print("="*70)
    print("MIGRATION 007: Add best_for Tags to Activities")
    print("="*70)
    migrate()
    print("\n" + "="*70)
