"""
مسیرهای «کارخانه‌ی ایجنت» — روی همون زیرساخت واقعی این پروژه (Gemini، دیتابیس،
auth با api_key) سوار شده، نه یه سرویس جدا. هیچ عدد جعلی تولید نمی‌کنه:
گزارش‌ها مستقیماً از جدول Message محاسبه می‌شن (تنها منبع داده‌ی واقعی که
این اپ در حال حاضر از مشتری‌ها داره).
"""
import json
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import GEMINI_API_KEY, GEMINI_URL, TEMPERATURE
from backend.database import get_db
from backend.models import Customer, Message, ContentItem
from backend.auth import get_customer
from backend.factory_prompts import (
    FACTORY_CONTENT_PROMPT,
    FACTORY_CAMPAIGN_PROMPT,
    FACTORY_REPORT_PROMPT,
)

router = APIRouter(prefix="/factory", tags=["Factory"])


def _call_gemini(system: str, prompt: str, max_tokens: int = 700) -> str:
    """
    همون الگوی routes/chat.py — تماس مستقیم با Gemini با requests.
    اگه خطا بده، خطای واقعی raise می‌شه؛ متن ساختگی برنمی‌گردونیم.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="کلید Gemini تنظیم نشده است.")

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": max_tokens},
    }
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    res = requests.post(url, json=payload, timeout=90)

    if res.status_code != 200:
        err = res.text[:400]
        try:
            err = res.json().get("error", {}).get("message") or err
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"خطای Gemini ({res.status_code}): {err}")

    data = res.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        raise HTTPException(status_code=502, detail="پاسخی از Gemini دریافت نشد.")


def _real_message_kpis(db: Session, customer: Customer, window_days: int) -> dict:
    """
    KPI واقعی — مستقیم از جدول Message همین مشتری. هیچ فرض یا عدد ساختگی نیست.
    اگه پیامی ثبت نشده باشه، صراحتاً اعلام می‌شه.
    """
    now = datetime.now()
    cur_start = now - timedelta(days=window_days)
    prev_start = cur_start - timedelta(days=window_days)

    cur_count = db.query(func.count(Message.id)).filter(
        Message.customer_id == customer.id, Message.created_at >= cur_start
    ).scalar() or 0

    prev_count = db.query(func.count(Message.id)).filter(
        Message.customer_id == customer.id,
        Message.created_at >= prev_start,
        Message.created_at < cur_start,
    ).scalar() or 0

    total_ever = db.query(func.count(Message.id)).filter(
        Message.customer_id == customer.id
    ).scalar() or 0

    if total_ever == 0:
        return {"status": "no_data", "message": "هنوز هیچ پیامی برای این ربات ثبت نشده."}

    growth_pct = None
    if prev_count > 0:
        growth_pct = round((cur_count - prev_count) / prev_count * 100, 1)

    top_categories = (
        db.query(Message.category, func.count(Message.id).label("c"))
        .filter(Message.customer_id == customer.id, Message.created_at >= cur_start)
        .group_by(Message.category)
        .order_by(func.count(Message.id).desc())
        .limit(3)
        .all()
    )

    return {
        "status": "ok",
        "window_days": window_days,
        "messages_this_window": cur_count,
        "messages_previous_window": prev_count,
        "growth_pct": growth_pct,
        "top_categories": [{"category": c[0], "count": c[1]} for c in top_categories],
    }


class ContentRequest(BaseModel):
    api_key: str
    topic: str


class CampaignRequest(BaseModel):
    api_key: str
    budget_toman: int
    goal: str = ""


@router.post("/content")
async def generate_content(req: ContentRequest, db: Session = Depends(get_db)):
    customer = get_customer(req.api_key, db)

    prompt = f"""
کسب‌وکار: {customer.business} (دسته: {customer.category})
موضوع محتوا: {req.topic}

