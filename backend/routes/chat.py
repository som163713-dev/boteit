from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
import json
import requests
import time
import threading

from backend.config import (
    AI_MODEL, MAX_TOKENS, TEMPERATURE, MAX_HISTORY,
    GEMINI_API_KEY, GEMINI_URL,
    MAX_MESSAGES_PER_DAY, MAX_REQUESTS_PER_MINUTE
)
from backend.prompts import SYSTEM_PROMPTS
from backend.database import get_db
from backend.models import Message, Customer
from backend.auth import get_customer

router = APIRouter()

# ─── rate-limit ساده در حافظه (برای هر مشتری) ───
_rate_lock = threading.Lock()
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(api_key: str):
    now = time.time()
    with _rate_lock:
        bucket = _rate_buckets[api_key]
        # پاک کردن درخواست‌های قدیمی‌تر از ۶۰ ثانیه
        bucket[:] = [t for t in bucket if now - t < 60]
        if len(bucket) >= MAX_REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="تعداد درخواست‌ها بیش از حد مجاز است. کمی صبر کنید."
            )
        bucket.append(now)


def _check_daily_quota(db: Session, customer: Customer):
    limit = MAX_MESSAGES_PER_DAY.get(customer.plan, MAX_MESSAGES_PER_DAY["basic"])
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.query(func.count(Message.id)).filter(
        Message.customer_id == customer.id,
        Message.created_at >= today_start,
        Message.role == "user"
    ).scalar() or 0
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"سهمیه پیام روزانه پلن {customer.plan} تمام شده ({limit} پیام)."
        )


def _estimate_tokens(text: str) -> int:
    """تقریب ساده: حدود ۴ کاراکتر ≈ ۱ توکن برای فارسی/انگلیسی"""
    if not text:
        return 0
    return max(1, len(text) // 4)


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


class ChatRequest(BaseModel):
    message: str
    api_key: str = Field(..., description="کلید API مشتری")
    category: str = "general"
    history: list = []
    user_id: str = "anonymous"


def build_contents(request: ChatRequest) -> list:
    contents = []
    for msg in (request.history or [])[-MAX_HISTORY:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = _as_text(msg.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role in ("assistant", "model"):
            contents.append({"role": "model", "parts": [{"text": content}]})

    user_msg = _as_text(request.message).strip()
    if user_msg:
        contents.append({"role": "user", "parts": [{"text": user_msg}]})
    return contents


def _system_text(category: str) -> str:
    return _as_text(SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS.get("general", "")))


def _call_gemini(system: str, contents: list) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="کلید Gemini تنظیم نشده است.")

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
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
        raise HTTPException(status_code=502, detail=f"خطای Gemini ({res.status_code}): {err}")

    data = res.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        raise HTTPException(status_code=502, detail="پاسخی از Gemini دریافت نشد.")


def _save_messages(db: Session, customer: Customer, user_id: str, category: str,
                   user_text: str, assistant_text: str):
    """ذخیره پیام کاربر و پاسخ دستیار در دیتابیس"""
    user_tokens = _estimate_tokens(user_text)
    asst_tokens = _estimate_tokens(assistant_text)

    db.add(Message(
        customer_id=customer.id,
        user_id=user_id or "anonymous",
        role="user",
        content=user_text,
        category=category,
        tokens=user_tokens,
    ))
    db.add(Message(
        customer_id=customer.id,
        user_id=user_id or "anonymous",
        role="assistant",
        content=assistant_text,
        category=category,
        tokens=asst_tokens,
    ))
    db.commit()


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        customer = get_customer(request.api_key, db)
        _check_rate_limit(request.api_key)
        _check_daily_quota(db, customer)

        # دسته را از درخواست یا از پروفایل مشتری بگیر
        category = (request.category or customer.category or "general").strip().lower()
        if category not in SYSTEM_PROMPTS:
            category = customer.category if customer.category in SYSTEM_PROMPTS else "general"

        contents = build_contents(request)
        if not contents:
            return {"success": False, "response": "پیام خالی است."}

        text = _call_gemini(_system_text(category), contents)

        # ذخیره واقعی در دیتابیس
        _save_messages(db, customer, request.user_id, category, request.message.strip(), text)

        return {
            "success": True,
            "response": text,
            "customer": customer.business,
            "plan": customer.plan,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat Error: {type(e).__name__}: {e}")
        return {"success": False, "response": f"خطا در پردازش: {e}"}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """
    استریم سازگار با فرانت فعلی:
    پاسخ کامل از Gemini گرفته می‌شود، سپس تکه‌تکه به فرانت فرستاده می‌شود
    و در نهایت پیام‌ها در دیتابیس ذخیره می‌شوند.
    """

    def event_generator():
        try:
            customer = get_customer(request.api_key, db)
            _check_rate_limit(request.api_key)
            _check_daily_quota(db, customer)

            category = (request.category or customer.category or "general").strip().lower()
            if category not in SYSTEM_PROMPTS:
                category = customer.category if customer.category in SYSTEM_PROMPTS else "general"

            contents = build_contents(request)
            if not contents:
                yield f"data: {json.dumps({'content': 'پیام خالی است.', 'done': True}, ensure_ascii=False)}\n\n"
                return

            text = _call_gemini(_system_text(category), contents)

            # ذخیره در دیتابیس
            try:
                _save_messages(db, customer, request.user_id, category, request.message.strip(), text)
            except Exception as save_err:
                print(f"⚠️ ذخیره پیام ناموفق: {save_err}")

            # ارسال تکه‌تکه برای حس استریم
            step = 14
            for i in range(0, len(text), step):
                chunk = text[i:i + step]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True, 'customer': customer.business}, ensure_ascii=False)}\n\n"

        except HTTPException as he:
            msg = he.detail if isinstance(he.detail, str) else str(he.detail)
            yield f"data: {json.dumps({'content': msg, 'done': True, 'error': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            print(f"❌ Stream Error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'content': f'خطا در پردازش: {e}', 'done': True, 'error': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/quota")
async def chat_quota(api_key: str, db: Session = Depends(get_db)):
    """بررسی سهمیه باقی‌مانده روزانه مشتری"""
    customer = get_customer(api_key, db)
    limit = MAX_MESSAGES_PER_DAY.get(customer.plan, MAX_MESSAGES_PER_DAY["basic"])
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    used = db.query(func.count(Message.id)).filter(
        Message.customer_id == customer.id,
        Message.created_at >= today_start,
        Message.role == "user"
    ).scalar() or 0
    return {
        "plan": customer.plan,
        "limit": limit,
        "used": used,
        "remaining": max(0, limit - used),
        "business": customer.business,
        "expires_at": str(customer.expires_at) if customer.expires_at else None,
    }
