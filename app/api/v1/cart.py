from fastapi import APIRouter, Depends, HTTPException
from app.services.cart_service import CartService
from app.schemas.cart import CartItemRequest, CartResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId 

router = APIRouter()

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_service = CartService(db)
    cart = await cart_service.get_cart(str(current_user["_id"]))
    
    # Get product details for each item
    items = []
    for item in cart.items:
        product = await db.products.find_one({"_id": ObjectId(item.product_id)})
        if product:
            items.append({
                "product_id": item.product_id,
                "product_name": product["name"],
                "product_price": product["price"],
                "quantity": item.quantity,
                "subtotal": product["price"] * item.quantity,
                "added_at": item.added_at
            })
    
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "items": items,
        "total_items": cart.total_items,
        "total_price": cart.total_price,
        "updated_at": cart.updated_at
    }

@router.post("/items")
async def add_to_cart(
    item_data: CartItemRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_service = CartService(db)
    try:
        cart = await cart_service.add_to_cart(
            str(current_user["_id"]),
            item_data.product_id,
            item_data.quantity
        )
        return {"message": "Item added to cart successfully", "cart_id": cart.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/items/{product_id}")
async def remove_from_cart(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_service = CartService(db)
    cart = await cart_service.remove_from_cart(str(current_user["_id"]), product_id)
    return {"message": "Item removed from cart successfully"}

@router.put("/items/{product_id}")
async def update_cart_item(
    product_id: str,
    quantity: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity must be >= 0")
    
    cart_service = CartService(db)
    cart = await cart_service.update_cart_item(
        str(current_user["_id"]),
        product_id,
        quantity
    )
    return {"message": "Cart item updated successfully"}

@router.delete("/")
async def clear_cart(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_service = CartService(db)
    cart = await cart_service.clear_cart(str(current_user["_id"]))
    return {"message": "Cart cleared successfully"}