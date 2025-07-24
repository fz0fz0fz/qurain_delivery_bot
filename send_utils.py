import os
import requests
import json

ORDERS_FILE = "orders_log.json"
ORDER_PREFIX = "G"  # أو غيّر إلى "A" إذا أحببت

def get_last_order_number():
    # يبحث عن آخر رقم طلب مستخدم في الملف
    if not os.path.exists(ORDERS_FILE):
        return 0
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            orders = data.get("orders", {})
            numbers = []
            for order_id in orders:
                if order_id.startswith(ORDER_PREFIX):
                    try:
                        numbers.append(int(order_id[len(ORDER_PREFIX):]))
                    except ValueError:
                        continue
            return max(numbers) if numbers else 0
    except Exception:
        return 0

def generate_order_id():
    last_number = get_last_order_number()
    return f"{ORDER_PREFIX}{last_number + 1}"

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
