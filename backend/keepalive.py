import threading
import requests
import time
import os

def keep_alive():
    url = os.getenv("APP_URL", "")
    if not url:
        print("⚠️ APP_URL تنظیم نشده")
        return

    url = f"{url}/health"
    print(f"✅ Keep Alive شروع شد → {url}")

    while True:
        try:
            time.sleep(600)
            res = requests.get(url, timeout=10)
            print(f"💓 Ping → {res.status_code}")
        except Exception as e:
            print(f"⚠️ Ping خطا: {e}")

def start_keep_alive():
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
