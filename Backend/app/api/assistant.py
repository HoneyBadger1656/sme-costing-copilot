# backend/app/api/assistant.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import io
import PyPDF2

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.services.ai_assistant_service import AIAssistantService

router = APIRouter(tags=["ai-assistant"])

class ChatRequest(BaseModel):
    message: str
    client_id: int

class FileUploadChatRequest(BaseModel):
    message: str
    client_id: int
    file_content: str
    file_name: str
    file_type: str

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

@router.post("/upload-chat")
async def upload_and_chat(
    file: UploadFile = File(...),
    message: str = "Analyze this file",
    client_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file and ask questions about it"""
    
    # Validate file type
    allowed_types = ["application/pdf", "text/csv", "application/vnd.ms-excel", 
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, CSV, or Excel files.")
    
    try:
        # Read file content
        file_content = await file.read()
        file_text = ""
        
        if file.content_type == "application/pdf":
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                file_text += page.extract_text() + "\n"
        
        elif file.content_type == "text/csv":
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content))
            file_text = f"CSV File Analysis:\n"
            file_text += f"Columns: {', '.join(df.columns.tolist())}\n"
            file_text += f"Rows: {len(df)}\n"
            file_text += f"Sample data:\n{df.head(10).to_string()}\n"
            file_text += f"Summary statistics:\n{df.describe().to_string()}"
        
        elif file.content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            # Read Excel
            df = pd.read_excel(io.BytesIO(file_content))
            file_text = f"Excel File Analysis:\n"
            file_text += f"Columns: {', '.join(df.columns.tolist())}\n"
            file_text += f"Rows: {len(df)}\n"
            file_text += f"Sample data:\n{df.head(10).to_string()}\n"
            file_text += f"Summary statistics:\n{df.describe().to_string()}"
        
        # Limit file content to prevent token overflow
        if len(file_text) > 5000:
            file_text = file_text[:5000] + "\n... (content truncated)"
        
        # Process with AI assistant
        enhanced_message = f"{message}\n\nFile: {file.filename}\nContent:\n{file_text}"
        
        response = AIAssistantService.chat_with_file(
            db=db,
            client_id=client_id,
            user_message=enhanced_message,
            file_name=file.filename,
            file_content=file_text
        )
        
        return {
            "message": response["message"],
            "query_type": response["query_type"],
            "file_processed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
