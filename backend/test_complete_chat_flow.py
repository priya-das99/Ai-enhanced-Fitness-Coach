#!/usr/bin/env python3
"""
Complete chat flow test - registration -> login -> chat init -> messaging
Run this test after deployment to verify everything works end-to-end
"""

import requests
import time
import json

def test_complete_chat_flow(base_url="https://ai-enhanced-fitness-coach.onrender.com"):
    """Test the complete chat flow"""
    
    # Create unique test user
    timestamp = int(time.time())
    test_user = {
        "username": f"chat_test_{timestamp}",
        "email": f"chat_test_{timestamp}@test.com",
        "password": "test123456",
        "full_name": "Chat Test User"
    }
    
    print(f"🚀 Testing Complete Chat Flow")
    print(f"Base URL: {base_url}")
    print(f"Test user: {test_user['username']}")
    print("=" * 60)
    
    try:
        # Step 1: Registration
        print("\n1️⃣ Testing Registration...")
        reg_response = requests.post(f"{base_url}/api/v1/auth/register", json=test_user, timeout=30)
        
        if reg_response.status_code == 201:
            print("✅ Registration successful")
            reg_data = reg_response.json()
            user_id = reg_data.get('user_id')
            print(f"   User ID: {user_id}")
        else:
            print(f"❌ Registration failed: {reg_response.status_code}")
            print(f"   Response: {reg_response.text}")
            return False
        
        # Step 2: Login
        print("\n2️⃣ Testing Login...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=30)
        
        if login_response.status_code == 200:
            print("✅ Login successful")
            login_result = login_response.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"   Token received: {token[:20]}...")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
        
        # Step 3: Chat Initialization
        print("\n3️⃣ Testing Chat Initialization...")
        chat_init_response = requests.get(f"{base_url}/api/v1/chat/init", headers=headers, timeout=30)
        
        if chat_init_response.status_code == 200:
            print("✅ Chat initialization successful!")
            init_data = chat_init_response.json()
            print(f"   Message: {init_data.get('message', 'No message')}")
            print(f"   UI Elements: {init_data.get('ui_elements', [])}")
            print(f"   Activity Options: {len(init_data.get('activity_options', []))} options")
            print(f"   State: {init_data.get('state', 'unknown')}")
        else:
            print(f"❌ Chat initialization failed: {chat_init_response.status_code}")
            print(f"   Response: {chat_init_response.text}")
            return False
        
        # Step 4: Test Chat Messages Endpoint
        print("\n4️⃣ Testing Chat Messages Endpoint...")
        messages_response = requests.get(f"{base_url}/api/v1/chat/messages", headers=headers, timeout=30)
        
        if messages_response.status_code == 200:
            print("✅ Chat messages endpoint working")
            messages_data = messages_response.json()
            print(f"   Initial messages count: {len(messages_data.get('messages', []))}")
        else:
            print(f"❌ Chat messages failed: {messages_response.status_code}")
            print(f"   Response: {messages_response.text}")
            return False
        
        # Step 5: Test Actual Chat Messaging
        print("\n5️⃣ Testing Chat Messaging...")
        
        # Test messages to send
        test_messages = [
            "Hello!",
            "😊",  # Mood emoji
            "I want to log some water",
            "3"    # Follow-up response
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   5.{i} Sending message: '{message}'")
            
            message_data = {"message": message}
            msg_response = requests.post(
                f"{base_url}/api/v1/chat/message", 
                json=message_data, 
                headers=headers, 
                timeout=30
            )
            
            if msg_response.status_code == 200:
                print("   ✅ Message sent successfully")
                response_data = msg_response.json()
                bot_message = response_data.get('message', 'No response')
                ui_elements = response_data.get('ui_elements', [])
                state = response_data.get('state', 'unknown')
                
                print(f"   📤 Bot response: {bot_message[:100]}{'...' if len(bot_message) > 100 else ''}")
                print(f"   🎛️  UI Elements: {ui_elements}")
                print(f"   📊 State: {state}")
                
                # Small delay between messages
                time.sleep(1)
            else:
                print(f"   ❌ Message failed: {msg_response.status_code}")
                print(f"   Response: {msg_response.text}")
                return False
        
        # Step 6: Check Final Message History
        print("\n6️⃣ Checking Final Message History...")
        final_messages_response = requests.get(f"{base_url}/api/v1/chat/messages", headers=headers, timeout=30)
        
        if final_messages_response.status_code == 200:
            final_messages_data = final_messages_response.json()
            final_count = len(final_messages_data.get('messages', []))
            print(f"✅ Final message count: {final_count}")
            
            # Show last few messages
            messages = final_messages_data.get('messages', [])
            if messages:
                print("   📝 Recent messages:")
                for msg in messages[-4:]:  # Show last 4 messages
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('message', 'No content')
                    timestamp = msg.get('timestamp', 'No time')
                    print(f"      {sender}: {content[:50]}{'...' if len(content) > 50 else ''}")
        else:
            print(f"❌ Final message check failed: {final_messages_response.status_code}")
        
        print(f"\n{'='*60}")
        print("🎉 COMPLETE CHAT FLOW TEST PASSED!")
        print("✅ Registration ✅ Login ✅ Chat Init ✅ Messaging ✅ History")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server might be slow or down")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server might be down")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            success = test_complete_chat_flow("http://localhost:8000")
        elif sys.argv[1] == "deployment":
            success = test_complete_chat_flow("https://ai-enhanced-fitness-coach.onrender.com")
        else:
            print("Usage: python test_complete_chat_flow.py [local|deployment]")
            sys.exit(1)
    else:
        # Default to deployment test
        success = test_complete_chat_flow()
    
    if not success:
        sys.exit(1)