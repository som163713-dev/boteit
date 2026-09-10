import os
from huggingface_hub import InferenceClient

APP_VERSION = "2.0.0"
APP_NAME = "Eitaa AI Miniapp"

# مدل — روی Inference Providers رایگان کار می‌کند
AI_MODEL = "HuggingFaceH4/zephyr-7b-beta"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
MAX_HISTORY = 10

# توکن از Environment Variables رندر
_HF_TOKEN = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")

# endpoint جدید Hugging Face (جایگزین api-inference.huggingface.co)
client = InferenceClient(
    model=AI_MODEL,
    token=_HF_TOKEN,
    timeout=120,
)
