# app/services/auth_service.py
from typing import Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.password_handler import verify_password, get_password_hash  # ✅ Import từ utils
from app.utils.jwt_handler import create_access_token  # ✅ Import từ utils
from app.models.user import User, UserInDB
from app.schemas.auth import RegisterRequest, LoginRequest, GoogleLoginRequest

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def register(self, data: RegisterRequest) -> Tuple[Optional[UserInDB], str]:
        # Kiểm tra email đã tồn tại
        existing_user = await self.db.users.find_one({"email": data.email})
        if existing_user:
            return None, "Email already registered"

        # Tạo user mới
        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),  # ✅ Dùng từ utils
            full_name=data.full_name or data.email.split('@')[0],
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = await self.db.users.insert_one(user.dict())
        user_id = str(result.inserted_id)
        
        created_user = await self.db.users.find_one({"_id": result.inserted_id})
        user_in_db = UserInDB(**created_user, id=user_id)
        
        return user_in_db, "User registered successfully"

    async def login(self, data: LoginRequest) -> Tuple[Optional[str], Optional[UserInDB], str]:
        user_data = await self.db.users.find_one({"email": data.email})
        if not user_data:
            return None, None, "Invalid credentials"

        user = UserInDB(**user_data, id=str(user_data["_id"]))
        
        if not user.password_hash or not verify_password(data.password, user.password_hash):  # ✅ Dùng từ utils
            return None, None, "Invalid credentials"

        if not user.is_active:
            return None, None, "Account has been deactivated"

        # Cập nhật last login
        await self.db.users.update_one(
            {"_id": user_data["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        # Tạo token
        access_token = create_access_token(  # ✅ Dùng từ utils
            data={"sub": user.email, "user_id": user.id}
        )
        
        return access_token, user, "Login successful"

    async def google_login(self, data: GoogleLoginRequest) -> Tuple[Optional[str], Optional[UserInDB], str]:
        try:
            # Kiểm tra user đã tồn tại chưa
            user_data = await self.db.users.find_one({"email": data.email})
            
            if user_data:
                # User đã tồn tại
                user = UserInDB(**user_data, id=str(user_data["_id"]))
                
                # Cập nhật google_id nếu chưa có
                if not user.google_id:
                    await self.db.users.update_one(
                        {"_id": user_data["_id"]},
                        {"$set": {
                            "google_id": data.google_id,
                            "updated_at": datetime.utcnow()
                        }}
                    )
            else:
                # Tạo user mới
                new_user = User(
                    email=data.email,
                    full_name=data.full_name or data.email.split('@')[0],
                    google_id=data.google_id,
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                result = await self.db.users.insert_one(new_user.dict())
                user_id = str(result.inserted_id)
                
                created_user = await self.db.users.find_one({"_id": result.inserted_id})
                user = UserInDB(**created_user, id=user_id)

            # Cập nhật last login
            await self.db.users.update_one(
                {"email": data.email},
                {"$set": {"last_login": datetime.utcnow()}}
            )

            # Tạo token
            access_token = create_access_token(  # ✅ Dùng từ utils
                data={"sub": user.email, "user_id": user.id}
            )
            
            return access_token, user, "Google login successful"

        except Exception as e:
            return None, None, f"Google authentication failed: {str(e)}"