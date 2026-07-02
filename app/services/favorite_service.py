from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.favorite import Favorite, FavoriteInDB
from app.models.product import ProductInDB
from datetime import datetime

class FavoriteService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def add_favorite(self, user_id: str, product_id: str) -> bool:
        # Check if product exists and is active
        product = await self.db.products.find_one({"_id": ObjectId(product_id), "is_active": True})
        if not product:
            return False
        
        # Check if already favorited
        existing = await self.db.favorites.find_one({
            "user_id": user_id,
            "product_id": product_id
        })
        if existing:
            return True
        
        favorite = Favorite(user_id=user_id, product_id=product_id)
        result = await self.db.favorites.insert_one(favorite.dict())
        return result.inserted_id is not None

    async def remove_favorite(self, user_id: str, product_id: str) -> bool:
        result = await self.db.favorites.delete_one({
            "user_id": user_id,
            "product_id": product_id
        })
        return result.deleted_count > 0

    async def get_favorites(self, user_id: str) -> List[ProductInDB]:
        favorites = []
        cursor = self.db.favorites.find({"user_id": user_id})
        
        async for fav in cursor:
            product = await self.db.products.find_one({"_id": ObjectId(fav["product_id"])})
            if product:
                favorites.append(ProductInDB(**product, id=str(product["_id"])))
        
        return favorites

    async def is_favorited(self, user_id: str, product_id: str) -> bool:
        favorite = await self.db.favorites.find_one({
            "user_id": user_id,
            "product_id": product_id
        })
        return favorite is not None