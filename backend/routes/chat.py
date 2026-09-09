from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import client, AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY
from backend.prompts import SYSTEM_PROMPTS

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    category: str
    history: list = []

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # ساخت پیام‌ها
        messages = build_messages(request)
        
        # ارسال به Hugging Face
        response = client.chat_completion(
            model=AI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content
        }
    except Exception as e:
        print(f"❌ Hugging Face Error: {str(e)}")
        return {
            "success": False,
            "response": f"خطا در پردازش: {str(e)}"
        }

def build_messages(request: ChatRequest) -> list:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS.get(
                request.category,
                SYSTEM_PROMPTS["general"]
            )
        }
    ]
    
    # اضافه کردن تاریخچه
    for msg in request.history[-MAX_HISTORY:]:
        if msg.get("role") in ["user", "assistant"]:
            messages.append(msg)
    
    # پیام فعلی
    messages.append({
        "role": "user",
        "content": request.message
    })
    
    return messages
