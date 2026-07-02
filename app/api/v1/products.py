from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    name: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    product_service = ProductService(db)
    products = await product_service.get_products(
        skip=skip,
        limit=limit,
        category=category,
        min_price=min_price,
        max_price=max_price,
        name=name
    )
    return [ProductResponse(**p.dict()) for p in products]

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    product_service = ProductService(db)
    product = await product_service.get_product(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse(**product.dict())

@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if user is admin
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    product_service = ProductService(db)
    product = await product_service.create_product(product_data)
    return ProductResponse(**product.dict())

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if user is admin
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    product_service = ProductService(db)
    product = await product_service.update_product(product_id, product_data)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse(**product.dict())

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if user is admin
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    product_service = ProductService(db)
    deleted = await product_service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}