from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY, GEMINI_API_KEY, GEMINI_URL
from backend.prompts import SYSTEM_PROMPTS
import json
import requests

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    category: str = "general"
    history: list = []


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "text" in value:
            return str(value["text"])
        if "content" in value:
            return _as_text(value["content"])
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return " ".join(_as_text(v) for v in value)
    return str(value)


def build_contents(request: ChatRequest) -> list:
    """ساخت تاریخچه به فرمت Gemini."""
    contents = []

    for msg in (request.history or [])[-MAX_HISTORY:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = _as_text(msg.get("content", "")).strip()
        if not content:
            continue
        # Gemini: user / model
        if role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})

    user_msg = _as_text(request.message).strip()
    if user_msg:
        contents.append({"role": "user", "parts": [{"text": user_msg}]})

    return contents


def _system_text(category: str) -> str:
    return _as_text(SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS.get("general", "")))


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        if not GEMINI_API_KEY:
            return {"success": False, "response": "کلید Gemini تنظیم نشده است."}

        contents = build_contents(request)
        if not contents:
            return {"success": False, "response": "پیام خالی است."}

        payload = {
            "system_instruction": {
                "parts": [{"text": _system_text(request.category)}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": TEMPERATURE,
                "maxOutputTokens": MAX_TOKENS,
            },
        }

        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        res = requests.post(url, json=payload, timeout=90)

        if res.status_code != 200:
            err = res.text[:400]
            try:
                ej = res.json()
                err = ej.get("error", {}).get("message") or json.dumps(ej, ensure_ascii=False)
            except Exception:
                pass
            return {"success": False, "response": f"خطای Gemini ({res.status_code}): {err}"}

        data = res.json()
        text = ""
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            text = _as_text(data)

        if not text:
            text = "پاسخی دریافت نشد."

        return {"success": True, "response": text}

    except Exception as e:
        print(f"❌ Gemini Error: {type(e).__name__}: {e}")
        return {"success": False, "response": f"خطا در پردازش: {e}"}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """استریم ساده: کل پاسخ را یک‌جا می‌گیرد و تکه‌تکه می‌فرستد (سازگار با فرانت)."""

    def event_generator():
        try:
            if not GEMINI_API_KEY:
                yield f"data: {json.dumps({'content': 'کلید Gemini تنظیم نشده.', 'done': True}, ensure_ascii=False)}\n\n"
                return

            contents = build_contents(request)
            if not contents:
                yield f"data: {json.dumps({'content': 'پیام خالی است.', 'done': True}, ensure_ascii=False)}\n\n"
                return

            payload = {
                "system_instruction": {
                    "parts": [{"text": _system_text(request.category)}]
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": TEMPERATURE,
                    "maxOutputTokens": MAX_TOKENS,
                },
            }

            url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
            res = requests.post(url, json=payload, timeout=90)

            if res.status_code != 200:
                err = res.text[:300]
                try:
                    ej = res.json()
                    err = ej.get("error", {}).get("message") or str(ej)
                except Exception:
                    pass
                yield f"data: {json.dumps({'content': f'خطای Gemini ({res.status_code}): {err}', 'done': True}, ensure_ascii=False)}\n\n"
                return

            data = res.json()
            text = ""
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                text = "پاسخی دریافت نشد."

            # تکه‌تکه برای حس استریم در فرانت
            step = 12
            for i in range(0, len(text), step):
                chunk = text[i : i + step]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"❌ Stream Error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'content': f'خطا در پردازش: {e}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
