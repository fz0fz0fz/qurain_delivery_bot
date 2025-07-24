# order_logger.py

import json
import os

ORDERS_FILE = "orders_log.json"

def load_orders():
    """تحميل جميع الطلبات من الملف"""
    if not os.path.exists(ORDERS_FILE):
        return {"orders": {}, "states": {}, "last_service": {}}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ ملف orders_log.json تالف. سيتم إعادة تهيئته.")
        return {"orders": {}, "states": {}, "last_service": {}}

def save_all_orders(data):
    """حفظ جميع الطلبات إلى الملف"""
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_order(order_id, user_id, orders):
    """حفظ طلب جديد إلى قسم 'orders' فقط"""
    data = load_orders()

    if "orders" not in data:
        data["orders"] = {}

    data["orders"][order_id] = {
        "user_id": user_id,
        "orders": orders,
        "sent_to": []  # قائمة المناديب الذين تم إرسال الطلب لهم
    }

    save_all_orders(data)
