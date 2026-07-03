# app/services/ai_service.py
import httpx
import json
import logging
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os
from datetime import datetime

logger = logging.getLogger(__name__)

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
            logger.error(f"Error searching products: {e}")
            return []

    async def chat_with_ai(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Xử lý chat với AI và dữ liệu từ MongoDB"""
        try:
            # 1. Lấy dữ liệu từ MongoDB
            context_data = await self._get_context_data(message, user_id)
            
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
                "history": self.chat_history[-10:]
            }
            
        except Exception as e:
            logger.error(f"Error in chat_with_ai: {e}", exc_info=True)
            return {
                "response": "Xin lỗi, tôi gặp sự cố. Vui lòng thử lại sau.",
                "error": str(e)
            }

    async def _get_context_data(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Lấy context data từ MongoDB"""
        context_data = {}
        lower_message = message.lower()
        
        # Tìm kiếm sản phẩm
        products = await self.search_products(message)
        if products:
            context_data["products"] = products
        
        return context_data

    def _build_system_prompt(self) -> str:
        return """Bạn là trợ lý AI chuyên nghiệp của Apple Store Việt Nam.

        QUY TẮC QUAN TRỌNG:
        1. Ưu tiên sử dụng DỮ LIỆU THỰC TẾ từ hệ thống để trả lời
        2. Nếu có dữ liệu sản phẩm, hãy trích dẫn giá và thông tin cụ thể
        3. Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp
        4. Nếu hỏi về giá, hãy đưa ra giá chính xác từ hệ thống
        """

    def _build_user_prompt(self, message: str, context_data: Dict[str, Any]) -> str:
        prompt = f"Câu hỏi: {message}\n\n"
        
        if context_data and "products" in context_data:
            prompt += "=== DỮ LIỆU TỪ HỆ THỐNG ===\n"
            prompt += "\n📦 SẢN PHẨM TÌM THẤY:\n"
            for product in context_data["products"][:3]:
                prompt += f"- {product['name']}: {product['price']:,}đ"
                if product.get('stock', 0) > 0:
                    prompt += f" (Còn {product['stock']} sản phẩm)"
                else:
                    prompt += " (Hết hàng)"
                prompt += "\n"
        
        prompt += "\nHãy trả lời câu hỏi dựa trên dữ liệu trên."
        return prompt

    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> str:
        """Gọi OpenRouter API"""
        try:
            if not self.openrouter_api_key:
                logger.warning("OpenRouter API Key not configured")
                return "⚠️ Chưa cấu hình OpenRouter API Key!"

            logger.info(f"Calling OpenRouter API with model: {self.openrouter_model}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                    }
                )
                
                if response.status_code != 200:
                    error_data = response.json()
                    logger.error(f"OpenRouter Error: {error_data}")
                    return f"⚠️ Lỗi từ AI: {error_data.get('error', {}).get('message', 'Unknown error')}"
                
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "Xin lỗi, tôi không có phản hồi.")
                
        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            return "⏱️ Kết nối đến AI bị timeout. Vui lòng thử lại."
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {e}", exc_info=True)
            return f"⚠️ Lỗi kết nối: {str(e)}"