#!/usr/bin/env python3
"""
Test script for demo reminders
Quick way to test and regenerate reminders for demo purposes
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from demo_reminders import DemoReminderScript

def test_reminders():
    """Test the reminder system"""
    print("🧪 Testing Demo Reminder System")
    print("=" * 50)
    
    script = DemoReminderScript()
    user_id = 1  # Default test user
    
    try:
        # Clear any existing demo notifications
        print("1. Clearing previous demo notifications...")
        script.clear_demo_notifications(user_id)
        
        # Setup demo data
        print("2. Setting up demo challenges...")
        script.setup_demo_data(user_id)
        
        # Show current challenges
        print("3. Current user challenges:")
        script.show_user_challenges(user_id)
        
        # Send water reminder
        print("4. Sending water reminder...")
        water_reminder = script.send_water_reminder(user_id)
        
        # Send challenge reminder
        print("5. Sending challenge reminder...")
        challenge_reminder = script.send_challenge_reminder(user_id)
        
        print("\n" + "=" * 50)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("\n📱 Notifications sent:")
        print(f"💧 Water: {water_reminder['title']}")
        print(f"🎯 Challenge: {challenge_reminder['title']}")
        print("\n💬 Check your chat interface to see the notifications!")
        print("\n🔄 To regenerate reminders, run this script again.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_regenerate():
    """Quickly regenerate reminders for demo"""
    print("🔄 Regenerating Demo Reminders...")
    
    script = DemoReminderScript()
    user_id = 1
    
    try:
        # Clear and send new reminders
        script.clear_demo_notifications(user_id)
        result = script.send_both_reminders(user_id)
        
        print("\n✅ Reminders regenerated!")
        print("💬 Check your chat to see the new notifications!")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed to regenerate: {e}")
        return None

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_regenerate()
    else:
        test_reminders()