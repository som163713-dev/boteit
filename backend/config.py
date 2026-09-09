import os
from openai import OpenAI

APP_VERSION = "1.0.0"
APP_NAME = "Eitaa AI Miniapp"

# مدل رایگان Hugging Face
AI_MODEL = "HuggingFaceH4/zephyr-7b-beta"  # یا "mistralai/Mistral-7B-Instruct-v0.2"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
MAX_HISTORY = 10

# اتصال به Hugging Face Inference API
client = OpenAI(
    api_key=os.getenv("HF_API_KEY"), 
    base_url="https://api-inference.huggingface.co/v1"
)
