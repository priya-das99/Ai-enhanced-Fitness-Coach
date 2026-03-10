#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.core.database import get_db

with get_db() as db:
    cursor = db.cursor()
    cursor.execute('PRAGMA table_info(health_activities)')
    print("health_activities schema:")
    for row in cursor.fetchall():
        print(f"  {dict(row)}")
