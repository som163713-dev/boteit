import os
from huggingface_hub import InferenceClient

APP_VERSION = "2.1.0"
APP_NAME = "Eitaa AI Miniapp"

# مدل رایگان و در دسترس روی Inference Providers
AI_MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
MAX_HISTORY = 10

_HF_TOKEN = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")

# اجبار به endpoint جدید — دیگر از api-inference.huggingface.co استفاده نمی‌شود
client = InferenceClient(
    base_url="https://router.huggingface.co/v1",
    api_key=_HF_TOKEN,
    timeout=120,
)
