from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.cart import Cart, CartItem, CartInDB
from app.schemas.cart import CartItemRequest, CartItemResponse, CartResponse
from datetime import datetime

class CartService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_cart(self, user_id: str) -> CartInDB:
        cart_data = await self.db.carts.find_one({"user_id": user_id})
        if not cart_data:
            # Create new cart
            cart = Cart(user_id=user_id)
            result = await self.db.carts.insert_one(cart.dict())
            cart_data = await self.db.carts.find_one({"_id": result.inserted_id})
        
        # Calculate totals
        await self._update_cart_totals(cart_data["_id"])
        cart_data = await self.db.carts.find_one({"_id": cart_data["_id"]})
        
        return CartInDB(**cart_data, id=str(cart_data["_id"]))

    async def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> CartInDB:
        cart = await self.get_cart(user_id)
        
        # Check if product exists
        product = await self.db.products.find_one({"_id": ObjectId(product_id), "is_active": True})
        if not product:
            raise ValueError("Product not found or inactive")
        
        # Check if product already in cart
        cart_data = await self.db.carts.find_one({"_id": ObjectId(cart.id)})
        existing_item = None
        for item in cart_data.get("items", []):
            if item["product_id"] == product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity
            await self.db.carts.update_one(
                {"_id": ObjectId(cart.id), "items.product_id": product_id},
                {"$inc": {"items.$.quantity": quantity}}
            )
        else:
            # Add new item
            new_item = CartItem(product_id=product_id, quantity=quantity)
            await self.db.carts.update_one(
                {"_id": ObjectId(cart.id)},
                {"$push": {"items": new_item.dict()}}
            )
        
        return await self.get_cart(user_id)

    async def remove_from_cart(self, user_id: str, product_id: str) -> CartInDB:
        cart = await self.get_cart(user_id)
        
        await self.db.carts.update_one(
            {"_id": ObjectId(cart.id)},
            {"$pull": {"items": {"product_id": product_id}}}
        )
        
        return await self.get_cart(user_id)

    async def update_cart_item(self, user_id: str, product_id: str, quantity: int) -> CartInDB:
        if quantity <= 0:
            return await self.remove_from_cart(user_id, product_id)
        
        cart = await self.get_cart(user_id)
        
        await self.db.carts.update_one(
            {"_id": ObjectId(cart.id), "items.product_id": product_id},
            {"$set": {"items.$.quantity": quantity}}
        )
        
        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: str) -> CartInDB:
        cart = await self.get_cart(user_id)
        
        await self.db.carts.update_one(
            {"_id": ObjectId(cart.id)},
            {"$set": {"items": [], "total_items": 0, "total_price": 0}}
        )
        
        return await self.get_cart(user_id)

    async def _update_cart_totals(self, cart_id):
        cart_data = await self.db.carts.find_one({"_id": cart_id})
        if not cart_data:
            return
        
        total_items = 0
        total_price = 0
        
        for item in cart_data.get("items", []):
            product = await self.db.products.find_one({"_id": ObjectId(item["product_id"])})
            if product:
                total_items += item["quantity"]
                total_price += product["price"] * item["quantity"]
        
        await self.db.carts.update_one(
            {"_id": cart_id},
            {"$set": {"total_items": total_items, "total_price": total_price, "updated_at": datetime.utcnow()}}
        )