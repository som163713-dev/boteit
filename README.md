# Boteit / آشا — مینی‌اپ هوشمند ایتا (نسخه ۴.۰)

محصول SaaS چندمستاجری برای کسب‌وکارهای ایرانی:  
چت‌بات هوشمند اختصاصی روی ایتا + پنل ادمین + پرداخت زرین‌پال + کارخانه تولید محتوا/کمپین/گزارش بر اساس داده واقعی.

## چه چیزی در نسخه ۴.۰ رفع و کامل شد؟

| مشکل قبلی | وضعیت جدید |
|-----------|------------|
| چت بدون api_key و بدون ذخیره پیام | چت **الزاماً** با api_key کار می‌کند و پیام‌ها در دیتابیس ذخیره می‌شوند |
| آمار و Factory خالی | اکنون از پیام‌های واقعی پر می‌شوند |
| سهمیه و محدودیت استفاده | سهمیه روزانه بر اساس پلن + rate-limit در دقیقه |
| SQLite خام | پشتیبانی از `DATABASE_URL` (Postgres روی Render هم کار می‌کند) |
| SECRET_KEY موقت | هشدار واضح + توصیه تنظیم در env |
| لینک اختصاصی مشتری | هنگام ساخت مشتری، لینک `/?key=eai_...` تولید و کپی می‌شود |

## معماری سریع

```
frontend/          → مینی‌اپ ایتا (آشا)
frontend/admin/    → پنل مدیریت
backend/
  routes/chat.py   → چت با اعتبارسنجی + ذخیره پیام + سهمیه
  routes/admin.py  → مدیریت مشتریان و ادمین
  routes/payment.py→ زرین‌پال
  routes/stats.py  → داشبورد
  routes/factory.py→ تولید محتوا / کمپین / گزارش واقعی
```

## راه‌اندازی سریع (لوکال)

```bash
cd boteit-complete
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

export GEMINI_API_KEY="کلید-گوگل-شما"
export SECRET_KEY="یک-رشته-بلند-تصادفی"
# اختیاری برای پرداخت:
export ZARINPAL_MERCHANT="کد-مرچنت"

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- مینی‌اپ: http://localhost:8000  
- پنل ادمین: http://localhost:8000/panel  

### ساخت ادمین اول
```bash
curl -X POST http://localhost:8000/admin/setup \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'
```

### ساخت مشتری و گرفتن لینک
از پنل ادمین مشتری بسازید. بعد از موفقیت، **لینک مینی‌اپ اختصاصی** نمایش داده می‌شود:
```
https://your-domain.com/?key=eai_xxxxxxxx
```
این لینک را به صاحب کسب‌وکار بدهید. کاربران نهایی با باز کردن همین لینک داخل ایتا با ربات همان کسب‌وکار چت می‌کنند.

## متغیرهای محیطی (Render / Production)

| متغیر | توضیح |
|-------|--------|
| `GEMINI_API_KEY` | کلید Google AI (الزامی) |
| `SECRET_KEY` | کلید JWT (الزامی در production) |
| `DATABASE_URL` | `postgresql://...` یا خالی بگذارید تا SQLite |
| `ZARINPAL_MERCHANT` | کد مرچنت زرین‌پال |
| `APP_URL` | آدرس کامل سرویس برای keep-alive |

## پلن‌ها و سهمیه روزانه پیام (کاربر)

| پلن | قیمت ماهانه | پیام روزانه |
|-----|-------------|-------------|
| basic | ۲۹۰٬۰۰۰ تومان | ۱۵۰ |
| pro | ۶۹۰٬۰۰۰ تومان | ۶۰۰ |
| enterprise | ۱٬۴۹۰٬۰۰۰ تومان | ۳۰۰۰ |

## اندپوینت‌های مهم

```
POST /chat/stream          {api_key, message, category, history, user_id}
GET  /chat/quota?api_key=  سهمیه باقی‌مانده
POST /factory/content      تولید محتوا
POST /factory/campaign     طرح کمپین بر اساس داده واقعی
GET  /factory/report       گزارش تعامل واقعی
GET  /health
```

## نکات مهم production

1. حتماً `SECRET_KEY` و `GEMINI_API_KEY` را در env تنظیم کنید.
2. برای Render از دیتابیس Postgres استفاده کنید (افزودن Database و تنظیم `DATABASE_URL`).
3. در ایتا، مینی‌اپ را با start_param یا لینک مستقیم `?key=...` باز کنید.
4. هزینه Gemini را مانیتور کنید؛ rate-limit و سهمیه روزانه جلوی سوءاستفاده را می‌گیرند ولی کافی نیست.

## نسخه

**4.0.0** — هسته multi-tenant کامل، ذخیره پیام واقعی، سهمیه، لینک اختصاصی، پشتیبانی Postgres.
