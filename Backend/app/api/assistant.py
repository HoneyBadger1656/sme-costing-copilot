# backend/app/api/assistant.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.services.ai_assistant_service import AIAssistantService

router = APIRouter(tags=["ai-assistant"])

class ChatRequest(BaseModel):
    message: str
    client_id: int

class ChatResponse(BaseModel):
    message: str
    query_type: str

@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message to AI assistant"""
    response = AIAssistantService.chat(
        db=db,
        client_id=request.client_id,
        user_message=request.message
    )
    
    return {
        "message": response["message"],
        "query_type": response["query_type"]
    }

@router.get("/history")
def get_history(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    history = AIAssistantService.get_conversation_history(db, client_id)
    return {"messages": history}
