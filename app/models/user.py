from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

class UserInDB(User):
    id: str