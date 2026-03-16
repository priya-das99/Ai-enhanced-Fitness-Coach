# Demo Reminders System

This system creates water reminders and challenge reminders for demonstration purposes. The reminders appear as system messages in the chat interface.

## Files Created

1. **`demo_reminders.py`** - Main script with reminder functionality
2. **`test_demo_reminders.py`** - Test script for quick testing
3. **API endpoints** - Added to `chat.py` for web interface integration
4. **Frontend buttons** - Added to `index.html` and `chat.js`

## Usage Methods

### 1. Command Line Usage

```bash
# Send both water and challenge reminders
python demo_reminders.py

# Send only water reminder
python demo_reminders.py --water-only

# Send only challenge reminder  
python demo_reminders.py --challenge-only

# Clear recent demo notifications
python demo_reminders.py --clear

# Show user's current challenges
python demo_reminders.py --show-challenges

# Setup demo data only (without sending reminders)
python demo_reminders.py --setup-only

# Specify different user ID (default is 1)
python demo_reminders.py --user-id 2
```

### 2. Quick Test Script

```bash
# Run full test
python test_demo_reminders.py

# Quick regenerate reminders
python test_demo_reminders.py quick
```

### 3. Web Interface (Recommended for Demo)

When logged into the chat interface, you'll see demo control buttons at the bottom:

- **💧 Water Reminder** - Sends a water reminder notification
- **🎯 Challenge Reminder** - Sends a challenge reminder notification  
- **🚀 Both Reminders** - Sends both types of reminders
- **Hide Demo** - Toggles visibility of demo buttons

### 4. API Endpoints

- `POST /api/v1/chat/demo/water-reminder` - Send water reminder
- `POST /api/v1/chat/demo/challenge-reminder` - Send challenge reminder
- `POST /api/v1/chat/demo/reminders` - Send both reminders

## How It Works

1. **Setup Demo Data**: Creates sample challenges (water, exercise, sleep) and joins the user to some of them with partial progress
2. **Generate Reminders**: Creates randomized reminder messages with action buttons
3. **Store Notifications**: Saves reminders in the database and as chat messages
4. **Display in Chat**: Reminders appear as system messages in the chat interface

## Demo Features

- **Randomized Messages**: Each reminder type has multiple message variations
- **Action Buttons**: Reminders include interactive buttons (for future functionality)
- **Progress Tracking**: Challenge reminders show actual progress from demo data
- **Clean Regeneration**: Can clear previous demo notifications and generate fresh ones

## Demo Data Created

- **7-Day Water Challenge** (42.8% complete, 3 days in)
- **14-Day Exercise Challenge** (21.4% complete, 1 day in)  
- **21-Day Sleep Challenge** (available to join)

## For Demo Presentation

1. **Show Initial State**: Open chat to show normal conversation
2. **Trigger Reminders**: Click "🚀 Both Reminders" button
3. **Show Results**: Refresh page to see reminder notifications in chat
4. **Regenerate**: Click buttons again to show different reminder variations
5. **Explain System**: Show how reminders would work in real-time with scheduling

## Customization

To modify reminder messages, edit the arrays in `demo_reminders.py`:
- `water_reminders` - Water reminder message variations
- `challenge_reminders` - Challenge reminder message variations

To add new challenge types, modify the `demo_challenges` array in `setup_demo_data()`.