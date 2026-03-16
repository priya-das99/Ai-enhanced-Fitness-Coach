#!/usr/bin/env python3
"""
Demo Reminders Script
Creates water reminders and challenge reminders for demonstration purposes.
Can be run to generate sample notifications that appear in the chat.
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import random

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.notification_service import get_notification_service
from app.services.challenge_service import ChallengeService
from app.core.database import get_db

class DemoReminderScript:
    def __init__(self):
        self.notification_service = get_notification_service()
        self.challenge_service = ChallengeService()
    
    def setup_demo_data(self, user_id: int = 1):
        """Setup demo challenges and user data"""
        with get_db() as db:
            cursor = db.cursor()
            
            # Create demo challenges if they don't exist
            demo_challenges = [
                {
                    'title': '7-Day Water Challenge',
                    'description': 'Drink 8 glasses of water daily for 7 days',
                    'challenge_type': 'water',
                    'duration_days': 7,
                    'points': 50,
                    'target_value': 8,
                    'target_unit': 'glasses'
                },
                {
                    'title': '14-Day Exercise Challenge',
                    'description': 'Exercise for at least 30 minutes daily for 14 days',
                    'challenge_type': 'exercise',
                    'duration_days': 14,
                    'points': 100,
                    'target_value': 30,
                    'target_unit': 'minutes'
                },
                {
                    'title': '21-Day Sleep Challenge',
                    'description': 'Get 8 hours of sleep daily for 21 days',
                    'challenge_type': 'sleep',
                    'duration_days': 21,
                    'points': 150,
                    'target_value': 8,
                    'target_unit': 'hours'
                }
            ]
            
            # Insert challenges
            for challenge in demo_challenges:
                cursor.execute('''
                    INSERT OR IGNORE INTO challenges 
                    (title, description, challenge_type, duration_days, points, target_value, target_unit, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    challenge['title'],
                    challenge['description'],
                    challenge['challenge_type'],
                    challenge['duration_days'],
                    challenge['points'],
                    challenge['target_value'],
                    challenge['target_unit']
                ))
            
            # Join user to water challenge (for demo)
            cursor.execute('''
                INSERT OR IGNORE INTO user_challenges (user_id, challenge_id, status, progress, joined_at)
                SELECT ?, c.id, 'active', 42.8, ?
                FROM challenges c 
                WHERE c.challenge_type = 'water'
                LIMIT 1
            ''', (user_id, datetime.now() - timedelta(days=3)))
            
            # Join user to exercise challenge (for demo)
            cursor.execute('''
                INSERT OR IGNORE INTO user_challenges (user_id, challenge_id, status, progress, joined_at)
                SELECT ?, c.id, 'active', 21.4, ?
                FROM challenges c 
                WHERE c.challenge_type = 'exercise'
                LIMIT 1
            ''', (user_id, datetime.now() - timedelta(days=1)))
            
            db.commit()
            print("✅ Demo challenges setup complete")
    
    def send_water_reminder(self, user_id: int = 1):
        """Send a water reminder notification"""
        water_reminders = [
            {
                'title': '💧 Hydration Check!',
                'message': "It's been a while since your last water intake. Remember to stay hydrated! Your body needs water to function at its best.",
                'type': 'reminder',
                'priority': 'normal',
                'action_buttons': [
                    {'text': '💧 Log Water', 'action': 'log_water'},
                    {'text': '⏰ Remind Later', 'action': 'snooze_reminder'}
                ]
            },
            {
                'title': '🌊 Time for Water!',
                'message': "Your body is calling for hydration! Drinking water now will help you feel more energized and focused.",
                'type': 'reminder',
                'priority': 'normal',
                'action_buttons': [
                    {'text': '💧 Drink Water', 'action': 'log_water'},
                    {'text': '📊 View Progress', 'action': 'view_water_stats'}
                ]
            },
            {
                'title': '💦 Hydration Reminder',
                'message': "Don't forget to drink water! Staying hydrated helps with concentration, energy levels, and overall health.",
                'type': 'reminder',
                'priority': 'normal',
                'action_buttons': [
                    {'text': '💧 Log Glass', 'action': 'log_water'},
                    {'text': '🎯 View Challenge', 'action': 'view_challenges'}
                ]
            }
        ]
        
        reminder = random.choice(water_reminders)
        self.notification_service.send_notification(user_id, reminder)
        print(f"💧 Water reminder sent to user {user_id}")
        return reminder
    
    def send_challenge_reminder(self, user_id: int = 1):
        """Send a challenge reminder notification"""
        # Get user's active challenges
        challenges = self.challenge_service.get_user_challenges(user_id)
        
        if not challenges:
            # Send generic challenge invitation
            reminder = {
                'title': '🎯 Ready for a Challenge?',
                'message': "Join a wellness challenge to stay motivated and earn points! Challenges help you build healthy habits consistently.",
                'type': 'reminder',
                'priority': 'normal',
                'action_buttons': [
                    {'text': '🎯 Browse Challenges', 'action': 'view_challenges'},
                    {'text': '💪 Join Challenge', 'action': 'join_challenge'}
                ]
            }
        else:
            # Send reminder about active challenges
            challenge = random.choice(challenges)
            days_left = challenge['duration_days'] - challenge['days_completed']
            progress_percent = challenge['progress']
            
            challenge_reminders = [
                {
                    'title': f"🏆 {challenge['title']} Progress",
                    'message': f"You're {progress_percent:.1f}% through your {challenge['title']}! {days_left} days remaining. Keep up the great work!",
                    'type': 'reminder',
                    'priority': 'normal',
                    'action_buttons': [
                        {'text': '📊 View Progress', 'action': 'view_challenge_progress'},
                        {'text': '💪 Log Activity', 'action': f"log_{challenge['challenge_type']}"}
                    ]
                },
                {
                    'title': '🔥 Challenge Check-in',
                    'message': f"How's your {challenge['title']} going? You've completed {challenge['days_completed']} out of {challenge['duration_days']} days. You're doing amazing!",
                    'type': 'reminder',
                    'priority': 'normal',
                    'action_buttons': [
                        {'text': '✅ Mark Complete', 'action': f"log_{challenge['challenge_type']}"},
                        {'text': '📈 View Stats', 'action': 'view_challenge_stats'}
                    ]
                },
                {
                    'title': '🎯 Challenge Motivation',
                    'message': f"Don't give up on your {challenge['title']}! You're {challenge['days_completed']} days in and earning {challenge['points']} points when you complete it.",
                    'type': 'reminder',
                    'priority': 'normal',
                    'action_buttons': [
                        {'text': '💪 Continue', 'action': f"log_{challenge['challenge_type']}"},
                        {'text': '🏆 View Rewards', 'action': 'view_points'}
                    ]
                }
            ]
            
            reminder = random.choice(challenge_reminders)
        
        self.notification_service.send_notification(user_id, reminder)
        print(f"🎯 Challenge reminder sent to user {user_id}")
        return reminder
    
    def send_both_reminders(self, user_id: int = 1):
        """Send both water and challenge reminders"""
        print(f"\n🚀 Sending demo reminders to user {user_id}...")
        
        # Setup demo data first
        self.setup_demo_data(user_id)
        
        # Send reminders
        water_reminder = self.send_water_reminder(user_id)
        challenge_reminder = self.send_challenge_reminder(user_id)
        
        print(f"\n✅ Demo reminders sent successfully!")
        print(f"💧 Water reminder: {water_reminder['title']}")
        print(f"🎯 Challenge reminder: {challenge_reminder['title']}")
        print(f"\n💬 Check your chat to see the notifications!")
        
        return {
            'water_reminder': water_reminder,
            'challenge_reminder': challenge_reminder
        }
    
    def clear_demo_notifications(self, user_id: int = 1):
        """Clear demo notifications for clean testing"""
        with get_db() as db:
            cursor = db.cursor()
            
            # Delete recent notifications
            cursor.execute('''
                DELETE FROM notifications 
                WHERE user_id = ? 
                AND created_at > datetime('now', '-1 hour')
            ''', (user_id,))
            
            # Delete recent chat messages from system
            cursor.execute('''
                DELETE FROM chat_messages 
                WHERE user_id = ? 
                AND sender = 'system'
                AND timestamp > datetime('now', '-1 hour')
            ''', (user_id,))
            
            db.commit()
            print(f"🧹 Cleared recent demo notifications for user {user_id}")
    
    def show_user_challenges(self, user_id: int = 1):
        """Show user's current challenges"""
        challenges = self.challenge_service.get_user_challenges(user_id)
        
        if not challenges:
            print(f"❌ No active challenges found for user {user_id}")
            return
        
        print(f"\n🎯 Active challenges for user {user_id}:")
        for challenge in challenges:
            print(f"  • {challenge['title']}")
            print(f"    Progress: {challenge['progress']:.1f}% ({challenge['days_completed']}/{challenge['duration_days']} days)")
            print(f"    Points: {challenge['points']}")
            print()


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Demo Reminders Script')
    parser.add_argument('--user-id', type=int, default=1, help='User ID to send reminders to')
    parser.add_argument('--water-only', action='store_true', help='Send only water reminder')
    parser.add_argument('--challenge-only', action='store_true', help='Send only challenge reminder')
    parser.add_argument('--clear', action='store_true', help='Clear recent demo notifications')
    parser.add_argument('--show-challenges', action='store_true', help='Show user challenges')
    parser.add_argument('--setup-only', action='store_true', help='Only setup demo data')
    
    args = parser.parse_args()
    
    script = DemoReminderScript()
    
    if args.clear:
        script.clear_demo_notifications(args.user_id)
        return
    
    if args.show_challenges:
        script.show_user_challenges(args.user_id)
        return
    
    if args.setup_only:
        script.setup_demo_data(args.user_id)
        return
    
    if args.water_only:
        script.setup_demo_data(args.user_id)
        script.send_water_reminder(args.user_id)
    elif args.challenge_only:
        script.setup_demo_data(args.user_id)
        script.send_challenge_reminder(args.user_id)
    else:
        script.send_both_reminders(args.user_id)


if __name__ == '__main__':
    main()