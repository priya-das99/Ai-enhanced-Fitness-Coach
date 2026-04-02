"""
LLM Service with Token Tracking
Wraps the existing LLM service to automatically track all calls
"""
import time
from typing import Optional, Dict, Any, List
from chat_assistant.llm_service import LLMService, get_llm_service
from app.services.llm_token_tracker import LLMTokenTracker
import logging

logger = logging.getLogger(__name__)

class LLMServiceWithTracking:
    """
    Wrapper around LLMService that automatically tracks token usage
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.encoding = None
        try:
            # Try to import tiktoken for accurate token counting
            import tiktoken
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            logger.info("✅ Using tiktoken for accurate token counting")
        except ImportError:
            logger.warning("⚠️  tiktoken not installed, using approximate token counting")
        except Exception as e:
            logger.warning(f"Could not initialize tokenizer: {e}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except:
                pass
        # Fallback: rough estimate (1 token ≈ 4 characters)
        # This is approximate but good enough for tracking
        return max(1, len(text) // 4)
    
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4  # Overhead per message
        total += 2  # Overhead for message list
        return total
    
    def call(
        self,
        prompt: str = None,
        system_message: str = "You are a helpful assistant in a wellness app.",
        max_tokens: int = 100,
        temperature: float = 0.3,
        messages: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None,
        call_type: str = "general"
    ) -> str:
        """
        Call LLM with automatic token tracking
        
        Args:
            prompt: User prompt
            system_message: System message
            max_tokens: Max output tokens
            temperature: Temperature
            messages: Full message list (overrides prompt/system_message)
            user_id: User ID for tracking
            call_type: Type of call for analytics
        
        Returns:
            Response text
        """
        start_time = time.time()
        
        # Count input tokens
        if messages:
            input_tokens = self.count_message_tokens(messages)
        else:
            input_tokens = self.count_tokens(system_message) + self.count_tokens(prompt or "")
        
        try:
            # Make the actual LLM call
            response = self.llm_service.call(
                prompt=prompt,
                system_message=system_message,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            # Count output tokens
            output_tokens = self.count_tokens(response)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log the call
            LLMTokenTracker.log_llm_call(
                user_id=user_id,
                call_type=call_type,
                model=self.llm_service.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
                context_data={
                    "prompt_preview": (prompt or "")[:100] if prompt else None,
                    "response_preview": response[:100]
                }
            )
            
            return response
            
        except Exception as e:
            # Log failed call
            latency_ms = int((time.time() - start_time) * 1000)
            LLMTokenTracker.log_llm_call(
                user_id=user_id,
                call_type=call_type,
                model=self.llm_service.model,
                input_tokens=input_tokens,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e)
            )
            raise
    
    def call_structured(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        schema_name: str = "response",
        system_message: str = "You are a helpful assistant in a wellness app.",
        temperature: float = 0.2,
        max_tokens: int = 200,
        user_id: Optional[int] = None,
        call_type: str = "structured"
    ) -> Dict[str, Any]:
        """
        Call LLM for structured output with tracking
        """
        start_time = time.time()
        
        # Count input tokens
        input_tokens = self.count_tokens(system_message) + self.count_tokens(prompt)
        input_tokens += len(str(json_schema)) // 4  # Rough estimate for schema
        
        try:
            # Make the actual LLM call
            response = self.llm_service.call_structured(
                prompt=prompt,
                json_schema=json_schema,
                schema_name=schema_name,
                system_message=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Count output tokens
            output_tokens = self.count_tokens(str(response))
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log the call
            LLMTokenTracker.log_llm_call(
                user_id=user_id,
                call_type=call_type,
                model=self.llm_service.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
                context_data={
                    "prompt_preview": prompt[:100],
                    "schema_name": schema_name
                }
            )
            
            return response
            
        except Exception as e:
            # Log failed call
            latency_ms = int((time.time() - start_time) * 1000)
            LLMTokenTracker.log_llm_call(
                user_id=user_id,
                call_type=call_type,
                model=self.llm_service.model,
                input_tokens=input_tokens,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e)
            )
            raise

# Global instance
_tracked_llm_service: Optional[LLMServiceWithTracking] = None

def get_tracked_llm_service() -> LLMServiceWithTracking:
    """Get the tracked LLM service instance"""
    global _tracked_llm_service
    if _tracked_llm_service is None:
        _tracked_llm_service = LLMServiceWithTracking()
    return _tracked_llm_service
