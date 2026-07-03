import httpx
import json
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os
from datetime import datetime

class AIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp")
        self.base_url = "https://openrouter.ai/api/v1"
        self.chat_history = []

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Tìm kiếm sản phẩm trong MongoDB"""
        try:
            # Tìm kiếm theo tên hoặc mô tả
            search_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"category": {"$regex": query, "$options": "i"}}
                ],
                "is_active": True
            }
            
            cursor = self.db.products.find(search_query).limit(5)
            products = []
            async for doc in cursor:
                products.append({
                    "id": str(doc["_id"]),
                    "name": doc.get("name", ""),
                    "price": doc.get("price", 0),
                    "description": doc.get("description", ""),
                    "category": doc.get("category", ""),
                    "stock": doc.get("stock", 0),
                    "images": doc.get("images", [])
                })
            return products
        except Exception as e:
            print(f"Error searching products: {e}")
            return []

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Lấy sản phẩm theo danh mục"""
        try:
            cursor = self.db.products.find({
                "category": {"$regex": category, "$options": "i"},
                "is_active": True
            }).limit(5)
            
            products = []
            async for doc in cursor:
                products.append({
                    "id": str(doc["_id"]),
                    "name": doc.get("name", ""),
                    "price": doc.get("price", 0),
                    "description": doc.get("description", ""),
                    "category": doc.get("category", ""),
                    "stock": doc.get("stock", 0)
                })
            return products
        except Exception as e:
            print(f"Error getting products by category: {e}")
            return []

    async def search_products_by_price(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """Tìm kiếm sản phẩm theo khoảng giá"""
        try:
            cursor = self.db.products.find({
                "price": {"$gte": min_price, "$lte": max_price},
                "is_active": True
            }).limit(5)
            
            products = []
            async for doc in cursor:
                products.append({
                    "id": str(doc["_id"]),
                    "name": doc.get("name", ""),
                    "price": doc.get("price", 0),
                    "description": doc.get("description", ""),
                    "category": doc.get("category", ""),
                    "stock": doc.get("stock", 0)
                })
            return products
        except Exception as e:
            print(f"Error searching products by price: {e}")
            return []

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Lấy chi tiết sản phẩm theo ID"""
        try:
            if not ObjectId.is_valid(product_id):
                return None
            doc = await self.db.products.find_one({"_id": ObjectId(product_id)})
            if doc:
                return {
                    "id": str(doc["_id"]),
                    "name": doc.get("name", ""),
                    "price": doc.get("price", 0),
                    "description": doc.get("description", ""),
                    "category": doc.get("category", ""),
                    "stock": doc.get("stock", 0),
                    "images": doc.get("images", []),
                    "rating": doc.get("rating", 0)
                }
            return None
        except Exception as e:
            print(f"Error getting product: {e}")
            return None

    async def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy đơn hàng của user"""
        try:
            cursor = self.db.orders.find({"user_id": user_id}).limit(5)
            orders = []
            async for doc in cursor:
                orders.append({
                    "id": str(doc["_id"]),
                    "total": doc.get("total", 0),
                    "status": doc.get("status", ""),
                    "created_at": doc.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
                    "items": doc.get("items", [])
                })
            return orders
        except Exception as e:
            print(f"Error getting user orders: {e}")
            return []

    async def process_query(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Xử lý query và lấy dữ liệu từ MongoDB"""
        lower_message = message.lower()
        context_data = {}
        
        # 1. Tìm kiếm sản phẩm theo từ khóa
        products = await self.search_products(message)
        if products:
            context_data["products"] = products
        
        # 2. Tìm kiếm theo danh mục
        categories = ["accessories", "iphone", "ipad", "macbook", "apple watch", "airpods", "phụ kiện"]
        for category in categories:
            if category in lower_message:
                category_products = await self.get_products_by_category(category)
                if category_products:
                    context_data["category_products"] = category_products
                    context_data["category"] = category
                break
        
        # 3. Tìm kiếm theo giá
        import re
        price_pattern = r'(\d+[\.,]?\d*)\s*(triệu|ngàn|k|đ)'
        price_match = re.search(price_pattern, lower_message)
        if price_match:
            price = float(price_match.group(1).replace(',', '.'))
            unit = price_match.group(2)
            min_price, max_price = 0, 0
            
            if unit == "triệu":
                min_price = price * 1000000 * 0.8
                max_price = price * 1000000 * 1.2
            elif unit in ["ngàn", "k"]:
                min_price = price * 1000 * 0.8
                max_price = price * 1000 * 1.2
            
            if min_price > 0:
                price_products = await self.search_products_by_price(min_price, max_price)
                if price_products:
                    context_data["price_products"] = price_products
        
        # 4. Lấy đơn hàng của user
        if user_id and ("đơn hàng" in lower_message or "order" in lower_message):
            orders = await self.get_user_orders(user_id)
            if orders:
                context_data["orders"] = orders
        
        # 5. Lấy thông tin user
        if user_id:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                context_data["user"] = {
                    "full_name": user.get("full_name", ""),
                    "email": user.get("email", "")
                }
        
        return context_data

    async def chat_with_ai(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Xử lý chat với AI và dữ liệu từ MongoDB"""
        try:
            # 1. Lấy dữ liệu từ MongoDB
            context_data = await self.process_query(message, user_id)
            
            # 2. Xây dựng prompt với context
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(message, context_data)
            
            # 3. Gọi OpenRouter API
            ai_response = await self._call_openrouter(system_prompt, user_prompt)
            
            # 4. Lưu lịch sử
            self.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.chat_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "response": ai_response,
                "context": context_data,
                "history": self.chat_history[-10:]  # Trả về 10 tin nhắn cuối
            }
            
        except Exception as e:
            print(f"Error in chat_with_ai: {e}")
            return {
                "response": "Xin lỗi, tôi gặp sự cố. Vui lòng thử lại sau.",
                "error": str(e)
            }

    def _build_system_prompt(self) -> str:
        """Xây dựng system prompt"""
        return """Bạn là trợ lý AI chuyên nghiệp của Apple Store Việt Nam.

        QUY TẮC QUAN TRỌNG:
        1. Ưu tiên sử dụng DỮ LIỆU THỰC TẾ từ hệ thống để trả lời
        2. Nếu có dữ liệu sản phẩm, hãy trích dẫn giá và thông tin cụ thể
        3. Nếu không có dữ liệu, hãy dùng kiến thức chung của bạn
        4. Luôn kiểm tra tính chính xác của thông tin
        5. Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp
        6. Nếu hỏi về giá, hãy đưa ra giá chính xác từ hệ thống
        7. Nếu hỏi về sản phẩm, hãy giới thiệu chi tiết và ưu điểm
        8. Nếu sản phẩm hết hàng, hãy đề xuất sản phẩm tương tự
        """

    def _build_user_prompt(self, message: str, context_data: Dict[str, Any]) -> str:
        """Xây dựng user prompt với context"""
        prompt = f"Câu hỏi: {message}\n\n"
        
        if context_data:
            prompt += "=== DỮ LIỆU TỪ HỆ THỐNG ===\n"
            
            # Thông tin user
            if "user" in context_data:
                user = context_data["user"]
                prompt += f"\n👤 Khách hàng: {user.get('full_name', '')}"
                prompt += f"\n📧 Email: {user.get('email', '')}\n"
            
            # Sản phẩm tìm thấy
            if "products" in context_data:
                prompt += "\n📦 SẢN PHẨM TÌM THẤY:\n"
                for product in context_data["products"][:3]:
                    prompt += f"- {product['name']}: {product['price']:,}đ"
                    if product['stock'] > 0:
                        prompt += f" (Còn {product['stock']} sản phẩm)"
                    else:
                        prompt += " (Hết hàng)"
                    prompt += "\n"
                    if product.get('description'):
                        prompt += f"  {product['description'][:100]}...\n"
            
            # Sản phẩm theo danh mục
            if "category_products" in context_data:
                prompt += f"\n📂 SẢN PHẨM DANH MỤC {context_data.get('category', '').upper()}:\n"
                for product in context_data["category_products"][:3]:
                    prompt += f"- {product['name']}: {product['price']:,}đ\n"
            
            # Sản phẩm theo giá
            if "price_products" in context_data:
                prompt += "\n💰 SẢN PHẨM TRONG KHOẢNG GIÁ:\n"
                for product in context_data["price_products"][:3]:
                    prompt += f"- {product['name']}: {product['price']:,}đ\n"
            
            # Đơn hàng
            if "orders" in context_data:
                prompt += "\n📋 ĐƠN HÀNG CỦA BẠN:\n"
                for order in context_data["orders"][:3]:
                    prompt += f"- Mã: {order['id']} | Ngày: {order['created_at']} | Tổng: {order['total']:,}đ\n"
            
            prompt += "\n=== HẾT DỮ LIỆU ===\n\n"
            prompt += f"Dựa trên dữ liệu trên, hãy trả lời câu hỏi: {message}\n"
            prompt += "Nếu có sản phẩm, hãy giới thiệu chi tiết và gợi ý mua hàng."
        else:
            prompt += "\n(Không có dữ liệu cụ thể từ hệ thống, hãy dùng kiến thức chung để trả lời)\n"
        
        return prompt

    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi OpenRouter API"""
        try:
            if not self.openrouter_api_key:
                return "⚠️ Chưa cấu hình OpenRouter API Key!"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "Apple Store AI Assistant"
                    },
                    json={
                        "model": self.openrouter_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "top_p": 0.95,
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_data = response.json()
                    print(f"OpenRouter Error: {error_data}")
                    return f"⚠️ Lỗi từ AI: {error_data.get('error', {}).get('message', 'Unknown error')}"
                
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "Xin lỗi, tôi không có phản hồi.")
                
        except Exception as e:
            print(f"Error calling OpenRouter: {e}")
            return f"⚠️ Lỗi kết nối: {str(e)}"