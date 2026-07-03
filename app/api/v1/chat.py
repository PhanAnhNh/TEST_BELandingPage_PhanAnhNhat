# app/api/v1/chat.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_service import AIService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Chat với AI có truy cập MongoDB"""
    try:
        logger.info(f"Chat request from user: {current_user.get('email') if current_user else 'anonymous'}")
        logger.info(f"Message: {request.message}")
        
        ai_service = AIService(db)
        
        # Lấy user_id từ token
        user_id = str(current_user["_id"]) if current_user else None
        
        result = await ai_service.chat_with_ai(
            message=request.message,
            user_id=user_id
        )
        
        logger.info(f"Chat response generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history")
async def get_chat_history(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Lấy lịch sử chat của user"""
    try:
        # TODO: Implement chat history storage in MongoDB
        return {"history": []}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {"history": []}

@router.post("/chat/clear")
async def clear_chat_history(
    current_user = Depends(get_current_user)
):
    """Xóa lịch sử chat"""
    try:
        # TODO: Clear chat history from MongoDB
        return {"message": "Chat history cleared"}
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))