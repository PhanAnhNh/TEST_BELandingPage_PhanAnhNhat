from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, products, cart, favorites
from app.core.database import database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    yield
    # Shutdown
    await database.disconnect()

app = FastAPI(
    title="E-commerce API",
    description="E-commerce backend API with authentication",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "https://test-landing-page-phan-anh-nhat.vercel.app", 
    "http://localhost:5173",                             
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["Favorites"])

@app.get("/")
async def root():
    return {"message": "E-commerce API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}