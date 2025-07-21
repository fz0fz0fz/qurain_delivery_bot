from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Qurain Delivery Bot is running ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    print("📥 نوع البيانات:", request.content_type)

    try:
        data = request.form.to_dict()  # ✅ قراءة بيانات UltraMsg بشكل صحيح
        print("📥 البيانات المستلمة:", data)

        sender = data.get("from")
        message = data.get("body")

        print("👤 المرسل:", sender)
        print("💬 الرسالة:", message)

        if sender and message:
            reply = f"📩 تم استلام رسالتك: {message}"
            send_whatsapp(sender, reply)

        return "OK", 200

    except Exception as e:
        print("❌ خطأ:", str(e))
        return "Error", 400

def send_whatsapp(to, message):
    url = "https://api.ultramsg.com/instance130542/messages/chat"
    payload = {
        "token": "9dxefhg0k4l3b7ak",
        "to": to,
        "body": message
    }
    response = requests.post(url, data=payload)
    print("تم الإرسال إلى:", to, "✅" if response.ok else "❌", response.text)
