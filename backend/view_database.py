import sqlite3
import sys

def view_database(db_path='backend/mood_capture.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("=" * 80)
    print(f"DATABASE: {db_path}")
    print("=" * 80)
    print(f"\nFound {len(tables)} tables\n")
    
    for (table_name,) in tables:
        print(f"\n{'=' * 80}")
        print(f"TABLE: {table_name}")
        print('=' * 80)
        
        # Get schema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        schema = cursor.fetchone()[0]
        print(f"\nSchema:\n{schema}\n")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        # Show sample data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\nSample data (first 5 rows):")
            print("-" * 80)
            print(" | ".join(columns))
            print("-" * 80)
            
            for row in rows:
                # Truncate long values
                formatted_row = []
                for val in row:
                    val_str = str(val) if val is not None else 'NULL'
                    if len(val_str) > 50:
                        val_str = val_str[:47] + '...'
                    formatted_row.append(val_str)
                print(" | ".join(formatted_row))
    
    conn.close()
    print("\n" + "=" * 80)
    print("END OF DATABASE")
    print("=" * 80)

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'backend/mood_capture.db'
    view_database(db_path)
