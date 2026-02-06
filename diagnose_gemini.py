#!/usr/bin/env python3
"""
Comprehensive Gemini API Diagnostic Tool
"""

import google.generativeai as genai
from config import GEMINI_API_KEY, LLM_MODEL
import json

def diagnose_gemini_api():
    """Comprehensive diagnosis of Gemini API issues"""
    
    print("🔍 Gemini API Diagnostic Tool")
    print("=" * 60)
    
    # Test 1: API Key and Configuration
    print("\n1. API Key & Configuration:")
    if not GEMINI_API_KEY:
        print("   ❌ No API key found")
        return
    
    print(f"   ✅ API Key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    print(f"   📋 Model: {LLM_MODEL}")
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(LLM_MODEL)
        print("   ✅ Model initialized successfully")
    except Exception as e:
        print(f"   ❌ Model initialization failed: {e}")
        return
    
    # Test 2: Simple API Call
    print("\n2. Basic API Test:")
    try:
        response = model.generate_content("Hello")
        print(f"   ✅ Basic call successful")
        print(f"   📄 Response: {response.text[:50]}...")
    except Exception as e:
        print(f"   ❌ Basic call failed: {e}")
        return
    
    # Test 3: Our Specific Prompt
    print("\n3. Our Wellness Prompt Test:")
    prompt = """Pick one wellness activity: breathing, meditation, stretching, take_break, short_walk

Context: afternoon, work hours
Answer with just one word:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=10,
                temperature=0.1,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        
        print(f"   ✅ Wellness prompt successful")
        print(f"   📄 Response: '{response.text.strip()}'")
        
        # Check response details
        if response.candidates:
            candidate = response.candidates[0]
            print(f"   🔍 Finish reason: {candidate.finish_reason}")
            print(f"   🔍 Safety ratings: {len(candidate.safety_ratings)} items")
            
            for rating in candidate.safety_ratings:
                print(f"      - {rating.category}: {rating.probability}")
        
    except Exception as e:
        print(f"   ❌ Wellness prompt failed: {e}")
        
        # Try to get more details about the failure
        try:
            response = model.generate_content(prompt)
            print(f"   🔍 Without safety settings: {response}")
        except Exception as e2:
            print(f"   ❌ Even without safety settings: {e2}")
    
    # Test 4: Alternative Simple Prompts
    print("\n4. Alternative Prompt Tests:")
    
    simple_prompts = [
        "Choose: breathing",
        "meditation",
        "Select one: breathing, meditation, stretching",
        "Pick: breathing or meditation",
        "breathing"
    ]
    
    for i, test_prompt in enumerate(simple_prompts, 1):
        try:
            response = model.generate_content(
                test_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=5,
                    temperature=0.0,
                )
            )
            print(f"   ✅ Test {i}: '{test_prompt}' → '{response.text.strip()}'")
        except Exception as e:
            print(f"   ❌ Test {i}: '{test_prompt}' → Failed: {e}")
    
    # Test 5: Check API Quotas
    print("\n5. API Quota Check:")
    try:
        # Make multiple quick calls to test rate limits
        for i in range(3):
            response = model.generate_content("Hi")
            print(f"   ✅ Call {i+1}: Success")
    except Exception as e:
        print(f"   ⚠️  Quota issue detected: {e}")
    
    # Test 6: Model Availability
    print("\n6. Available Models:")
    try:
        models = list(genai.list_models())
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"   📋 Available models: {len(available_models)}")
        
        if f"models/{LLM_MODEL}" in available_models:
            print(f"   ✅ Current model '{LLM_MODEL}' is available")
        else:
            print(f"   ❌ Current model '{LLM_MODEL}' not found")
            print(f"   💡 Try these instead: {available_models[:3]}")
            
    except Exception as e:
        print(f"   ❌ Could not list models: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Diagnosis Complete!")
    
    print("\n💡 Common Solutions:")
    print("1. If API key issues → Check https://aistudio.google.com/app/apikey")
    print("2. If safety filter issues → Try simpler prompts")
    print("3. If quota issues → Check billing at https://console.cloud.google.com/")
    print("4. If model issues → Try 'gemini-pro' or 'gemini-2.0-flash'")

if __name__ == "__main__":
    diagnose_gemini_api()