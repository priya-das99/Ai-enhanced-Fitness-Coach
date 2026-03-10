import sys
sys.path.insert(0, '.')
from app.core.database import get_db

with get_db() as db:
    cursor = db.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row['name'] for row in cursor.fetchall()]
    print("Tables in database:")
    for table in tables:
        print(f"  - {table}")
