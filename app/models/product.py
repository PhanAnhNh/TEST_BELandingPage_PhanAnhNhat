from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    images: List[str] = []
    stock: int = 0
    rating: float = 0
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

class ProductInDB(Product):
    id: str