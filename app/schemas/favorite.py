from pydantic import BaseModel
from datetime import datetime

class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FavoriteCheckResponse(BaseModel):
    is_favorited: bool