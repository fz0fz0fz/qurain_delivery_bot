# order_logger.py

import json
from datetime import datetime
import os

LOG_FILE = "orders_log.json"

def log_order(user_id, service, order_text):
    order_data = {
        "user_id": user_id,
        "service": service,
        "order": order_text,
        "timestamp": datetime.now().isoformat()
    }

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([order_data], f, ensure_ascii=False, indent=2)
    else:
        with open(LOG_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

            data.append(order_data)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
