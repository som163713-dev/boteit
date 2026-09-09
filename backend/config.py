import os
from huggingface_hub import InferenceClient

APP_VERSION = "1.0.0"
APP_NAME = "Eitaa AI Miniapp"

AI_MODEL = "HuggingFaceH4/zephyr-7b-beta"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
MAX_HISTORY = 10

client = InferenceClient(
    token=os.getenv("HF_API_KEY"),
    timeout=120
)
