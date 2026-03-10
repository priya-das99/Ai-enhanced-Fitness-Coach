import sys
sys.path.insert(0, '.')
from app.core.database import get_db

with get_db() as db:
    cursor = db.cursor()
    cursor.execute('PRAGMA table_info(chat_messages)')
    print("chat_messages schema:")
    for row in cursor.fetchall():
        print(f"  {dict(row)}")
