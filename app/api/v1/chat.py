# app/api/v1/chat.py
from fastapi import APIRouter, Depends, HTTPException, Body
from app.services.ai_service import AIService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    context: dict
    history: list

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Chat với AI có truy cập MongoDB"""
    try:
        ai_service = AIService(db)
        
        # Lấy user_id từ token hoặc từ request
        user_id = str(current_user["_id"]) if current_user else request.user_id
        
        result = await ai_service.chat_with_ai(
            message=request.message,
            user_id=user_id
        )
        
        return ChatResponse(
            response=result["response"],
            context=result.get("context", {}),
            history=result.get("history", [])
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history")
async def get_chat_history(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Lấy lịch sử chat của user"""
    try:
        # Lưu lịch sử chat vào MongoDB
        # TODO: Implement chat history storage
        return {"history": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/clear")
async def clear_chat_history(
    current_user = Depends(get_current_user)
):
    """Xóa lịch sử chat"""
    try:
        # TODO: Clear chat history from MongoDB
        return {"message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))