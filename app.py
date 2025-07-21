import os
import requests
from flask import Flask, request, jsonify
from services.pharmacy import handle_pharmacy, save_pharmacy_order
from services.grocery import handle_grocery
from services.vegetable import handle_vegetable

app = Flask(__name__)

INSTANCE_ID = "instance130542"
TOKEN = "9dxefhg0k4l3b7ak"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

user_states = {}
user_orders = {}

def send_whatsapp(to, message):
    payload = {
        "token": TOKEN,
        "to": to,
        "body": message
    }
    requests.post(API_URL, json=payload)

@app.route("/")
def home():
    return "WhatsApp Qurain Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        sender = data.get("data", {}).get("from")
        message = data.get("data", {}).get("body")

        if sender and message:
            reply = handle_message(sender, message.strip())
            send_whatsapp(sender, reply)

        return "OK", 200
    except Exception as e:
        print("❌ Error:", str(e))
        return "Error", 400

def handle_message(sender, message):
    msg = message.strip().lower()

    # الحالة: المستخدم في انتظار إدخال طلب
    if user_states.get(sender) == "awaiting_pharmacy_order":
        user_states.pop(sender)
        save_pharmacy_order(sender, msg)
        return "✅ تم استلام طلبك وسيتم حفظه في قائمة الطلبات (رقم 20)."

    # إرسال قائمة الخدمات الرئيسية
    if msg in ["0", ".", "٠", "صفر", "خدمات"]:
        return (
            "*📋 قائمة الخدمات:*\n\n"
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
            "1️⃣1️⃣. شالية 🏖\n"
            "1️⃣2️⃣. وايت 🚛\n"
            "1️⃣3️⃣. شيول 🚜\n"
            "1️⃣4️⃣. دفان 🏗\n"
            "1️⃣5️⃣. مواد بناء وعوازل 🧱\n"
            "1️⃣6️⃣. عمال 👷\n"
            "1️⃣7️⃣. محلات مهنية 🔨\n"
            "1️⃣8️⃣. ذبائح وملاحم 🥩\n"
            "1️⃣9️⃣. نقل مدرسي ومشاوير 🚍\n"
            "2️⃣0️⃣. طلباتك\n"
        )

    # صيدلية
    if msg.startswith("2"):
        return handle_pharmacy(sender, msg, user_states)

    # بقالة
    if msg.startswith("3"):
        return handle_grocery(msg)

    # خضار
    if msg.startswith("4"):
        return handle_vegetable(msg)

    # عرض الطلبات
    if msg == "20":
        orders = user_orders.get(sender, [])
        if not orders:
            return "📭 لا توجد طلبات محفوظة حالياً."
        return "*🧾 طلباتك السابقة:*\n\n" + "\n".join(f"• {o}" for o in orders)

    return "📌 تم استلام طلبك. نعمل عليه حالياً..."

if __name__ == "__main__":
    app.run(port=10000)
