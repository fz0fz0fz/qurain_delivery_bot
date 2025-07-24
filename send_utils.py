import os
import requests
import json

ORDERS_FILE = "orders_log.json"
ORDER_PREFIX = "G"  # غيّر إذا أحببت
ORDER_COUNTER_FILE = "order_counter.txt"

def get_last_order_number():
    # يقرأ آخر رقم طلب من ملف منفصل (أو يرجع صفر إذا الملف غير موجود)
    if not os.path.exists(ORDER_COUNTER_FILE):
        return 0
    try:
        with open(ORDER_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_last_order_number(n):
    # يحفظ الرقم الجديد في ملف منفصل
    with open(ORDER_COUNTER_FILE, "w") as f:
        f.write(str(n))

def generate_order_id():
    last_number = get_last_order_number()
    new_number = last_number + 1
    save_last_order_number(new_number)
    return f"{ORDER_PREFIX}{new_number}"

def send_message(phone, message):
    instance_id = os.getenv("ULTRA_INSTANCE_ID")
    token = os.getenv("ULTRA_TOKEN")
    if not instance_id or not token:
        raise EnvironmentError("ULTRA_INSTANCE_ID and ULTRA_TOKEN must be set in environment variables.")

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "to": phone,
        "body": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, params={"token": token}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"error": str(e)}
