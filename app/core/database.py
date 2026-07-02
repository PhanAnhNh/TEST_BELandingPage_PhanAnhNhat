from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.core.config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        
        # Create indexes
        await self.create_indexes()

    async def create_indexes(self):
        # User indexes
        await self.db.users.create_index("email", unique=True)
        
        # Product indexes
        await self.db.products.create_index("name")
        await self.db.products.create_index("price")
        await self.db.products.create_index("category")
        
        # Cart indexes
        await self.db.carts.create_index([("user_id", 1)], unique=True)
        
        # Favorites indexes
        await self.db.favorites.create_index([("user_id", 1), ("product_id", 1)], unique=True)

    async def disconnect(self):
        if self.client:
            self.client.close()

database = Database()

def get_db():
    return database.db