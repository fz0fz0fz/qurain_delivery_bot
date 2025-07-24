import json
import os

ORDERS_FILE = "orders_log.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ ملف orders_log.json تالف أو غير صالح، سيتم تجاهله.")
    return {"orders": {}, "states": {}, "last_service": {}}

def save_all_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
