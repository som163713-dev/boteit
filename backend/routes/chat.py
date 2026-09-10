from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY, HF_TOKEN, HF_CHAT_URL
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


def _headers():
    h = {"Content-Type": "application/json"}
    if HF_TOKEN:
        h["Authorization"] = f"Bearer {HF_TOKEN}"
    return h


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        messages = build_messages(request)
        if len(messages) < 2:
            return {"success": False, "response": "پیام خالی است."}

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "stream": False,
        }

        res = requests.post(HF_CHAT_URL, headers=_headers(), json=payload, timeout=120)

        if res.status_code != 200:
            err_body = res.text[:500]
            try:
                err_json = res.json()
                err_body = err_json.get("error", err_json)
                if isinstance(err_body, dict):
                    err_body = err_body.get("message") or json.dumps(err_body, ensure_ascii=False)
            except Exception:
                pass
            return {
                "success": False,
                "response": f"خطای API ({res.status_code}): {err_body}",
            }

        data = res.json()
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            text = _as_text(data)

        if not text:
            text = "پاسخی دریافت نشد."

        return {"success": True, "response": text}

    except Exception as e:
        print(f"❌ Chat Error: {type(e).__name__}: {e}")
        return {"success": False, "response": f"خطا در پردازش: {e}"}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            messages = build_messages(request)
            if len(messages) < 2:
                yield f"data: {json.dumps({'content': 'پیام خالی است.', 'done': True}, ensure_ascii=False)}\n\n"
                return

            payload = {
                "model": AI_MODEL,
                "messages": messages,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "stream": True,
            }

            with requests.post(
                HF_CHAT_URL,
                headers=_headers(),
                json=payload,
                timeout=120,
                stream=True,
            ) as res:
                if res.status_code != 200:
                    err = res.text[:400]
                    try:
                        ej = res.json()
                        err = ej.get("error", ej)
                        if isinstance(err, dict):
                            err = err.get("message") or json.dumps(err, ensure_ascii=False)
                    except Exception:
                        pass
                    yield f"data: {json.dumps({'content': f'خطای API ({res.status_code}): {err}', 'done': True}, ensure_ascii=False)}\n\n"
                    return

                for raw in res.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    line = raw.strip() if isinstance(raw, str) else raw.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                        content = delta.get("content") or ""
                        if content:
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    except Exception:
                        continue

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
