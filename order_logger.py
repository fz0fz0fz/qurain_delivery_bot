# order_logger.py

import json
import os

ORDERS_FILE = "orders_log.json"

# ✅ حفظ الطلب في orders_log.json مع بنية كاملة
def save_order(order_id, user_id, orders):
    all_data = {
        "orders": {},
        "states": {},
        "last_service": {}
    }

    # تحميل البيانات القديمة إن وجدت
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ ملف orders_log.json تالف أو غير صالح، سيتم إعادة بنائه.")

    # حفظ الطلب الجديد
    all_data["orders"][order_id] = {
        "user_id": user_id,
        "orders": orders,
        "sent_to": []
    }

    # كتابة الملف
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

# ✅ تحميل كل الطلبات
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return {"orders": {}, "states": {}, "last_service": {}}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ تعذر قراءة ملف الطلبات.")
        return {"orders": {}, "states": {}, "last_service": {}}

# ✅ حفظ كل البيانات دفعة واحدة (تستخدم عند تعديل الطلب أو تحديث sent_to)
def save_all_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
