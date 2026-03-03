"""
View Chat Messages - Show how chat messages are stored in the database
"""

import sqlite3
import os
import json

def view_chat_messages():
    """View chat messages and their format"""
    db_path = os.path.join(os.path.dirname(__file__), 'mood.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("💬 CHAT MESSAGES STORAGE FORMAT")
    print("=" * 80)
    
    # Get table schema
    print("\n📐 TABLE SCHEMA:")
    print("-" * 80)
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        pk_marker = " [PRIMARY KEY]" if pk else ""
        null_marker = " NOT NULL" if not_null else ""
        default_marker = f" DEFAULT {default}" if default else ""
        print(f"  {name:20} {col_type:15}{pk_marker}{null_marker}{default_marker}")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total Messages: {total}")
    
    # Get sample conversation
    print("\n" + "=" * 80)
    print("💬 SAMPLE CONVERSATION (Latest 10 messages)")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, user_id, message, sender, timestamp, metadata
        FROM chat_messages
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    messages = cursor.fetchall()
    
    for msg in reversed(messages):  # Show oldest first
        msg_id, user_id, message, sender, timestamp, metadata = msg
        
        print(f"\n{'─' * 80}")
        print(f"ID: {msg_id}")
        print(f"User ID: {user_id}")
        print(f"Sender: {sender}")
        print(f"Timestamp: {timestamp}")
        print(f"Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        if metadata:
            print(f"Metadata: {metadata[:200]}{'...' if len(metadata) > 200 else ''}")
            
            # Try to parse metadata as JSON
            try:
                metadata_obj = json.loads(metadata)
                print("\nParsed Metadata:")
                for key, value in metadata_obj.items():
                    if isinstance(value, list):
                        print(f"  {key}: [{len(value)} items]")
                        if value and len(value) <= 3:
                            for item in value:
                                if isinstance(item, dict):
                                    print(f"    - {item.get('name', item.get('id', 'item'))}")
                    elif isinstance(value, dict):
                        print(f"  {key}: {{{len(value)} keys}}")
                    else:
                        print(f"  {key}: {value}")
            except:
                pass
        else:
            print("Metadata: None")
    
    # Show message statistics
    print("\n" + "=" * 80)
    print("📊 MESSAGE STATISTICS")
    print("=" * 80)
    
    # Messages by sender
    cursor.execute("""
        SELECT sender, COUNT(*) as count
        FROM chat_messages
        GROUP BY sender
    """)
    
    print("\nMessages by Sender:")
    for row in cursor.fetchall():
        print(f"  {row[0]:10} {row[1]:5} messages")
    
    # Messages by user
    cursor.execute("""
        SELECT user_id, COUNT(*) as count
        FROM chat_messages
        GROUP BY user_id
        ORDER BY count DESC
        LIMIT 5
    """)
    
    print("\nTop 5 Most Active Users:")
    for row in cursor.fetchall():
        print(f"  User {row[0]:10} {row[1]:5} messages")
    
    # Messages with metadata
    cursor.execute("""
        SELECT COUNT(*) 
        FROM chat_messages 
        WHERE metadata IS NOT NULL
    """)
    with_metadata = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM chat_messages 
        WHERE metadata IS NULL
    """)
    without_metadata = cursor.fetchone()[0]
    
    print(f"\nMessages with metadata: {with_metadata}")
    print(f"Messages without metadata: {without_metadata}")
    
    # Show metadata types
    print("\n" + "=" * 80)
    print("🔍 METADATA EXAMPLES")
    print("=" * 80)
    
    cursor.execute("""
        SELECT DISTINCT metadata
        FROM chat_messages
        WHERE metadata IS NOT NULL
        LIMIT 5
    """)
    
    print("\nSample Metadata Structures:")
    for i, row in enumerate(cursor.fetchall(), 1):
        metadata = row[0]
        print(f"\nExample {i}:")
        print(f"  Raw: {metadata[:150]}{'...' if len(metadata) > 150 else ''}")
        
        try:
            parsed = json.loads(metadata)
            print(f"  Structure: {json.dumps(parsed, indent=4)[:300]}...")
        except:
            print("  (Not valid JSON)")
    
    conn.close()
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")

if __name__ == '__main__':
    view_chat_messages()
