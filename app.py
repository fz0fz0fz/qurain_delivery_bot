import os
import logging
from flask import Flask, request, jsonify
from services.unified_service import handle_service  # دالة موحدة للخدمات
from send_utils import send_message, generate_order_id

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

user_states = {}  # {"9665xxxx": "awaiting_order_الصيدلية"}
user_orders = {}  # {"9665xxxx": [{"service": "الصيدلية", "order": "اسم المنتج"}]}

# الأقسام المفعلة حاليًا
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

    # القائمة الرئيسية
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

    # عرض الطلبات
    if message == "20":
        orders = user_orders.get(user_id, [])
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات محفوظة.")})

        order_text = "*🧾 طلباتك الحالية:*\n"
        for i, item in enumerate(orders, 1):
            order_text += f"{i}. [{item['service']}] {item['order']}\n"
        order_text += "\n✉️ أرسل (تم) لإرسال الطلب للمندوب."
        return jsonify({"sent": send_message(phone, order_text)})

    # إرسال الطلب النهائي
    if message == "تم":
        orders = user_orders.get(user_id, [])
        if not orders:
            return jsonify({"sent": send_message(phone, "📭 لا توجد طلبات لإرسالها.")})

        order_id = generate_order_id()
        summary = f"📦 *طلب جديد {order_id}:*\n"
        for i, item in enumerate(orders, 1):
            summary += f"{i}. [{item['service']}] {item['order']}\n"

        send_message(phone, summary)
        # send_message("رقم_مندوب", summary) ← استبدله لاحقًا عند التوصيل
        user_orders[user_id] = []
        return jsonify({"sent": send_message(phone, "✅ تم إرسال طلبك بنجاح. رقم الطلب: " + order_id)})

    # تمرير للخدمات فقط إذا كان المستخدم في نفس الخدمة
    for code, service in services.items():
        current_state = user_states.get(user_id)

        if (
            message == code or
            current_state == f"awaiting_order_{service['name']}" or
            (message == "99" and current_state == f"awaiting_order_{service['name']}")
        ):
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
                return jsonify({"sent": send_message(phone, response)})

    # الرد الافتراضي
    return jsonify({"sent": send_message(phone, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")})
