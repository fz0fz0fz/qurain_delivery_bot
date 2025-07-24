import json
import os

ORDERS_FILE = "orders_log.json"

def save_order(order_id, user_id, orders):
    all_data = {}

    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ ملف orders_log.json تالف أو غير صالح، سيتم تجاهله وإعادة الكتابة.")

    # تأكد من وجود قسم الطلبات
    if "orders" not in all_data:
        all_data["orders"] = {}

    all_data["orders"][order_id] = {
        "user_id": user_id,
        "orders": orders
    }

    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
