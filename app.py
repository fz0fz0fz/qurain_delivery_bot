import os
import logging
from flask import Flask, request, jsonify
from services.unified_service import handle_service
from send_utils import send_message, generate_order_id
from order_logger import get_all_orders

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

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
        orders = get_all_orders(user_id)
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات محفوظة.")})
        
        order_text = "*🧾 طلباتك الحالية:*\n"
        for i, item in enumerate(orders, 1):
            order_text += f"{i}. [{item['service']}] {item['order']}\n"
        order_text += "\n✉️ أرسل (تم) لإرسال الطلب للمندوب."
        return jsonify({"sent": send_message(phone, order_text)})

    if message == "تم":
        orders = get_all_orders(user_id)
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات لإرسالها.")})

        order_id = generate_order_id()
        summary = f"📦 *طلب جديد {order_id}:*\n"
        for i, item in enumerate(orders, 1):
            summary += f"{i}. [{item['service']}] {item['order']}\n"

        send_message(phone, summary)
        # send_message("رقم_مندوب", summary)
        
        # تفريغ الطلبات بعد الإرسال
        from order_logger import clear_user_orders
        clear_user_orders(user_id)

        return jsonify({"sent": send_message(phone, "✅ تم إرسال طلبك بنجاح. رقم الطلب: " + order_id)})

    for code, service in services.items():
        response = handle_service(
            user_id=user_id,
            message=message,
            service_id=code,
            service_name=service["name"],
            stores_list=service["stores"]
        )
        if response:
            return jsonify({"sent": send_message(phone, response)})

    return jsonify({"sent": send_message(phone, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")})
