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
            
            demo_challenges = [
                ('Water Intake Challenge',    'Drink 8 glasses of water daily for 7 days',       'water',    7,  50,  8,  'glasses'),
                ('14-Day Exercise Challenge', 'Exercise for at least 30 minutes daily for 14 days','exercise',14, 100, 30, 'minutes'),
                ('Sleep 8 Hours Challenge',  'Get 8 hours of sleep daily for 21 days',           'sleep',   21, 150,  8, 'hours'),
            ]
            
            for title, desc, ctype, days, pts, target, unit in demo_challenges:
                # Only insert if this challenge_type doesn't already exist
                cursor.execute('SELECT id FROM challenges WHERE challenge_type = ? AND title = ? LIMIT 1', (ctype, title))
                row = cursor.fetchone()
                if not row:
                    cursor.execute('''
                        INSERT INTO challenges 
                        (title, description, challenge_type, duration_days, points, target_value, target_unit, is_active, start_date, end_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, date('now'), date('now', '+' || ? || ' days'))
                    ''', (title, desc, ctype, days, pts, target, unit, days))
            
            # Enroll user in all three challenge types if not already enrolled
            for ctype in ('water', 'exercise', 'sleep'):
                cursor.execute('''
                    SELECT uc.id FROM user_challenges uc
                    JOIN challenges c ON uc.challenge_id = c.id
                    WHERE uc.user_id = ? AND c.challenge_type = ? AND uc.status = 'active'
                    LIMIT 1
                ''', (user_id, ctype))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO user_challenges (user_id, challenge_id, status, progress, joined_at)
                        SELECT ?, c.id, 'active', 0, datetime('now', '-1 day')
                        FROM challenges c 
                        WHERE c.challenge_type = ? AND c.is_active = 1
                        LIMIT 1
                    ''', (user_id, ctype))
            
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
        """Send a challenge reminder based on user's active challenges and today's activity"""
        challenges = self.challenge_service.get_user_challenges(user_id)

        if not challenges:
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
            # Pick a challenge the user hasn't logged progress for today
            pending = self._get_pending_challenges_today(user_id, challenges)
            challenge = random.choice(pending) if pending else random.choice(challenges)

            days_left = challenge['duration_days'] - challenge['days_completed']
            progress_percent = challenge['progress']
            ctype = challenge['challenge_type']  # water, exercise, sleep, etc.

            # Build type-specific action buttons
            type_config = {
                'water':    {'emoji': '💧', 'log_label': '💧 Log Water',    'log_action': 'log_water'},
                'exercise': {'emoji': '🏃', 'log_label': '🏃 Log Exercise', 'log_action': 'log_exercise'},
                'sleep':    {'emoji': '😴', 'log_label': '😴 Log Sleep',    'log_action': 'log_sleep'},
                'mood':     {'emoji': '😊', 'log_label': '😊 Log Mood',     'log_action': 'log_mood'},
            }
            cfg = type_config.get(ctype, {'emoji': '💪', 'log_label': '✅ Log Activity', 'log_action': f'log_{ctype}'})

            templates = [
                {
                    'title': f"{cfg['emoji']} {challenge['title']} — Day Check",
                    'message': f"You're {progress_percent:.0f}% through your {challenge['title']}! {days_left} day(s) left. Have you logged today's {ctype}?",
                    'action_buttons': [
                        {'text': cfg['log_label'],       'action': cfg['log_action']},
                        {'text': '📊 View Progress',     'action': 'view_challenge_progress'},
                    ]
                },
                {
                    'title': f"🔥 Keep Your Streak — {challenge['title']}",
                    'message': f"You've completed {challenge['days_completed']} out of {challenge['duration_days']} days. Don't break the streak — log your {ctype} now!",
                    'action_buttons': [
                        {'text': cfg['log_label'],       'action': cfg['log_action']},
                        {'text': '⏰ Remind Later',      'action': 'snooze_reminder'},
                    ]
                },
                {
                    'title': f"🏆 {challenge['points']} Points Waiting — {challenge['title']}",
                    'message': f"You're {progress_percent:.0f}% there! Complete today's {ctype} goal to stay on track and earn your {challenge['points']} point reward.",
                    'action_buttons': [
                        {'text': cfg['log_label'],       'action': cfg['log_action']},
                        {'text': '📈 View Stats',        'action': 'view_challenge_stats'},
                    ]
                },
            ]

            chosen = random.choice(templates)
            reminder = {
                'title': chosen['title'],
                'message': chosen['message'],
                'type': 'reminder',
                'priority': 'normal',
                'action_buttons': chosen['action_buttons']
            }

        self.notification_service.send_notification(user_id, reminder)
        print(f"🎯 Challenge reminder sent to user {user_id}: {reminder['title']}")
        return reminder

    def _get_pending_challenges_today(self, user_id: int, challenges: list) -> list:
        """Return challenges where the user hasn't met today's target yet"""
        from app.repositories.challenge_repository import ChallengeRepository
        repo = ChallengeRepository()
        pending = []
        for ch in challenges:
            try:
                progress_today = repo.get_challenge_progress_today(user_id, ch['challenge_type'])
                if not progress_today or not progress_today.get('target_met'):
                    pending.append(ch)
            except Exception:
                pending.append(ch)
        return pending
    
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