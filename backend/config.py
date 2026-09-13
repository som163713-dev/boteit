import os

APP_VERSION = "3.0.1"
APP_NAME = "Eitaa AI Miniapp"

# مدل فعلی Gemini (جایگزین gemini-2.0-flash)
AI_MODEL = "gemini-3.6-flash"
MAX_TOKENS = 800
TEMPERATURE = 0.7
MAX_HISTORY = 10

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent"

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY تنظیم نشده است!")
else:
    print(f"✅ Gemini key ok, model={AI_MODEL}")
