# chat_assistant/domain/llm/suggestion_ranker.py
# LLM-based suggestion ranking using centralized LLM service

import json
import logging
from typing import List, Dict, Any, Optional
from chat_assistant.llm_service import get_llm_service, LLMUnavailableError, LLMAPIError

logger = logging.getLogger(__name__)

class SuggestionRanker:
    """
    Uses centralized LLM service to rank top suggestions from pre-scored candidates.
    
    Phase 3: LLM ONLY ranks, does NOT score
    - Receives pre-scored candidates (top 5)
    - Reorders them based on context
    - Does NOT see entire suggestion pool
    - Business logic stays deterministic
    
    IMPORTANT: LLM can only select from provided suggestions by ID.
    It cannot invent new suggestions.
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def rank_suggestions(
        self,
        candidates: List[Dict[str, Any]],
        mood_emoji: str,
        reason: Optional[str],
        context: Dict[str, Any],
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Rank suggestions using LLM.
        
        Args:
            candidates: Pre-scored list of suggestions (with 'score' field)
            mood_emoji: User's mood emoji
            reason: Reason for mood
            context: Context dict
            top_n: Number of suggestions to return
            
        Returns:
            Top N suggestions ranked by LLM (or by score if LLM unavailable)
        """
        if len(candidates) <= top_n:
            # Not enough candidates to rank
            return candidates[:top_n]
        
        try:
            # Take top 5 candidates by score for LLM to choose from
            top_candidates = candidates[:min(5, len(candidates))]
            
            # Build prompt
            prompt = self._build_prompt(top_candidates, mood_emoji, reason, context, top_n)
            
            # Call LLM service with structured JSON schema
            schema = {
                "type": "object",
                "properties": {
                    "ranked_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of activity IDs in ranked order"
                    }
                },
                "required": ["ranked_ids"],
                "additionalProperties": False
            }
            
            result = self.llm_service.call_structured(
                prompt=prompt,
                json_schema=schema,
                schema_name="suggestion_ranking",
                system_message="You are a wellness suggestion ranking system.",
                temperature=0.2,  # Low temperature for deterministic ranking
                max_tokens=100
            )
            
            # Extract ranked IDs from structured response
            selected_ids = result.get('ranked_ids', [])
            
            if not selected_ids:
                logger.warning("LLM returned empty ranked_ids")
                return candidates[:top_n]
            
            if selected_ids:
                # Reorder candidates based on LLM selection
                ranked = []
                for suggestion_id in selected_ids[:top_n]:
                    for candidate in top_candidates:
                        if candidate.get('id') == suggestion_id or candidate.get('suggestion_key') == suggestion_id:
                            ranked.append(candidate)
                            break
                
                # Fill remaining slots with score-based ranking
                while len(ranked) < top_n and len(ranked) < len(candidates):
                    for candidate in candidates:
                        if candidate not in ranked:
                            ranked.append(candidate)
                            break
                
                logger.info(f"🤖 LLM ranked suggestions: {[s.get('id') or s.get('suggestion_key') for s in ranked]}")
                return ranked[:top_n]
            
            # Fallback to score-based ranking
            return candidates[:top_n]
            
        except (LLMUnavailableError, LLMAPIError) as e:
            logger.warning(f"LLM unavailable, using score-based ranking: {e}")
            return candidates[:top_n]
        except Exception as e:
            logger.error(f"LLM ranking failed: {e}")
            return candidates[:top_n]
    
    def _build_prompt(
        self,
        candidates: List[Dict[str, Any]],
        mood_emoji: str,
        reason: Optional[str],
        context: Dict[str, Any],
        top_n: int
    ) -> str:
        """Build strict ranking prompt for suggestion reordering"""

        candidate_list = []
        for candidate in candidates:
            suggestion_id = candidate.get('id') or candidate.get('suggestion_key')
            name = candidate.get('name') or candidate.get('title')
            description = candidate.get('description', '')
            score = round(candidate.get('score', 0), 3)

            candidate_list.append(
                f"- ID: {suggestion_id} | Name: {name} | Description: {description} | BaseScore: {score}"
            )

        candidates_text = "\n".join(candidate_list)

        time_info = context.get('time_period', 'day')
        if context.get('is_work_hours'):
            time_info += " (work hours)"

        prompt = f"""
You are a deterministic ranking engine.

Your task:
Reorder the provided activity IDs based on contextual suitability.

IMPORTANT RULES:
- You MUST select ONLY from the provided IDs.
- You CANNOT invent new IDs.
- You MUST return exactly {top_n} IDs.
- Do NOT include explanations.
- Do NOT return extra text.
- Respect BaseScore — higher score generally means better baseline relevance.

User Context:
Mood: {mood_emoji}
Reason: {reason or "not specified"}
Time: {time_info}

Activities to rank:
{candidates_text}

Ranking Principles:

1. Relevance to mood and reason comes first.
2. Practical feasibility (work hours constraint).
3. Avoid repetitive type clustering (e.g., all breathing/meditation).
4. Prefer diversity in activity type if scores are close.
5. If BaseScore difference is large (>0.15), do NOT override it unless clearly inappropriate.
6. If mood indicates high stress, prioritize calming or restorative activities.
7. If mood indicates low energy, prioritize light or restorative actions.
8. Maintain variety but do NOT sacrifice strong contextual match.

Tie-break rule:
If two options seem equal, choose the one with higher BaseScore.

Return JSON ONLY in this format:
{{
  "ranked_ids": ["id1", "id2", "id3"]
}}

No explanation.
"""

        return prompt
    
    def _parse_llm_response(self, content: str) -> List[str]:
        """Parse LLM response to extract suggestion IDs"""
        try:
            # Try to parse as JSON array
            if content.startswith('[') and content.endswith(']'):
                return json.loads(content)
            
            # Try to find JSON array in text
            start = content.find('[')
            end = content.rfind(']')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        return []


# Global instance
_suggestion_ranker = None

def get_suggestion_ranker() -> SuggestionRanker:
    """Get or create global SuggestionRanker instance"""
    global _suggestion_ranker
    if _suggestion_ranker is None:
        _suggestion_ranker = SuggestionRanker()
    return _suggestion_ranker
