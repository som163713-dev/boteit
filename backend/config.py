import os

APP_VERSION = "4.0.0"
APP_NAME = "Eitaa AI Miniapp (Boteit)"

# مدل Gemini
AI_MODEL = "gemini-3.6-flash"
MAX_TOKENS = 800
TEMPERATURE = 0.7
MAX_HISTORY = 10

# محدودیت‌های ساده برای جلوگیری از سوءاستفاده
MAX_MESSAGES_PER_DAY = {
    "basic": 150,
    "pro": 600,
    "enterprise": 3000,
}
MAX_REQUESTS_PER_MINUTE = 12  # per customer

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent"

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY تنظیم نشده است!")
else:
    print(f"✅ Gemini key ok, model={AI_MODEL}")
