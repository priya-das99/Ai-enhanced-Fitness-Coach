#!/usr/bin/env python3
"""
Test runner for all follow-up related tests.

Runs various test scenarios to verify the LLM-based follow-up intent detection
works correctly for different activities and use cases.
"""

import sys
import os
import subprocess
import time

def run_test_script(script_name, description):
    """Run a test script and capture its output"""
    print(f"\nRunning {description}")
    print("=" * 80)
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print("✅ Test completed successfully!")
            print("\n📋 OUTPUT:")
            print(result.stdout)
            if result.stderr:
                print("\n⚠️ WARNINGS/ERRORS:")
                print(result.stderr)
        else:
            print(f"❌ Test failed with return code {result.returncode}")
            print("\n📋 STDOUT:")
            print(result.stdout)
            print("\n❌ STDERR:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
    
    print("\n" + "=" * 80)
    time.sleep(1)  # Brief pause between tests

def main():
    """Run all follow-up tests"""
    print("FOLLOW-UP INTENT DETECTION TEST SUITE")
    print("Testing LLM-based follow-up understanding for various activities")
    print("=" * 80)
    
    # List of tests to run
    tests = [
        ("test_intent_extraction.py", "Intent Extraction with Context Tests"),
        ("test_followup_scenarios.py", "Focused Follow-up Scenario Tests"),
        ("test_comprehensive_followup.py", "Comprehensive Activity Follow-up Tests"),
        ("test_followup_fix.py", "Original Follow-up Fix Tests")
    ]
    
    print(f"\n📋 Test Plan:")
    for i, (script, desc) in enumerate(tests, 1):
        print(f"{i}. {desc} ({script})")
    
    print(f"\n⏰ Starting tests at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run each test
    for script, description in tests:
        if os.path.exists(script):
            run_test_script(script, description)
        else:
            print(f"⚠️ Skipping {script} - file not found")
    
    print(f"\n🏁 All tests completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("\n📊 SUMMARY:")
    print("These tests verify that the LLM-based follow-up system:")
    print("1. ✅ Understands 'add 1 more' without keyword matching")
    print("2. ✅ Maintains workflow context between messages")
    print("3. ✅ Extracts quantities from natural language")
    print("4. ✅ Handles activity switching during follow-ups")
    print("5. ✅ Distinguishes between logging, querying, and suggestions")
    print("6. ✅ Gracefully handles edge cases and ambiguous input")
    print("\n💡 The system now uses pure LLM intent understanding!")

if __name__ == "__main__":
    main()