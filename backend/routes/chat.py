from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import client, AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY
from backend.prompts import SYSTEM_PROMPTS
import json

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    category: str = "general"
    history: list = []


def _as_text(value) -> str:
    """هر نوع محتوا را به رشته تبدیل می‌کند."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # فرمت multimodal یا خطای JSON
        if "text" in value:
            return str(value["text"])
        if "content" in value:
            return _as_text(value["content"])
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return " ".join(_as_text(v) for v in value)
    return str(value)


def build_messages(request: ChatRequest) -> list:
    system = SYSTEM_PROMPTS.get(request.category, SYSTEM_PROMPTS.get("general", ""))
    messages = [{"role": "system", "content": _as_text(system)}]

    for msg in (request.history or [])[-MAX_HISTORY:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        content = _as_text(msg.get("content", ""))
        if content:
            messages.append({"role": role, "content": content})

    user_msg = _as_text(request.message).strip()
    if user_msg:
        messages.append({"role": "user", "content": user_msg})

    return messages


def _extract_content(response) -> str:
    """محتوای پاسخ را از فرمت‌های مختلف استخراج می‌کند."""
    try:
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            msg = getattr(choice, "message", None) or getattr(choice, "delta", None)
            if msg is not None:
                content = getattr(msg, "content", None)
                return _as_text(content)
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if choices:
                msg = choices[0].get("message") or choices[0].get("delta") or {}
                return _as_text(msg.get("content"))
            return _as_text(response.get("content") or response.get("generated_text"))
    except Exception:
        pass
    return _as_text(response)


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        messages = build_messages(request)
        if len(messages) < 2:
            return {"success": False, "response": "پیام خالی است."}

        response = client.chat_completion(
            model=AI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        text = _extract_content(response)
        if not text:
            text = "پاسخی دریافت نشد. دوباره تلاش کن."
        return {"success": True, "response": text}
    except Exception as e:
        print(f"❌ Hugging Face Error: {type(e).__name__}: {e}")
        return {"success": False, "response": f"خطا در پردازش: {e}"}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            messages = build_messages(request)
            if len(messages) < 2:
                yield f"data: {json.dumps({'content': 'پیام خالی است.', 'done': True}, ensure_ascii=False)}\n\n"
                return

            stream = client.chat_completion(
                model=AI_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stream=True,
            )

            for chunk in stream:
                try:
                    text = ""
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        text = _as_text(getattr(delta, "content", None))
                    elif isinstance(chunk, dict):
                        choices = chunk.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta") or choices[0].get("message") or {}
                            text = _as_text(delta.get("content"))
                    if text:
                        yield f"data: {json.dumps({'content': text}, ensure_ascii=False)}\n\n"
                except Exception as inner:
                    print(f"⚠️ chunk skip: {inner}")
                    continue

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"❌ Stream Error: {type(e).__name__}: {e}")
            err = json.dumps(
                {"content": f"خطا در پردازش: {e}", "done": True},
                ensure_ascii=False,
            )
            yield f"data: {err}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
