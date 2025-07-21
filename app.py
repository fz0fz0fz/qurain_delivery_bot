import os
import logging
from flask import Flask, request, jsonify
from send_utils import send_message
from unified_service import handle_service
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

user_states = {}
user_orders = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logging.info("📨 البيانات المستلمة من UltraMsg:\n%s", data)

    if not data or "data" not in data:
        return jsonify({"success": False}), 400

    msg = data["data"]
    phone = msg["from"]
    message = msg["body"].strip()
    user_id = phone

    # ✅ إذا أرسل المستخدم "0" أو "." أو "خدمات" يتم عرض القائمة الرئيسية
    if message in ["0", ".", "٠", "صفر", "خدمات"]:
        main_menu = (
            "*📋 خدمات القرين:*\n\n"
            "1️⃣ حكومي\n"
            "2️⃣ صيدلية 💊\n"
            "3️⃣ بقالة 🥤\n"
            "4️⃣ خضار 🥬\n"
            "5️⃣ رحلات ⛺️\n"
            "6️⃣ حلا 🍮\n"
            "7️⃣ أسر منتجة 🥧\n"
            "8️⃣ مطاعم 🍔\n"
            "9️⃣ قرطاسية 📗\n"
            "🔟 محلات 🏪\n"
            "11. شالية 🏖\n"
            "12. وايت 🚛\n"
            "13. شيول 🚜\n"
            "14. دفان 🏗\n"
            "15. مواد بناء وعوازل 🧱\n"
            "16. عمال 👷\n"
            "17. محلات مهنية 🔨\n"
            "18. ذبائح وملاحم 🥩\n"
            "19. نقل مدرسي ومشاوير 🚍\n"
            "20. طلباتك 📦\n"
        )
        return jsonify({"success": True}), send_message(phone, main_menu)

    # ✅ تمرير رسالة 99 إلى الخدمة الحالية إذا كان المستخدم داخل خدمة
    elif message == "99" and user_states.get(user_id, "").startswith("in_service:"):
        service_state = user_states[user_id]
        service_id = service_state.split(":")[1]
        service_name = service_state.split(":")[2]
        response = handle_service(
            user_id, message, user_states, user_orders,
            service_id, service_name, []
        )
        return jsonify({"success": True}), send_message(phone, response)

    # ✅ تمرير الرسائل إلى الخدمة الحالية إذا كان المستخدم داخل خدمة
    elif user_states.get(user_id, "").startswith("in_service:"):
        service_state = user_states[user_id]
        service_id = service_state.split(":")[1]
        service_name = service_state.split(":")[2]
        response = handle_service(
            user_id, message, user_states, user_orders,
            service_id, service_name, []
        )
        return jsonify({"success": True}), send_message(phone, response)

    # ✅ إذا أرسل "20" عرض الطلبات الحالية
    elif message == "20":
        user_data = user_orders.get(user_id, {})
        if not user_data:
            return jsonify({"success": True}), send_message(phone, "🗂 لا توجد طلبات محفوظة حالياً.")
        reply = "*📦 طلباتك الحالية:*\n\n"
        for service, items in user_data.items():
            reply += f"📌 *{service}:*\n"
            for item in items:
                reply += f" - {item}\n"
            reply += "\n"
        reply += '✅ إذا كنت جاهزاً للإرسال، أرسل كلمة *تم*.\n'
        return jsonify({"success": True}), send_message(phone, reply)

    # ✅ إرسال الطلب النهائي
    elif message == "تم":
        from order_router import process_order
        return process_order(user_id, phone, user_orders)

    # ⚠️ رد افتراضي
    else:
        return jsonify({"success": True}), send_message(phone, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")

if __name__ == "__main__":
    app.run()
