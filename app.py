import os
from flask import Flask, request
from services.pharmacy import handle_pharmacy
from services.grocery import handle_grocery
from utils import send_message
from dispatcher import dispatch_message

app = Flask(__name__)

# الحالات المؤقتة للمستخدمين
user_states = {}
user_orders = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("📨 البيانات المستلمة من UltraMsg:")
    print(data)

    message = data.get("data", {}).get("body", "").strip()
    user_id = data.get("data", {}).get("from", "")

    if not message or not user_id:
        print("❌ تم استلام بيانات غير صالحة:")
        print("message:", message)
        print("user_id:", user_id)
        return "Invalid", 400

    # عرض القائمة الرئيسية
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

    # الصيدلية
    response = handle_pharmacy(user_id, message, user_states, user_orders)
    if response:
        send_message(user_id, response)
        return "OK", 200

    # البقالة
    response = handle_grocery(user_id, message, user_states, user_orders)
    if response:
        send_message(user_id, response)
        return "OK", 200

    # عرض الطلبات
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

    # إنهاء الطلب
    if message == "تم":
        orders = user_orders.get(user_id, [])
        if not orders:
            send_message(user_id, "❌ لا يوجد أي طلبات لإرسالها.")
        else:
            from utils import generate_order_id
            from vendors import vendors
            from mandoubs import mandoubs

            order_id = generate_order_id()

            # إرسال نسخة للمندوب
            full_summary = "\n".join([f"- ({o['service']}) {o['order']}" for o in orders])
            for mandoub in mandoubs:
                if mandoub["available"]:
                    msg = f"📦 طلب جديد رقم {order_id} من {user_id}:\n{full_summary}"
                    send_message(mandoub["id"], msg)
                    break

            # إرسال لكل محل فقط الجزء الخاص به
            from services import pharmacy, grocery
            for o in orders:
                if o["service"] == "الصيدلية":
                    pharmacy.send_order(vendors["pharmacy"]["number"], order_id, o["order"])
                elif o["service"] == "البقالة":
                    grocery.send_order(vendors["grocery"]["number"], order_id, o["order"])

            send_message(user_id, f"📤 تم إرسال طلبك رقم {order_id} للمندوب والمحلات.")
            user_orders[user_id] = []

        return "OK", 200

    # رد افتراضي
    send_message(user_id, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")
    return "OK", 200
