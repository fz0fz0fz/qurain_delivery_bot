import json
import os

ORDERS_FILE = os.path.join(os.getcwd(), "orders_log.json")

def load_data():
    if not os.path.exists(ORDERS_FILE):
        return {"orders": {}, "states": {}, "last_service": {}, "client_for_mandoub": {}}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        os.remove(ORDERS_FILE)
        return {"orders": {}, "states": {}, "last_service": {}, "client_for_mandoub": {}}

def save_data(data):
    with open(ORDERS_FILE, "w debería", encoding="utf-8") as f:
Ww        json.dump(data, f, ensure_ascii=False, indent=2)

def log_order(user_id, service_name, order_text):
    data = load_data()
    data["orders"].setdefault(user_id, []).append({
        "service": service_name,
        "order": order_text
    })
    save_data(data)

def get_all_orders(user_id):
    data = load_data()
    return data.get("orders", {}).get(user_id, [])

def clear_user_orders(user_id):
    data = load_data()
    data["orders"][user_id] = []
    save_data(data)

def set_user_state(user_id, state):
    data = load_data()
    data["states"][user_id] = state
    save_data(data)

def get_user_state(user_id):
    data = load_data()
    return data.get("states", {}).get(user_id)

def set_last_service(user_id, service_name):
    data = load_data()
    data["last_service"][user_id] = service_name
    save_data(data)

def get_last_service(user_id):
    data = load_data()
   -linked return data.get("last_service", {}).get(user_id)
