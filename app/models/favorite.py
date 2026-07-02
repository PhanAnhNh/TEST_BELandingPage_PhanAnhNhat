from datetime import datetime
from pydantic import BaseModel

class Favorite(BaseModel):
    user_id: str
    product_id: str
    created_at: datetime = datetime.utcnow()

class FavoriteInDB(Favorite):
    id: str