یک کپشن واقعی و قابل انتشار درباره‌ی همین موضوع بنویس.
"""
    text = _call_gemini(FACTORY_CONTENT_PROMPT, prompt)

    item = ContentItem(customer_id=customer.id, kind="content", input_brief=req.topic, output_text=text)
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"success": True, "id": item.id, "output": text}


@router.post("/campaign")
async def generate_campaign(req: CampaignRequest, db: Session = Depends(get_db)):
    customer = get_customer(req.api_key, db)
    kpis = _real_message_kpis(db, customer, window_days=7)

    if kpis["status"] == "no_data":
        kpi_summary = "هنوز هیچ داده‌ی واقعی تعامل مشتری (پیام) برای این ربات ثبت نشده."
    else:
        growth_txt = (f"{kpis['growth_pct']}%" if kpis["growth_pct"] is not None
                      else "قابل محاسبه نیست (دوره‌ی قبل داده نداشت)")
        kpi_summary = (
            f"پیام‌های ۷ روز اخیر: {kpis['messages_this_window']} "
            f"(رشد نسبت به هفته‌ی قبل: {growth_txt}). "
            f"پرتکرارترین دسته‌ها: {', '.join(c['category'] for c in kpis['top_categories']) or 'نامشخص'}."
        )

    prompt = f"""
کسب‌وکار: {customer.business} (دسته: {customer.category})
بودجه‌ی کمپین: {req.budget_toman:,} تومان
هدف: {req.goal or 'افزایش تعامل و مشتری جدید'}

وضعیت واقعی تعامل با ربات هوشمند این کسب‌وکار:
{kpi_summary}

یک طرح کمپین دو هفته‌ای واقعی بنویس شامل: هدف کمی متناسب با بودجه،
تقسیم بودجه بین کانال‌ها، و ۳ ایده‌ی محتوایی مشخص.
"""
    text = _call_gemini(FACTORY_CAMPAIGN_PROMPT, prompt, max_tokens=900)

    item = ContentItem(customer_id=customer.id, kind="campaign",
                        input_brief=f"budget={req.budget_toman}, goal={req.goal}", output_text=text)
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"success": True, "id": item.id, "output": text, "kpis": kpis}


@router.get("/report")
async def generate_report(api_key: str = Query(...), days: int = Query(7, ge=1, le=90),
                           db: Session = Depends(get_db)):
    customer = get_customer(api_key, db)
    kpis = _real_message_kpis(db, customer, window_days=days)

    prompt = f"""
این خروجی خام و واقعی تحلیل تعامل مشتری‌ها با ربات هست (JSON):
{json.dumps(kpis, ensure_ascii=False)}

بر اساس دقیقاً همین داده (بدون اضافه کردن عدد یا فرض جدید)، یک گزارش کوتاه فارسی بنویس:
وضعیت فعلی + یک اقدام پیشنهادی مشخص. اگه status برابر no_data بود فقط همین رو توضیح بده
و هیچ عددی حدس نزن.
"""
    narrative = _call_gemini(FACTORY_REPORT_PROMPT, prompt, max_tokens=500)

    item = ContentItem(customer_id=customer.id, kind="report",
                        input_brief=f"days={days}", output_text=narrative)
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"success": True, "id": item.id, "kpis": kpis, "narrative": narrative}


@router.get("/history")
async def factory_history(api_key: str = Query(...), kind: str | None = Query(None),
                           db: Session = Depends(get_db)):
    customer = get_customer(api_key, db)
    q = db.query(ContentItem).filter(ContentItem.customer_id == customer.id)
    if kind:
        q = q.filter(ContentItem.kind == kind)
    items = q.order_by(ContentItem.created_at.desc()).limit(50).all()
    return [
        {
            "id": i.id,
            "kind": i.kind,
            "input_brief": i.input_brief,
            "output_text": i.output_text,
            "created_at": str(i.created_at),
        }
        for i in items
    ]
