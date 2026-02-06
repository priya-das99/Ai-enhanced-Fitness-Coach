#!/usr/bin/env python3
"""
OpenAI API Diagnostic Tool
"""

import openai
from config import OPENAI_API_KEY, LLM_MODEL
import json
import os

def diagnose_openai_api():
    """Comprehensive diagnosis of OpenAI API issues"""
    
    print("🔍 OpenAI API Diagnostic Tool")
    print("=" * 60)
    
    # Test 1: API Key and Configuration
    print("\n1. API Key & Configuration:")
    if not OPENAI_API_KEY:
        print("   ❌ No API key found")
        return
    
    print(f"   ✅ API Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
    print(f"   📋 Model from config: {LLM_MODEL}")
    print(f"   📋 Model from env: {os.getenv('LLM_MODEL', 'not set')}")
    
    try:
        openai.api_key = OPENAI_API_KEY
        print("   ✅ API key configured successfully")
    except Exception as e:
        print(f"   ❌ API key configuration failed: {e}")
        return
    
    # Test different models
    models_to_test = [LLM_MODEL, 'gpt-4o-mini', 'gpt-3.5-turbo']
    
    for model in models_to_test:
        print(f"\n2. Testing Model: {model}")
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print(f"   ✅ {model} call successful")
            print(f"   📄 Response: {response.choices[0].message.content}")
            
            # If successful, test our wellness prompt
            print(f"\n3. Wellness Prompt Test with {model}:")
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful wellness assistant. Always respond with exactly one word from the given options."},
                    {"role": "user", "content": "Choose one: breathing, meditation, stretching"}
                ],
                max_tokens=5,
                temperature=0.3
            )
            print(f"   ✅ Wellness prompt successful with {model}")
            print(f"   📄 Response: '{response.choices[0].message.content.strip()}'")
            break
            
        except Exception as e:
            print(f"   ❌ {model} failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Diagnosis Complete!")
    
    print("\n💡 Solutions:")
    print("1. Add credits: https://platform.openai.com/account/billing")
    print("2. Check usage: https://platform.openai.com/account/usage")
    print("3. Try different model if one works")

if __name__ == "__main__":
    diagnose_openai_api()