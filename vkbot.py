import time
import requests
import threading
import os
import random
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
URL = os.getenv("URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

ADMIN_ID = 489699668

last_status = None


# =========================
# 📩 VK SEND
# =========================
def send_vk(text, peer_id):
    try:
        resp = requests.post(
            "https://api.vk.com/method/messages.send",
            params={
                "access_token": VK_TOKEN,
                "v": "5.131",
                "peer_id": peer_id,
                "message": text,
                "random_id": random.randint(1, 10**9)
            }
        ).json()

        print("SEND:", resp)

    except Exception as e:
        print("SEND ERROR:", e)


# =========================
# 🔍 CHECK SERVER
# =========================
def check_server():
    try:
        r = requests.get(URL, timeout=3)
        print("STATUS:", r.status_code)
        return r.status_code == 200
    except Exception as e:
        print("CHECK ERROR:", e)
        return False


# =========================
# 🔁 MONITOR LOOP
# =========================
def monitor_loop():
    global last_status

    fail_count = 0

    while True:
        is_alive = check_server()

        print("SERVER:", is_alive)

        if is_alive:
            fail_count = 0

            if last_status is False:
                send_vk("✅ Сервер снова жив", ADMIN_ID)

            last_status = True

        else:
            fail_count += 1

            if last_status is not False:
                send_vk("🚨 Сервер УМЕР", ADMIN_ID)

            last_status = False

        time.sleep(CHECK_INTERVAL)


# =========================
# 🔌 LONG POLL INIT
# =========================
def get_longpoll():
    resp = requests.get(
        "https://api.vk.com/method/groups.getLongPollServer",
        params={
            "access_token": VK_TOKEN,
            "v": "5.131",
            "group_id": VK_GROUP_ID
        }
    ).json()

    print("LP INIT:", resp)

    return resp["response"]


# =========================
# 🤖 VK COMMANDS
# =========================
def vk_polling():
    lp = get_longpoll()

    server = lp["server"]
    key = lp["key"]
    ts = lp["ts"]

    while True:
        try:
            url = f"{server}?act=a_check&key={key}&ts={ts}&wait=25"
            resp = requests.get(url).json()

            ts = resp["ts"]

            for update in resp.get("updates", []):

                if update.get("type") != "message_new":
                    continue

                msg = update["object"]["message"]

                text = msg.get("text", "").lower().split("@")[0].strip()
                peer_id = msg["peer_id"]

                print("CMD:", text)

                # =========================
                # 🎮 COMMANDS
                # =========================
                if text == "/ping":
                    ok = check_server()
                    send_vk(
                        "🟢 Сервер отвечает" if ok else "🔴 Сервер НЕ отвечает",
                        peer_id
                    )

                elif text == "/status":
                    send_vk(
                        "🟢 Онлайн" if last_status else "🔴 Оффлайн",
                        peer_id
                    )

        except Exception as e:
            print("VK ERROR:", e)
            time.sleep(3)

            lp = get_longpoll()
            server = lp["server"]
            key = lp["key"]
            ts = lp["ts"]


# =========================
# 🚀 START
# =========================
if __name__ == "__main__":
    print("STARTED")

    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=vk_polling, daemon=True).start()

    while True:
        time.sleep(1)