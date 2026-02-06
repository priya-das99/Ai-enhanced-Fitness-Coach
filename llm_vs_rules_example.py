#!/usr/bin/env python3
"""
Example showing LLM vs Pure Rules difference
"""

def pure_rule_based_selection(mood, reason):
    """Old way: Always same result"""
    if mood == "not good" and reason == "work_stress":
        return "breathing"  # Always breathing
    elif mood == "tired":
        return "meditation"  # Always meditation
    return "stretching"

def llm_enhanced_selection(mood, reason, context):
    """New way: Context-aware selection"""
    # LLM considers multiple factors:
    # - Time of day (morning = energizing, evening = calming)
    # - Work hours (work-friendly vs not)
    # - Recent suggestions (avoid repetition)
    # - User patterns
    
    if context["time"] == "morning" and context["work_hours"]:
        return "stretching"  # Energizing + work-friendly
    elif context["recent_suggestions"] == ["breathing", "breathing"]:
        return "take_break"  # Avoid repetition
    else:
        return "breathing"   # Default

# Example scenarios:
scenarios = [
    {"mood": "not good", "reason": "work_stress", "time": "morning", "work_hours": True, "recent": []},
    {"mood": "not good", "reason": "work_stress", "time": "morning", "work_hours": True, "recent": ["breathing"]},
    {"mood": "not good", "reason": "work_stress", "time": "evening", "work_hours": False, "recent": []},
]

print("🔍 LLM vs Rules Comparison")
print("=" * 50)

for i, scenario in enumerate(scenarios, 1):
    context = {"time": scenario["time"], "work_hours": scenario["work_hours"], "recent_suggestions": scenario["recent"]}
    
    rule_result = pure_rule_based_selection(scenario["mood"], scenario["reason"])
    llm_result = llm_enhanced_selection(scenario["mood"], scenario["reason"], context)
    
    print(f"\nScenario {i}: {scenario['mood']} + {scenario['reason']}")
    print(f"  Context: {scenario['time']}, work={scenario['work_hours']}, recent={scenario['recent']}")
    print(f"  🔧 Pure Rules: {rule_result}")
    print(f"  🤖 LLM Enhanced: {llm_result}")
    print(f"  💡 Difference: {'Same' if rule_result == llm_result else 'DIFFERENT - More contextual!'}")

print("\n" + "=" * 50)
print("🎯 Key Benefits of LLM Integration:")
print("1. Context awareness (time, work hours, history)")
print("2. Avoids repetitive suggestions")
print("3. Adapts to user patterns")
print("4. More intelligent selection")
print("5. Still uses safe, predefined content")