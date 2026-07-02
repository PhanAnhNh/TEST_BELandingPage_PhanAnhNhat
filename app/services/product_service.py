from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.product import Product, ProductInDB
from app.schemas.product import ProductCreate, ProductUpdate
from datetime import datetime

class ProductService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> ProductInDB:
        product = Product(**product_data.dict())
        result = await self.db.products.insert_one(product.dict())
        product_id = str(result.inserted_id)
        return ProductInDB(**product.dict(), id=product_id)

    async def get_product(self, product_id: str) -> Optional[ProductInDB]:
        if not ObjectId.is_valid(product_id):
            return None
        product_data = await self.db.products.find_one({"_id": ObjectId(product_id)})
        if product_data:
            return ProductInDB(**product_data, id=str(product_data["_id"]))
        return None

    async def get_products(self, skip: int = 0, limit: int = 100, **filters) -> List[ProductInDB]:
        query = {}
        if filters.get("category"):
            query["category"] = filters["category"]
        if filters.get("min_price"):
            query["price"] = {"$gte": filters["min_price"]}
        if filters.get("max_price"):
            query["price"] = {"$lte": filters["max_price"]}
        if filters.get("name"):
            query["name"] = {"$regex": filters["name"], "$options": "i"}
        query["is_active"] = True

        cursor = self.db.products.find(query).skip(skip).limit(limit)
        products = []
        async for doc in cursor:
            products.append(ProductInDB(**doc, id=str(doc["_id"])))
        return products

    async def update_product(self, product_id: str, update_data: ProductUpdate) -> Optional[ProductInDB]:
        if not ObjectId.is_valid(product_id):
            return None
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_product(product_id)
        return None

    async def delete_product(self, product_id: str) -> bool:
        if not ObjectId.is_valid(product_id):
            return False
        result = await self.db.products.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0