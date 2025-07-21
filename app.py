import os
import requests
from flask import Flask, request, jsonify
from services.pharmacy import handle_pharmacy
from services.grocery import handle_grocery
from services.vegetable import handle_vegetable

app = Flask(__name__)

INSTANCE_ID = "instance130542"
TOKEN = "9dxefhg0k4l3b7ak"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

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
    print("📥 نوع البيانات:", request.content_type)

    try:
        data = request.get_json(force=True)
        print("📥 البيانات المستلمة:", data)

        sender = data.get("data", {}).get("from")
        message = data.get("data", {}).get("body")

        print("👤 المرسل:", sender)
        print("💬 الرسالة:", message)

        if sender and message:
            reply = handle_message(message)
            send_whatsapp(sender, reply)

        return "OK", 200

    except Exception as e:
        print("❌ خطأ:", str(e))
        return "Error", 400

def handle_message(message):
    msg = message.strip().lower()

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

    if msg.startswith("2"):
        return handle_pharmacy(message)

    if msg.startswith("3"):
        return handle_grocery(message)

    if msg.startswith("4"):
        return handle_vegetable(message)

    return "📌 تم استلام طلبك. نعمل عليه حالياً..."

if __name__ == "__main__":
    app.run(port=10000)
