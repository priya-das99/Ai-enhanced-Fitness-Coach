#!/usr/bin/env python3
"""
Test HTTP Flow
Simulate the exact flow that happens during an HTTP request
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def simulate_auth_flow():
    """Simulate the authentication flow"""
    print("🔐 Simulating auth flow...")
    
    try:
        from app.services.auth_service import AuthService
        
        auth_service = AuthService()
        result = auth_service.login_user("demo", "demo123")
        
        print(f"✅ Login successful")
        print(f"   User ID: {result['user']['id']}")
        print(f"   User type: {type(result['user']['id'])}")
        
        return result['user']
        
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None

def simulate_chat_init(user):
    """Simulate the chat init with the authenticated user"""
    print(f"\n💬 Simulating chat init for user {user['id']}...")
    
    try:
        from app.services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # This is exactly what the endpoint does
        current_user = user  # This is what get_current_user returns
        response = chat_service.init_conversation(current_user['id'])
        
        print("✅ Chat init successful!")
        print(f"   Message: {response.get('message', 'N/A')[:50]}...")
        print(f"   UI Elements: {response.get('ui_elements', [])}")
        
        return response
        
    except Exception as e:
        print(f"❌ Chat init error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_direct_endpoint():
    """Test the endpoint logic directly"""
    print(f"\n🎯 Testing endpoint logic directly...")
    
    try:
        # Simulate what the endpoint does
        from app.api.deps import get_current_user
        from app.services.chat_service import ChatService
        
        # Mock current_user (what get_current_user would return)
        current_user = {
            'id': 1,
            'username': 'demo',
            'email': 'demo@example.com',
            'full_name': 'Demo User'
        }
        
        chat_service = ChatService()
        response = chat_service.init_conversation(current_user['id'])
        
        print("✅ Direct endpoint test successful!")
        print(f"   Response keys: {list(response.keys())}")
        
    except Exception as e:
        print(f"❌ Direct endpoint error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🧪 Testing HTTP Flow Simulation")
    print("=" * 50)
    
    # Step 1: Authenticate
    user = simulate_auth_flow()
    
    if user:
        # Step 2: Chat init with authenticated user
        simulate_chat_init(user)
    
    # Step 3: Test direct endpoint logic
    test_direct_endpoint()