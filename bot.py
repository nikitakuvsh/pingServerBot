import time
import requests
import threading
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = os.getenv("URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

last_status = True
last_update_id = None


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })


def check_server():
    try:
        r = requests.get(URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def monitor_loop():
    global last_status

    while True:
        is_alive = check_server()

        if is_alive:
            if not last_status:
                send_telegram("✅ Сервер снова жив")
            last_status = True
        else:
            if last_status:
                send_telegram("🚨 Сервер УМЕР")
            last_status = False

        time.sleep(CHECK_INTERVAL)


def telegram_polling():
    global last_update_id

    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

        params = {
            "timeout": 30,
            "offset": last_update_id + 1 if last_update_id else None
        }

        try:
            resp = requests.get(url, params=params).json()

            for update in resp["result"]:
                last_update_id = update["update_id"]

                message = update.get("message")
                if not message:
                    continue

                text = message.get("text", "")
                chat_id = message["chat"]["id"]

                if str(chat_id) != str(CHAT_ID):
                    continue

                if text == "/ping":
                    is_alive = check_server()
                    send_telegram("🟢 Сервер отвечает" if is_alive else "🔴 Сервер НЕ отвечает")

                elif text == "/status":
                    send_telegram("🟢 Онлайн" if last_status else "🔴 Оффлайн")

        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)


if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=telegram_polling, daemon=True).start()

    while True:
        time.sleep(1)