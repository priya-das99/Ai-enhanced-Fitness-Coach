#!/usr/bin/env python3
"""
Test script for LLM integration
Run this to test the LLM service without starting the full Flask app
"""

import os
from llm_service import llm_service

def test_llm_service():
    """Test the LLM service functionality"""
    
    print("🧪 Testing LLM Integration (OpenAI)")
    print("=" * 50)
    
    # Test 1: Check configuration
    print("1. Configuration Check:")
    print(f"   - OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"   - LLM Enabled: {os.getenv('ENABLE_LLM', 'true')}")
    
    # Test 2: Test suggestion categories
    print("\n2. Available Suggestion Categories:")
    for cat_id, details in llm_service.suggestion_categories.items():
        print(f"   - {cat_id}: {details['description']} (effort: {details['effort']})")
    
    # Test 3: Test context info
    print("\n3. Current Context:")
    context = llm_service.get_context_info()
    for key, value in context.items():
        print(f"   - {key}: {value}")
    
    # Test 4: Test LLM selection (if API key available)
    print("\n4. LLM Selection Test:")
    if os.getenv('OPENAI_API_KEY'):
        try:
            suggestion = llm_service.select_suggestion_with_llm(
                mood="not good",
                reason="work_stress", 
                user_id="test_user"
            )
            print(f"   - LLM Result: {suggestion or 'No suggestion (fallback will be used)'}")
        except Exception as e:
            print(f"   - LLM Error: {e}")
    else:
        print("   - Skipped (no API key)")
    
    print("\n✅ Test completed!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env")
    print("2. Add your OpenAI API key to .env")
    print("3. Install requirements: pip install -r requirements.txt")
    print("4. Run the Flask app: python app.py")

if __name__ == "__main__":
    test_llm_service()