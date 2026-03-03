# app/models/chat.py
# Chat-related Pydantic models

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessageRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[Dict[str, Any]]] = None
    buttons: Optional[List[Dict[str, Any]]] = None
    mood: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    logs: List[Dict[str, Any]]
