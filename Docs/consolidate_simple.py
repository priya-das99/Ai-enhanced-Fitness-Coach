"""
Simple database consolidation using ATTACH
"""
import sqlite3

conn = sqlite3.connect('mood.db')
cursor = conn.cursor()

print("Attaching mood_capture.db...")
cursor.execute("ATTACH DATABASE 'mood_capture.db' AS source")

# Get schema and copy tables
tables_to_copy = ['content_categories', 'content_items', 'user_content_interactions', 'user_wellness_preferences']

for table in tables_to_copy:
    print(f"\nCopying {table}...")
    
    # Get CREATE statement from source
    cursor.execute(f"SELECT sql FROM source.sqlite_master WHERE type='table' AND name='{table}'")
    create_sql = cursor.fetchone()
    
    if create_sql:
        # Create table in target
        cursor.execute(create_sql[0])
        
        # Copy data
        cursor.execute(f"INSERT OR REPLACE INTO {table} SELECT * FROM source.{table}")
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"✅ {table}: {count} rows copied")
    else:
        print(f"⚠️  {table}: not found in source")

cursor.execute("DETACH DATABASE source")
conn.commit()
conn.close()

print("\n✅ Consolidation complete! mood.db now has all content.")
