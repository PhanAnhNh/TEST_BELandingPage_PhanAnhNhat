from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Giải mã JWT token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_token(token: str) -> bool:
    """
    Kiểm tra token có hợp lệ không
    """
    payload = decode_access_token(token)
    return payload is not None

def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Lấy user_id từ token
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("user_id")
    return None

def get_email_from_token(token: str) -> Optional[str]:
    """
    Lấy email từ token
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None

def is_token_expired(token: str) -> bool:
    """
    Kiểm tra token đã hết hạn chưa
    """
    payload = decode_access_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    # So sánh với thời gian hiện tại
    expire_time = datetime.fromtimestamp(exp)
    return expire_time < datetime.utcnow()

def refresh_token(old_token: str) -> Optional[str]:
    """
    Tạo token mới từ token cũ
    """
    payload = decode_access_token(old_token)
    if not payload:
        return None
    
    # Xóa exp cũ
    payload.pop("exp", None)
    
    # Tạo token mới
    return create_access_token(payload)