#!/usr/bin/env python3
"""
Test challenge intent detection with user's actual queries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_assistant.domain.llm.intent_extractor import get_intent_extractor

def test_challenge_queries():
    """Test the exact queries from the user"""
    
    extractor = get_intent_extractor()
    
    test_queries = [
        "Did I meet my goals for water intake till now?",
        "How many glasses do I need to drink more today to complete today's challenge?",
        "What are the current challenges?",
        "what are the five challenges",
        "what is my progress"
    ]
    
    print("=" * 80)
    print("TESTING CHALLENGE INTENT DETECTION")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 80)
        
        result = extractor.extract_intent(query)
        
        print(f"✓ Primary Intent: {result['primary_intent']}")
        print(f"✓ Secondary Intent: {result.get('secondary_intent', 'none')}")
        print(f"✓ Confidence: {result.get('confidence', 'unknown')}")
        
        # Check if it's being classified correctly
        if result['primary_intent'] == 'challenges':
            print("✅ CORRECT - Classified as challenges")
        else:
            print(f"❌ WRONG - Should be 'challenges' but got '{result['primary_intent']}'")

if __name__ == "__main__":
    test_challenge_queries()
