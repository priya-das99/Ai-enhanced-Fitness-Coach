# app/api/v1/endpoints/chat.py
# Chat endpoints

from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatMessageRequest, ChatResponse, ChatHistoryResponse
from app.services.chat_service import ChatService
from app.api.deps import get_current_user
from typing import Dict

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
    """Process user message"""
    try:
        response = chat_service.process_message(current_user['id'], request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Get chat message history"""
    try:
        messages = chat_service.get_chat_messages(current_user['id'], limit)
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
