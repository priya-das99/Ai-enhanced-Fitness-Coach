# app/api/v1/endpoints/chat.py
# Chat endpoints

from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatMessageRequest, ChatResponse, ChatHistoryResponse
from app.services.chat_service import ChatService
from app.api.deps import get_current_user
from typing import Dict
import time

router = APIRouter()
chat_service = ChatService()

@router.get("/init")
async def init_conversation(current_user: Dict = Depends(get_current_user)):
    """Initialize or resume conversation for logged-in user"""
    try:
        response = chat_service.init_conversation(current_user['id'])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process user message with comprehensive error handling, health monitoring, and per-user locking.
    
    Uses async lock to ensure messages from the same user are processed
    sequentially, preventing race conditions and workflow collisions.
    """
    from app.services.user_lock_manager import get_lock_manager
    from app.services.health_monitor import get_health_monitor
    import logging
    import sqlite3
    import asyncio
    
    logger = logging.getLogger(__name__)
    lock_manager = get_lock_manager()
    health_monitor = get_health_monitor()
    user_id = current_user['id']
    
    # Check circuit breaker
    if health_monitor.is_circuit_open():
        logger.warning("Circuit breaker is open - rejecting request")
        return {
            "response": "The system is temporarily unavailable for maintenance. Please try again in a few minutes.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "circuit_breaker"
        }
    
    # Check user rate limiting
    if health_monitor.should_rate_limit_user(user_id):
        logger.warning(f"Rate limiting user {user_id} due to repeated errors")
        return {
            "response": "You've encountered several errors recently. Please wait a moment before trying again.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "rate_limited"
        }
    
    # Get user-specific lock
    user_lock = lock_manager.get_lock(user_id)
    
    try:
        # Acquire lock - ensures sequential processing per user
        async with user_lock:
            logger.info(f"Processing message for user {user_id}: '{request.message[:50]}...'")
            
            # Add timeout to message processing
            response = await asyncio.wait_for(
                asyncio.to_thread(chat_service.process_message, user_id, request.message),
                timeout=25.0  # 25 second timeout for processing
            )
            
            # Reset user error count on success
            health_monitor.reset_user_errors(user_id)
            
            return response
            
    except asyncio.TimeoutError:
        # Processing timeout
        logger.error(f"Message processing timeout for user {user_id}")
        health_monitor.record_user_error(user_id, "timeout")
        health_monitor.record_system_error("processing_timeout")
        
        return {
            "response": "I'm taking longer than usual to process your request. Please try a simpler message or try again later.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "timeout"
        }
        
    except ValueError as e:
        # Workflow collision or validation error
        logger.warning(f"Validation error for user {user_id}: {e}")
        health_monitor.record_user_error(user_id, "validation")
        
        return {
            "response": "I'm still processing your previous request. Please wait a moment before sending another message.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "validation"
        }
        
    except sqlite3.OperationalError as e:
        # Database lock error
        logger.error(f"Database lock error for user {user_id}: {e}")
        health_monitor.record_user_error(user_id, "database")
        health_monitor.record_system_error("database_lock")
        
        return {
            "response": "The system is busy right now. Please try again in a moment.",
            "ui_elements": [],
            "state": "idle", 
            "error_type": "database_busy"
        }
        
    except ConnectionError as e:
        # Network/LLM service connection error
        logger.error(f"Connection error for user {user_id}: {e}")
        health_monitor.record_user_error(user_id, "connection")
        health_monitor.record_system_error("connection_error")
        
        return {
            "response": "I'm having trouble connecting to my AI service. Please try again in a moment.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "connection"
        }
        
    except Exception as e:
        # Unexpected error - log details but return friendly message
        logger.error(f"Unexpected error for user {user_id}: {e}", exc_info=True)
        health_monitor.record_user_error(user_id, "unexpected")
        health_monitor.record_system_error("unexpected_error")
        
        # Check if it's an LLM-related error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['openai', 'api', 'rate limit', 'quota', 'model']):
            return {
                "response": "I'm having trouble with my AI service right now. Please try a simpler message or try again later.",
                "ui_elements": [],
                "state": "idle",
                "error_type": "llm_service"
            }
        
        # Generic fallback
        return {
            "response": "Something went wrong while processing your message. Please try again with a different message.",
            "ui_elements": [],
            "state": "idle",
            "error_type": "unknown"
        }

@router.get("/history")
async def get_history(current_user: Dict = Depends(get_current_user)):
    """Get mood history for logged-in user"""
    try:
        logs = chat_service.get_history(current_user['id'])
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages")
async def get_chat_messages(
    limit: int = 100,
    current_user: Dict = Depends(get_current_user)
):
    """Get chat message history (all messages, used for history view)"""
    try:
        messages = chat_service.get_chat_messages(current_user['id'], limit)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/current-session")
async def get_current_session_messages(
    current_user: Dict = Depends(get_current_user)
):
    """Get messages from the current session only (used on chat open)"""
    try:
        messages = chat_service.get_current_session_messages(current_user['id'])
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Import suggestion tracker
from app.services.suggestion_interaction_tracker import SuggestionInteractionTracker
from pydantic import BaseModel

suggestion_tracker = SuggestionInteractionTracker()


class SuggestionActionRequest(BaseModel):
    """Request model for suggestion actions"""
    suggestion_key: str


@router.post("/suggestion/reject")
async def reject_suggestion(
    request: SuggestionActionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reject a suggestion
    
    This endpoint allows users to explicitly reject a suggestion,
    which helps improve personalization by tracking negative signals.
    """
    try:
        success = suggestion_tracker.track_rejected(
            user_id=current_user['id'],
            suggestion_key=request.suggestion_key
        )
        
        if success:
            return {
                "status": "rejected",
                "message": "Suggestion rejected successfully",
                "suggestion_key": request.suggestion_key
            }
        else:
            return {
                "status": "not_found",
                "message": "No recent suggestion found to reject",
                "suggestion_key": request.suggestion_key
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestion/accept")
async def accept_suggestion(
    request: SuggestionActionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Accept a suggestion
    
    This endpoint explicitly marks a suggestion as accepted.
    Note: Acceptance is also tracked automatically when user starts an activity.
    """
    try:
        success = suggestion_tracker.track_accepted(
            user_id=current_user['id'],
            suggestion_key=request.suggestion_key
        )
        
        if success:
            return {
                "status": "accepted",
                "message": "Suggestion accepted successfully",
                "suggestion_key": request.suggestion_key
            }
        else:
            return {
                "status": "not_found",
                "message": "No recent suggestion found to accept",
                "suggestion_key": request.suggestion_key
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ContentClickRequest(BaseModel):
    """Request model for content clicks"""
    content_id: str


@router.post("/content/click")
async def track_content_click(
    request: ContentClickRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Track when user clicks on wellness content (blog, video, podcast)
    """
    try:
        from chat_assistant.content_suggestions import track_content_click
        
        track_content_click(
            user_id=current_user['id'],
            content_id=request.content_id
        )
        
        return {
            "status": "tracked",
            "message": "Content click tracked successfully",
            "content_id": request.content_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout_user(current_user: Dict = Depends(get_current_user)):
    """
    Handle user logout - clear in-memory conversation state
    """
    try:
        from chat_assistant.unified_state import get_workflow_state
        
        # Clear in-memory state for this user
        workflow_state = get_workflow_state(current_user['id'])
        workflow_state.reset_on_logout()
        
        return {
            "status": "success",
            "message": "Logged out successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health(current_user: Dict = Depends(get_current_user)):
    """
    Get system health status (for debugging and monitoring)
    """
    try:
        from app.services.health_monitor import get_health_monitor
        from app.services.user_lock_manager import get_lock_manager
        
        health_monitor = get_health_monitor()
        lock_manager = get_lock_manager()
        
        health_status = health_monitor.get_health_status()
        lock_stats = lock_manager.get_stats()
        
        return {
            "status": "healthy" if not health_status['circuit_open'] else "degraded",
            "health": health_status,
            "locks": lock_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/reset")
async def reset_health_monitor(current_user: Dict = Depends(get_current_user)):
    """
    Reset health monitor (admin function)
    """
    try:
        from app.services.health_monitor import get_health_monitor
        
        health_monitor = get_health_monitor()
        health_monitor.force_circuit_close()
        
        return {
            "status": "success",
            "message": "Health monitor reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/reminders")
async def trigger_demo_reminders(current_user: Dict = Depends(get_current_user)):
    """Trigger demo reminders for testing purposes"""
    try:
        import sys
        import os
        
        # Add the backend directory to Python path for demo_reminders import
        backend_path = os.path.join(os.path.dirname(__file__), '../../../../')
        sys.path.append(backend_path)
        
        from demo_reminders import DemoReminderScript
        
        script = DemoReminderScript()
        user_id = current_user['id']
        
        # Clear previous demo notifications and send new ones
        script.clear_demo_notifications(user_id)
        result = script.send_both_reminders(user_id)
        
        return {
            "status": "success",
            "message": "Demo reminders sent successfully!",
            "reminders": {
                "water_reminder": result['water_reminder']['title'],
                "challenge_reminder": result['challenge_reminder']['title']
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send demo reminders: {str(e)}")

@router.post("/demo/water-reminder")
async def trigger_water_reminder(current_user: Dict = Depends(get_current_user)):
    """Trigger water reminder only"""
    try:
        import sys
        import os
        
        backend_path = os.path.join(os.path.dirname(__file__), '../../../../')
        sys.path.append(backend_path)
        
        from demo_reminders import DemoReminderScript
        
        script = DemoReminderScript()
        user_id = current_user['id']
        
        script.setup_demo_data(user_id)
        reminder = script.send_water_reminder(user_id)
        
        return {
            "status": "success",
            "message": "Water reminder sent!",
            "reminder": reminder['title']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send water reminder: {str(e)}")

@router.post("/demo/challenge-reminder")
async def trigger_challenge_reminder(current_user: Dict = Depends(get_current_user)):
    """Trigger challenge reminder only"""
    try:
        import sys
        import os
        
        backend_path = os.path.join(os.path.dirname(__file__), '../../../../')
        sys.path.append(backend_path)
        
        from demo_reminders import DemoReminderScript
        
        script = DemoReminderScript()
        user_id = current_user['id']
        
        script.setup_demo_data(user_id)
        reminder = script.send_challenge_reminder(user_id)
        
        return {
            "status": "success",
            "message": "Challenge reminder sent!",
            "reminder": reminder['title']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send challenge reminder: {str(e)}")