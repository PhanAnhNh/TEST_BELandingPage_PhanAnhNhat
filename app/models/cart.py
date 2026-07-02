from typing import List
from datetime import datetime
from pydantic import BaseModel

class CartItem(BaseModel):
    product_id: str
    quantity: int
    added_at: datetime = datetime.utcnow()

class Cart(BaseModel):
    user_id: str
    items: List[CartItem] = []
    total_items: int = 0
    total_price: float = 0
    updated_at: datetime = datetime.utcnow()

class CartInDB(Cart):
    id: str