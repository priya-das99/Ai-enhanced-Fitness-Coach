#!/usr/bin/env python3
"""
Check OpenAI Account Status
"""

import openai
import os
from dotenv import load_dotenv

load_dotenv()

def check_account_status():
    """Check OpenAI account and billing status"""
    
    print("🔍 OpenAI Account Status Check")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No API key found")
        return
    
    openai.api_key = api_key
    
    print(f"API Key: {api_key[:15]}...{api_key[-10:]}")
    print(f"Key Type: {'Project key' if 'proj' in api_key else 'Legacy key'}")
    
    # Try to get account information
    try:
        # Try to list models (this usually works even with quota issues)
        models = openai.Model.list()
        print(f"✅ API Key is valid - Found {len(models.data)} models")
        
        # Check if gpt-4o-mini is available
        available_models = [model.id for model in models.data]
        if 'gpt-4o-mini' in available_models:
            print("✅ gpt-4o-mini is available")
        else:
            print("⚠️  gpt-4o-mini not found, available models:")
            for model in available_models[:10]:  # Show first 10
                print(f"   - {model}")
        
    except Exception as e:
        print(f"❌ API Key validation failed: {e}")
        return
    
    # Try a minimal API call
    print(f"\n🧪 Testing Minimal API Call:")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Try the most basic model
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        print("✅ API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ API call failed: {error_msg}")
        
        if "quota" in error_msg.lower():
            print("\n💡 Quota Issue Detected:")
            print("1. Check your billing: https://platform.openai.com/account/billing")
            print("2. Check your usage: https://platform.openai.com/account/usage")
            print("3. Verify payment method is active")
            print("4. Check if you have any spending limits set")
        elif "invalid" in error_msg.lower():
            print("\n💡 API Key Issue:")
            print("1. Regenerate your API key")
            print("2. Make sure it's a project key (starts with sk-proj-)")
            print("3. Check key permissions")
    
    print(f"\n📋 Next Steps:")
    print("1. Visit https://platform.openai.com/account/billing")
    print("2. Ensure you have available credits")
    print("3. Check for any usage limits or restrictions")
    print("4. Try regenerating your API key if needed")

if __name__ == "__main__":
    check_account_status()