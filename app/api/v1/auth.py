from fastapi import APIRouter, HTTPException, Depends
from app.services.auth_service import AuthService
from app.core.security import get_current_user
from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, GoogleLoginRequest, TokenResponse

router = APIRouter( tags=["Authentication"])

@router.post("/register")
async def register(data: RegisterRequest, db = Depends(get_db)):
    auth_service = AuthService(db)
    user, message = await auth_service.register(data)
    
    if not user:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message, "user": user.dict()}

@router.post("/login")
async def login(data: LoginRequest, db = Depends(get_db)):
    auth_service = AuthService(db)
    access_token, user, message = await auth_service.login(data)
    
    if not access_token:
        raise HTTPException(status_code=400, detail=message)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user.dict()
    )

@router.post("/google-login")
async def google_login(data: GoogleLoginRequest, db = Depends(get_db)):
    auth_service = AuthService(db)
    access_token, user, message = await auth_service.google_login(data)
    
    if not access_token:
        raise HTTPException(status_code=400, detail=message)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user.dict()
    )

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    return current_user