"""
Verify Prompt Refactoring
Ensures no inline prompts remain in workflow files
"""
import os
import re

def check_file_for_inline_prompts(filepath):
    """Check if file contains inline prompts"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern for inline prompts
    inline_prompt_pattern = r'prompt\s*=\s*f?"""'
    matches = re.findall(inline_prompt_pattern, content)
    
    return len(matches), matches

def check_file_for_phraser_usage(filepath):
    """Check if file uses phraser functions"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    phraser_functions = [
        'phrase_activity_suggestion',
        'phrase_contextual_suggestion',
        'phrase_empathetic_response'
    ]
    
    found = []
    for func in phraser_functions:
        if func in content:
            found.append(func)
    
    return found

def main():
    print("=" * 70)
    print("  🔍 VERIFYING PROMPT REFACTORING")
    print("=" * 70)
    
    # Files to check
    workflow_files = [
        'backend/chat_assistant/mood_workflow.py',
        'backend/chat_assistant/general_workflow.py',
        'backend/chat_assistant/activity_workflow.py'
    ]
    
    domain_files = [
        'backend/chat_assistant/domain/llm/response_phraser.py'
    ]
    
    all_good = True
    
    # Check workflow files for inline prompts
    print("\n📋 Checking workflow files for inline prompts...")
    print("-" * 70)
    
    for filepath in workflow_files:
        if not os.path.exists(filepath):
            print(f"⚠️  {filepath} - NOT FOUND")
            continue
        
        count, matches = check_file_for_inline_prompts(filepath)
        
        if count > 0:
            print(f"❌ {filepath}")
            print(f"   Found {count} inline prompt(s)")
            all_good = False
        else:
            print(f"✅ {filepath}")
            print(f"   No inline prompts found")
    
    # Check workflow files use phraser functions
    print("\n📋 Checking workflow files use phraser functions...")
    print("-" * 70)
    
    for filepath in workflow_files:
        if not os.path.exists(filepath):
            continue
        
        found = check_file_for_phraser_usage(filepath)
        
        if found:
            print(f"✅ {filepath}")
            print(f"   Uses: {', '.join(found)}")
        else:
            print(f"⚠️  {filepath}")
            print(f"   No phraser functions found (might not need them)")
    
    # Check domain layer has prompt functions
    print("\n📋 Checking domain layer has prompt functions...")
    print("-" * 70)
    
    for filepath in domain_files:
        if not os.path.exists(filepath):
            print(f"❌ {filepath} - NOT FOUND")
            all_good = False
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            'phrase_activity_suggestion',
            'phrase_contextual_suggestion',
            'phrase_empathetic_response'
        ]
        
        missing = []
        for func in required_functions:
            if f'def {func}(' not in content:
                missing.append(func)
        
        if missing:
            print(f"❌ {filepath}")
            print(f"   Missing: {', '.join(missing)}")
            all_good = False
        else:
            print(f"✅ {filepath}")
            print(f"   All required functions present")
    
    # Summary
    print("\n" + "=" * 70)
    print("  📊 SUMMARY")
    print("=" * 70)
    
    if all_good:
        print("✅ All checks passed!")
        print("\n🎉 Prompt refactoring is complete and correct!")
        print("\nBenefits:")
        print("  - Workflows are clean (orchestration only)")
        print("  - Prompts centralized in domain layer")
        print("  - Easy to test and maintain")
        print("  - Follows clean architecture")
    else:
        print("❌ Some checks failed!")
        print("\n⚠️  Please review the issues above")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
