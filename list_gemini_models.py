#!/usr/bin/env python3
"""
List available Gemini models
"""

import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("Available Gemini models:")
    print("=" * 40)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
        else:
            print(f"❌ {model.name} (not supported for generateContent)")
else:
    print("No Gemini API key found")