import os
from huggingface_hub import InferenceClient

# تنظیمات پایه
APP_VERSION = "1.0.0"
APP_NAME = "Eitaa AI Miniapp"

# مدل‌های رایگان Hugging Face
AI_MODEL = "HuggingFaceH4/zephyr-7b-beta"  # یا "mistralai/Mistral-7B-Instruct-v0.3"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
MAX_HISTORY = 10

# اتصال به Hugging Face
client = InferenceClient(
    token=os.getenv("HF_API_KEY"),
    timeout=120
)
