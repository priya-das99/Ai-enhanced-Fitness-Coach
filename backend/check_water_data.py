#!/usr/bin/env python3
"""Check water data for user"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from datetime import datetime, date

def check_water_data():
    with get_db() as db:
        cursor = db.cursor()
        
        # Get today's water intake for user 1
        today = date.today().isoformat()
        
        cursor.execute("""
            SELECT * FROM health_activities 
            WHERE user_id=1 
            AND activity_type='water'
            AND DATE(created_at) = ?
            ORDER BY created_at DESC
        """, (today,))
        
        rows = cursor.fetchall()
        
        print(f"Water entries for user 1 today ({today}):")
        print(f"Found {len(rows)} entries")
        
        total = 0
        for row in rows:
            print(f"  - Value: {row['value']} {row['unit']} at {row['created_at']}")
            total += row['value']
        
        print(f"\nTotal water today: {total}")
        
        # Check challenge for water
        cursor.execute("""
            SELECT * FROM challenges 
            WHERE challenge_type='water'
            LIMIT 1
        """)
        
        challenge = cursor.fetchone()
        if challenge:
            print(f"\nWater challenge:")
            print(f"  - Title: {challenge['title']}")
            print(f"  - Target: {challenge['target_value']} {challenge['target_unit']}")
            print(f"  - Duration: {challenge['duration_days']} days")

if __name__ == "__main__":
    check_water_data()
