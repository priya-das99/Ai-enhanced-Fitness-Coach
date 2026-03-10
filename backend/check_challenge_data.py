#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.core.database import get_db

with get_db() as db:
    cursor = db.cursor()
    cursor.execute('SELECT * FROM challenges WHERE challenge_type="water"')
    row = cursor.fetchone()
    if row:
        print("Water challenge:")
        print(dict(row))
    else:
        print("No water challenge found")
