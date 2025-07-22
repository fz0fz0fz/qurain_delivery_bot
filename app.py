import os
import json
import logging
from flask import Flask, request, jsonify
from services.unified_service import handle_service
from send_utils import send_message, generate_order_id

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

user_states = {}
user_orders = {}
user_last_service = {}

ORDERS_LOG_FILE = "orders_log.json"

# تحميل الطلبات من الملف إن وُجد
if os.path.exists(ORDERS_LOG_FILE):
    with open(ORDERS_LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            user_orders = data.get("orders", {})
            user_states = data.get("states", {})
            user_last_service = data.get("last_service", {})
        except json.JSONDecodeError:
            pass

def save_orders():
    with open(ORDERS_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "orders": user_orders,
            "states": user_states,
            "last_service": user_last_service
        }, f, ensure_ascii=False, indent=2)

services = {
    "2": {
        "name": "الصيدلية",
        "stores": ["صيدلية الدواء", "صيدلية النهدي", "صيدلية زهرة"]
    },
    "3": {
        "name": "البقالة",
        "stores": ["بقالة التميمي", "بقالة الخير", "بقالة المدينة"]
    },
    "4": {
        "name": "الخضار",
        "stores": ["خضار الطازج", "سوق المزارعين", "خضار الوفرة"]
    }
}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "data" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    payload = data["data"]
    phone = payload["from"]
    message = payload["body"].strip()
    user_id = phone

    if message in ["0", ".", "٠", "صفر", "خدمات"]:
        return jsonify({
            "sent": send_message(phone,
                "*📋 قائمة خدمات القرين:*\n"
                "1️⃣ حكومي\n"
                "2️⃣ صيدلية 💊\n"
                "3️⃣ بقالة 🥤\n"
                "4️⃣ خضار 🥬\n"
                "...\n"
                "20. طلباتك"
            )
        })

    if message == "20":
        orders = user_orders.get(user_id, [])
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات محفوظة.")})
        
        order_text = "*🧾 طلباتك الحالية:*\n"
        for i, item in enumerate(orders, 1):
            order_text += f"{i}. [{item['service']}] {item['order']}\n"
        order_text += "\n✉️ أرسل (تم) لإرسال الطلب للمندوب."
        return jsonify({"sent": send_message(phone, order_text)})

    if message == "تم":
        orders = user_orders.get(user_id, [])
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات لإرسالها.")})

        order_id = generate_order_id()
        summary = f"📦 *طلب جديد {order_id}:*\n"
        for i, item in enumerate(orders, 1):
            summary += f"{i}. [{item['service']}] {item['order']}\n"

        send_message(phone, summary)
        # send_message("رقم_مندوب", summary)
        user_orders[user_id] = []
        save_orders()
        return jsonify({"sent": send_message(phone, "✅ تم إرسال طلبك بنجاح. رقم الطلب: " + order_id)})

    if message == "99":
        last_service = user_last_service.get(user_id)
        if last_service:
            for code, service in services.items():
                if service["name"] == last_service:
                    response = handle_service(
                        user_id=user_id,
                        message=message,
                        user_states=user_states,
                        user_orders=user_orders,
                        service_id=code,
                        service_name=service["name"],
                        stores_list=service["stores"]
                    )
                    if response:
                        save_orders()
                        return jsonify({"sent": send_message(phone, response)})

    for code, service in services.items():
        if message == code:
            user_last_service[user_id] = service["name"]

        response = handle_service(
            user_id=user_id,
            message=message,
            user_states=user_states,
            user_orders=user_orders,
            service_id=code,
            service_name=service["name"],
            stores_list=service["stores"]
        )
        if response:
            save_orders()
            return jsonify({"sent": send_message(phone, response)})

    return jsonify({"sent": send_message(phone, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")})
