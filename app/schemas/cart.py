from pydantic import BaseModel
from typing import List
from datetime import datetime

class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = 1

class CartItemResponse(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    quantity: int
    subtotal: float
    added_at: datetime

class CartResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemResponse]
    total_items: int
    total_price: float
    updated_at: datetime