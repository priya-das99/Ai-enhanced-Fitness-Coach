"""
Consolidate all tables from mood.db into mood_capture.db
Then update all code references to use mood_capture.db only
"""
import sqlite3
import os

def copy_missing_tables():
    """Copy missing tables from mood.db to mood_capture.db"""
    
    print("="*70)
    print("DATABASE CONSOLIDATION: mood.db → mood_capture.db")
    print("="*70)
    
    # Connect to both databases
    source_db = sqlite3.connect('mood.db')
    target_db = sqlite3.connect('mood_capture.db')
    
    source_cursor = source_db.cursor()
    target_cursor = target_db.cursor()
    
    # Get tables from source
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    source_tables = set([row[0] for row in source_cursor.fetchall()])
    
    # Get tables from target
    target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    target_tables = set([row[0] for row in target_cursor.fetchall()])
    
    print(f"\nSource (mood.db): {len(source_tables)} tables")
    print(f"Target (mood_capture.db): {len(target_tables)} tables")
    
    # Find missing tables
    missing_tables = source_tables - target_tables
    
    if missing_tables:
        print(f"\n📋 Missing tables in mood_capture.db: {len(missing_tables)}")
        for table in sorted(missing_tables):
            print(f"   - {table}")
        
        print("\n🔄 Copying missing tables...")
        
        for table in missing_tables:
            # Get CREATE statement
            source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            create_sql = source_cursor.fetchone()[0]
            
            # Create table in target
            target_cursor.execute(create_sql)
            
            # Copy data
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()
            
            if rows:
                # Get column count
                placeholders = ','.join(['?' for _ in range(len(rows[0]))])
                target_cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
                print(f"   ✅ {table}: {len(rows)} rows copied")
            else:
                print(f"   ✅ {table}: table created (no data)")
        
        target_db.commit()
        print("\n✅ All missing tables copied successfully!")
    else:
        print("\n✅ No missing tables - mood_capture.db is up to date!")
    
    # Verify
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    
    target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    final_tables = [row[0] for row in target_cursor.fetchall()]
    
    print(f"\nmood_capture.db now has {len(final_tables)} tables:")
    for table in sorted(final_tables):
        target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = target_cursor.fetchone()[0]
        print(f"   - {table}: {count} rows")
    
    source_db.close()
    target_db.close()
    
    print("\n" + "="*70)
    print("✅ CONSOLIDATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    copy_missing_tables()
