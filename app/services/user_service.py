from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.user import UserInDB
from app.schemas.user import UserUpdateRequest
from datetime import datetime

class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_user(self, user_id: str) -> Optional[UserInDB]:
        if not ObjectId.is_valid(user_id):
            return None
        user_data = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return UserInDB(**user_data, id=str(user_data["_id"]))
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        user_data = await self.db.users.find_one({"email": email})
        if user_data:
            return UserInDB(**user_data, id=str(user_data["_id"]))
        return None

    async def update_user(self, user_id: str, update_data: UserUpdateRequest) -> Optional[UserInDB]:
        if not ObjectId.is_valid(user_id):
            return None
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_user(user_id)
        return None

    async def get_user_favorites(self, user_id: str) -> list:
        favorites = []
        cursor = self.db.favorites.find({"user_id": user_id})
        async for fav in cursor:
            product = await self.db.products.find_one({"_id": ObjectId(fav["product_id"])})
            if product:
                favorites.append({
                    "id": str(product["_id"]),
                    "name": product["name"],
                    "price": product["price"],
                    "image": product.get("images", [])[0] if product.get("images") else None
                })
        return favorites