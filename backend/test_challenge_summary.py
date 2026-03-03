#!/usr/bin/env python3
"""Test challenge summary method"""

import sys
sys.path.insert(0, '.')

from app.services.challenge_service import ChallengeService

def test_summary():
    print("\n=== Testing Challenge Summary ===\n")
    
    service = ChallengeService()
    
    try:
        summary = service.get_challenges_summary(1)
        
        print(f"Active challenges: {len(summary['active_challenges'])}")
        print(f"Available challenges: {len(summary['available_challenges'])}")
        print(f"Total points: {summary['total_points']}")
        print(f"Challenges completed: {summary['challenges_completed']}")
        print(f"Current streak: {summary['current_streak']}")
        
        print("\nActive challenges:")
        for ch in summary['active_challenges']:
            print(f"  - {ch['title']}: {ch['progress']:.0f}%")
        
        print("\n✓ Challenge summary working!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_summary()
