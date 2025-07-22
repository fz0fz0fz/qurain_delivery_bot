import os
from flask import Flask, request
from services.unified_service import handle_service
from utils import send_message, generate_order_id
from dispatcher import dispatch_message

app = Flask(__name__)

# الحالات المؤقتة للمستخدمين
user_states = {}  # مثل {"9665xxx": "awaiting_order_الصيدلية"}
user_orders = {}  # مثل {"9665xxx": [{"service": "الصيدلية", "order": "طلب"}]}


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("📨 البيانات المستلمة من UltraMsg:")
    print(data)

    msg_data = data.get("data", {})
    message = msg_data.get("body", "").strip()
    user_id = msg_data.get("from", "").strip()

    if not message or not user_id:
        print("❌ تم استلام بيانات غير صالحة:")
        print("message:", message)
        print("user_id:", user_id)
        return "Invalid", 400

    # القائمة الرئيسية
    if message in ["0", ".", "٠", "خدمات", "القائمة"]:
        main_menu = (
            "*🧾 خدمات القرين:*\n\n"
            "1️⃣. حكومي\n"
            "2️⃣. صيدلية 💊\n"
            "3️⃣. بقالة 🥤\n"
            "4️⃣. خضار 🥬\n"
            "5️⃣. رحلات ⛺️\n"
            "6️⃣. حلا 🍮\n"
            "7️⃣. أسر منتجة 🥧\n"
            "8️⃣. مطاعم 🍔\n"
            "9️⃣. قرطاسية 📗\n"
            "🔟. محلات 🏪\n"
            "11. شالية 🏖\n"
            "12. وايت 🚛\n"
            "13. شيول 🚜\n"
            "14. دفان 🏗\n"
            "15. مواد بناء وعوازل 🧱\n"
            "16. عمال 👷\n"
            "17. محلات مهنية 🔨\n"
            "18. ذبائح وملاحم 🥩\n"
            "19. نقل مدرسي ومشاوير 🚍\n"
            "20. طلباتك"
        )
        send_message(user_id, main_menu)
        return "OK", 200

    # خدمات موحدة مثل الصيدلية والبقالة
    unified_services = [
        ("2", "الصيدلية", ["صيدلية النهدي", "صيدلية الدواء"]),
        ("3", "البقالة", ["بقالة السالم", "بقالة الراية", "بقالة التوفير"]),
    ]

    for service_id, service_name, stores in unified_services:
        current_state = user_states.get(user_id)

        # التفاعل فقط مع الخدمة المناسبة أو اللي المستخدم بدأ فيها
        if (
            message == service_id or
            current_state == f"awaiting_order_{service_name}" or
            (message == "99" and current_state == f"awaiting_order_{service_name}")
        ):
            response = handle_service(user_id, message, user_states, user_orders, service_id, service_name, stores)
            if response:
                send_message(user_id, response)
                return "OK", 200

    # عرض الطلبات المجمعة
    if message in ["20", "طلباتك"]:
        orders = user_orders.get(user_id, [])
        if not orders:
            send_message(user_id, "🗃 لا يوجد طلبات محفوظة حالياً.")
        else:
            summary = "🗂 *ملخص طلباتك:*\n"
            for i, item in enumerate(orders, 1):
                summary += f"{i}. ({item['service']}) {item['order']}\n"
            summary += "\n✅ أرسل *تم* للإرسال النهائي."
            send_message(user_id, summary)
        return "OK", 200

    # إنهاء الطلبات وإرسالها للمندوب
    if message.strip() == "تم":
        orders = user_orders.get(user_id, [])
        if not orders:
            send_message(user_id, "❌ لا يوجد أي طلبات لإرسالها.")
        else:
            order_id = generate_order_id()
            combined = "\n".join([f"- ({o['service']}) {o['order']}" for o in orders])
            send_message("رقم_المندوب@c.us", f"📦 *طلب جديد* رقم #{order_id} من {user_id}:\n{combined}")
            send_message(user_id, f"📤 تم إرسال طلبك بنجاح ✅\n*رقم الطلب: {order_id}*\nسيتم التواصل معك قريباً.")
            user_orders[user_id] = []  # إفراغ الطلبات بعد الإرسال
        return "OK", 200

    # رد افتراضي
    send_message(user_id, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")
    return "OK", 200
