import os
from huggingface_hub import InferenceClient

APP_VERSION = "2.2.0"
APP_NAME = "Eitaa AI Miniapp"

AI_MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 800
TEMPERATURE = 0.7
MAX_HISTORY = 10

_HF_TOKEN = (os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN") or "").strip()

if not _HF_TOKEN:
    print("⚠️ HF_API_KEY تنظیم نشده است!")

# اجبار به روتر جدید Hugging Face
client = InferenceClient(
    base_url="https://router.huggingface.co/v1",
    api_key=_HF_TOKEN if _HF_TOKEN else None,
    timeout=120,
)
