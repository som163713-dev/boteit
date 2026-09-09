from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import (
    get_client, AI_MODEL,
    MAX_TOKENS, TEMPERATURE, MAX_HISTORY
)
from backend.prompts import SYSTEM_PROMPTS
import json

router = APIRouter()

class ChatRequest(BaseModel):
    message:  str
    category: str
    history:  list = []

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    def generate():
        try:
            client   = get_client()
            messages = build_messages(request)

            stream = client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stream=True
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    data = json.dumps({
                        "content": content,
                        "done": False
                    }, ensure_ascii=False)
                    yield f"data: {data}\n\n"

            yield f"data: {json.dumps({'content':'','done':True})}\n\n"

        except Exception as e:
            print(f"❌ Groq Error: {e}")
            err = json.dumps({
                "content": "مشکلی پیش اومد. دوباره تلاش کن!",
                "done": True
            }, ensure_ascii=False)
            yield f"data: {err}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        client   = get_client()
        messages = build_messages(request)

        response = client.chat.completions.create(
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
        print(f"❌ Error: {e}")
        return {
            "success": False,
            "response": "مشکلی پیش اومد!"
        }

def build_messages(request: ChatRequest) -> list:
    messages = [{
        "role":    "system",
        "content": SYSTEM_PROMPTS.get(
            request.category,
            SYSTEM_PROMPTS["general"]
        )
    }]

    for msg in request.history[-MAX_HISTORY:]:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role":    msg["role"],
                "content": msg["content"]
            })

    messages.append({
        "role":    "user",
        "content": request.message
    })

    return messages
