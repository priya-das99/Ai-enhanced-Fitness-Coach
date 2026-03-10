# Proper Solution: LLM-Based Reason Extraction

## The Problem with Keyword Matching

**Current Approach:**
```python
REASON_MAPPING = {
    'stress': {'mood': '😟', 'reason': 'stress'},
    'anxiety': {'mood': '😰', 'reason': 'anxiety'},
    # ... 50+ keywords
}
```

**Why This Fails:**
- ❌ Can't handle variations: "gaining weight" vs "putting on pounds" vs "getting heavier"
- ❌ Can't understand context: "I'm stressed about my weight" → should be weight, not stress
- ❌ Requires endless keyword additions
- ❌ Doesn't scale to new use cases
- ❌ Brittle and maintenance-heavy

## The Right Solution: LLM-Based Extraction

### Use the LLM to Extract Intent & Reason

Instead of keyword matching, ask the LLM:
```
User said: "im gaining weight how to controll it"

Extract:
1. What is the user's primary concern? (weight_management, stress, sleep, etc.)
2. What mood emoji best represents this? (😟, 😊, 🤔, etc.)
```

### Implementation Approach

```python
def _extract_reason_with_llm(self, message: str) -> Dict[str, str]:
    """Use LLM to extract reason and mood from user message"""
    
    prompt = f"""You are analyzing a user's wellness query.

User said: "{message}"

Determine:
1. Primary concern category
2. Appropriate mood emoji

Categories:
- weight_management: weight gain/loss, diet, body image
- nutrition: food, eating, meals, calories
- exercise: workout, fitness, physical activity
- stress: stress, pressure, overwhelm
- anxiety: worry, nervousness, fear
- sleep: insomnia, tired, rest
- energy: fatigue, low energy, exhaustion
- mood: general mood, happiness, sadness
- focus: concentration, productivity
- calm: relaxation, peace
- general: unclear or multiple concerns

Respond in JSON:
{{
  "reason": "category_name",
  "mood": "emoji",
  "confidence": "high/medium/low"
}}
"""

    try:
        result = llm_service.call_structured(
            prompt=prompt,
            json_schema={
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "mood": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                },
                "required": ["reason", "mood", "confidence"]
            }
        )
        
        return {
            'mood': result['mood'],
            'reason': result['reason']
        }
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}, using fallback")
        return self._extract_reason_fallback(message)
```

## Benefits of LLM-Based Approach

### 1. Handles Any Input
```
"im gaining weight how to controll it" → weight_management
"putting on pounds lately" → weight_management
"my clothes don't fit anymore" → weight_management
"need to lose some weight" → weight_management
```

### 2. Understands Context
```
"I'm stressed about my weight" → weight_management (not stress)
"Can't sleep because of work" → sleep (not work stress)
"Feeling anxious about my diet" → nutrition (not anxiety)
```

### 3. No Maintenance Required
- New use cases work automatically
- No keyword list to maintain
- Handles typos and variations
- Understands natural language

### 4. Scalable
- Add new categories by just updating the prompt
- No code changes needed
- Works in multiple languages (if needed)

## Implementation Plan

### Step 1: Add LLM-Based Extraction Method
```python
# In activity_query_workflow.py

def _extract_reason(self, message: str) -> Dict[str, str]:
    """Extract reason and mood from message using LLM"""
    
    # Try LLM first
    if self.llm_service.is_available():
        return self._extract_reason_with_llm(message)
    
    # Fallback to keyword matching if LLM unavailable
    return self._extract_reason_fallback(message)
```

### Step 2: Keep Keyword Matching as Fallback
```python
def _extract_reason_fallback(self, message: str) -> Dict[str, str]:
    """Fallback keyword-based extraction (when LLM unavailable)"""
    message_lower = message.lower()
    
    # Keep existing REASON_MAPPING for fallback
    for keyword, mapping in self.REASON_MAPPING.items():
        if keyword in message_lower:
            return mapping
    
    return {'mood': '😊', 'reason': 'general'}
```

### Step 3: Expand Content Library
Ensure wellness content has activities for all categories:
- weight_management
- nutrition
- exercise
- stress
- anxiety
- sleep
- energy
- etc.

## Cost Considerations

**LLM Call Cost:**
- ~100 tokens per extraction
- ~$0.0001 per extraction (with gpt-4o-mini)
- For 1000 queries/day: ~$0.10/day = $3/month

**Worth it because:**
- ✅ Better user experience
- ✅ Handles all edge cases
- ✅ No maintenance burden
- ✅ Scales automatically

## Comparison

### Keyword Matching (Current)
```
Input: "im gaining weight how to controll it"
Process: Check 50+ keywords → No match → Default to 'general'
Output: Generic wellness activities ❌
Maintenance: High (add keywords constantly)
```

### LLM-Based (Proposed)
```
Input: "im gaining weight how to controll it"
Process: Ask LLM to categorize → "weight_management"
Output: Weight-specific activities ✅
Maintenance: Low (just update prompt)
```

## Conclusion

**Stop fighting natural language with keywords.**

Use the LLM to understand what the user actually wants, then use your smart suggestion system to provide personalized activities.

This is what LLMs are designed for - understanding intent and context.
