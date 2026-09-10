import os

APP_VERSION = "2.3.0"
APP_NAME = "Eitaa AI Miniapp"

AI_MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 800
TEMPERATURE = 0.7
MAX_HISTORY = 10

HF_TOKEN = (os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN") or "").strip()
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"

if not HF_TOKEN:
    print("⚠️ HF_API_KEY تنظیم نشده است!")
