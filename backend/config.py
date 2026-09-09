import os
from groq import Groq

APP_VERSION = "2.0.0"
APP_NAME    = "Eitaa AI Miniapp"
MAX_HISTORY = 10
AI_MODEL    = "llama-3.3-70b-versatile"
MAX_TOKENS  = 1000
TEMPERATURE = 0.7

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY تنظیم نشده!")
        _client = Groq(api_key=api_key)
    return _client
