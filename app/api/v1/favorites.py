from fastapi import APIRouter, Depends, HTTPException
from app.services.favorite_service import FavoriteService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.get("/")
async def get_favorites(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    favorite_service = FavoriteService(db)
    favorites = await favorite_service.get_favorites(str(current_user["_id"]))
    
    # Convert to response format
    result = []
    for product in favorites:
        result.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "category": product.category,
            "images": product.images,
            "rating": product.rating
        })
    
    return {
        "favorites": result,
        "total": len(result)
    }

@router.post("/{product_id}")
async def add_favorite(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    favorite_service = FavoriteService(db)
    success = await favorite_service.add_favorite(str(current_user["_id"]), product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product added to favorites successfully"}

@router.delete("/{product_id}")
async def remove_favorite(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    favorite_service = FavoriteService(db)
    success = await favorite_service.remove_favorite(str(current_user["_id"]), product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Product removed from favorites successfully"}

@router.get("/check/{product_id}")
async def check_favorite(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    favorite_service = FavoriteService(db)
    is_favorited = await favorite_service.is_favorited(str(current_user["_id"]), product_id)
    
    return {"is_favorited": is_favorited}