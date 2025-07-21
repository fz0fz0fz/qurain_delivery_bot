import os
from flask import Flask, request
from services.pharmacy import handle_pharmacy
from utils import send_message
from dispatcher import dispatch_message

app = Flask(__name__)

# الحالات المؤقتة للمستخدمين
user_states = {}  # {"9665xxx": "awaiting_pharmacy_order"}
user_orders = {}  # {"9665xxx": [{"service": "الصيدلية", "order": "طلب معين"}]}


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("📨 البيانات المستلمة من UltraMsg:")
    print(data)

    data = data.get("data", {})  # ✅ التصحيح المهم
    message = data.get("body", "").strip()
    user_id = data.get("from", "")

    if not message or not user_id:
        print("❌ تم استلام بيانات غير صالحة:")
        print("message:", message)
        print("user_id:", user_id)
        return "Invalid", 400

    # الرد على الأوامر العامة (0 = القائمة الرئيسية)
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

    # تمرير الرسالة لخدمة الصيدلية
    response = handle_pharmacy(user_id, message, user_states, user_orders)
    if response:
        send_message(user_id, response)
        return "OK", 200

    # عرض الطلبات من كافة الأقسام
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

    if message == "تم":
        orders = user_orders.get(user_id, [])
        if not orders:
            send_message(user_id, "❌ لا يوجد أي طلبات لإرسالها.")
        else:
            combined = "\n".join([f"- ({o['service']}) {o['order']}" for o in orders])
            # إرسال الطلب للمندوب أو المشرف (عدّل الرقم هنا):
            send_message("رقم_المندوب@c.us", f"📦 طلب جديد من {user_id}:\n{combined}")
            send_message(user_id, "📤 تم إرسال طلبك للمندوب، سيتم التواصل معك قريباً.")
            user_orders[user_id] = []  # مسح الطلبات
        return "OK", 200

    # رد افتراضي
    send_message(user_id, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")
    return "OK", 200
