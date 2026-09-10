from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import client, AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY
from backend.prompts import SYSTEM_PROMPTS
import json

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    category: str
    history: list = []


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

    for msg in request.history[-MAX_HISTORY:]:
        if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg.get("content", "")
            })

    messages.append({
        "role": "user",
        "content": request.message
    })

    return messages


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        messages = build_messages(request)
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            messages = build_messages(request)
            stream = client.chat_completion(
                model=AI_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stream=True
            )

            for chunk in stream:
                try:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None) or ""
                    if content:
                        payload = json.dumps({"content": content}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                except Exception:
                    continue

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"❌ Stream Error: {str(e)}")
            err = json.dumps(
                {"content": f"خطا در پردازش: {str(e)}", "done": True},
                ensure_ascii=False
            )
            yield f"data: {err}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
